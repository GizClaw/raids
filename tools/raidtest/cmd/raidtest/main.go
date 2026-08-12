package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
	"github.com/GizClaw/raids/tools/raidtest/internal/agent"
	"github.com/GizClaw/raids/tools/raidtest/internal/catalog"
	"github.com/GizClaw/raids/tools/raidtest/internal/config"
	"github.com/GizClaw/raids/tools/raidtest/internal/conversation"
	openaiapi "github.com/GizClaw/raids/tools/raidtest/internal/openai"
	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/provision"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
	"github.com/GizClaw/raids/tools/raidtest/internal/server"
)

type stringsFlag []string

func (s *stringsFlag) String() string         { return strings.Join(*s, ",") }
func (s *stringsFlag) Set(value string) error { *s = append(*s, value); return nil }

func main() { os.Exit(realMain(os.Args[1:], os.Stdin, os.Stdout, os.Stderr)) }

func realMain(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	if len(args) == 0 || args[0] != "run" {
		fmt.Fprintln(stderr, "usage: raidtest run [flags]")
		return 2
	}
	cfg, err := parseFlags(args[1:], stderr)
	if err != nil {
		return 2
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	result, runErr := run(ctx, cfg, stdin)
	result.Finish(runErr)
	if err := result.WriteJSON(cfg.Report); err != nil {
		fmt.Fprintf(stderr, "write report: %v\n", err)
		return 1
	}
	result.WriteTerminal(stdout)
	if runErr != nil {
		fmt.Fprintf(stderr, "raidtest: %v\n", runErr)
		return 1
	}
	return 0
}

func parseFlags(args []string, stderr io.Writer) (config.Config, error) {
	var c config.Config
	var memories stringsFlag
	fs := flag.NewFlagSet("raidtest run", flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.StringVar(&c.Server, "server", "", "GizClaw Server host:port")
	fs.StringVar(&c.Workflow, "workflow", "", "local Workflow YAML")
	fs.StringVar(&c.RuntimeProfile, "runtime-profile", "default", "deployed base RuntimeProfile ID")
	fs.StringVar(&c.RuntimeProfileFile, "runtime-profile-file", "", "optional local RuntimeProfile YAML")
	fs.Var(&memories, "memory-layout", "optional local MemoryLayout YAML (repeatable)")
	fs.StringVar(&c.Plan, "plan", "", "acceptance plan YAML")
	fs.StringVar(&c.Report, "report", "raidtest-report.json", "JSON report path")
	fs.StringVar(&c.OpenAIBaseURL, "openai-base-url", "", "GizClaw OpenAI-compatible base URL")
	fs.StringVar(&c.AgentModel, "agent-model", "", "human-simulation model ID")
	fs.StringVar(&c.JudgeModel, "judge-model", "", "semantic judge model ID")
	fs.StringVar(&c.AdminKey.Env, "admin-private-key-env", "", "environment variable containing the Admin private key")
	fs.StringVar(&c.AdminKey.File, "admin-private-key-file", "", "file containing the Admin private key")
	fs.BoolVar(&c.AdminKey.Stdin, "admin-private-key-stdin", false, "read the Admin private key from stdin")
	fs.StringVar(&c.OpenAIKey.Env, "openai-api-key-env", "", "environment variable containing the OpenAI-compatible key")
	fs.StringVar(&c.OpenAIKey.File, "openai-api-key-file", "", "file containing the OpenAI-compatible key")
	fs.BoolVar(&c.OpenAIKey.Stdin, "openai-api-key-stdin", false, "read the OpenAI-compatible key from stdin")
	fs.BoolVar(&c.Keep, "keep", false, "retain run-owned resources for debugging")
	fs.DurationVar(&c.Timeout, "timeout", 2*time.Minute, "per-turn timeout")
	if err := fs.Parse(args); err != nil {
		return c, err
	}
	if fs.NArg() != 0 {
		return c, fmt.Errorf("unexpected positional arguments: %s", strings.Join(fs.Args(), " "))
	}
	c.MemoryLayouts = memories
	if c.AdminKey.Stdin && c.OpenAIKey.Stdin {
		return c, errors.New("admin and OpenAI keys cannot both use stdin")
	}
	return c, c.Validate()
}

func run(ctx context.Context, c config.Config, stdin io.Reader) (result report.Report, runErr error) {
	runID, err := randomID(6)
	if err != nil {
		return report.New("unknown"), err
	}
	result = report.New(runID)
	workflow, err := catalog.LoadWorkflow(c.Workflow)
	if err != nil {
		return result, err
	}
	testPlan, err := plan.Load(c.Plan)
	if err != nil {
		return result, err
	}
	if !driverMatches(workflow.Driver, testPlan.Driver) {
		return result, fmt.Errorf("Workflow driver %q does not match plan driver %q", workflow.Driver, testPlan.Driver)
	}
	testPlan, err = testPlan.ForWorkflow(workflow.Source.Metadata.ID)
	if err != nil {
		return result, err
	}
	if testPlan.NeedsAgent() && c.AgentModel == "" {
		return result, errors.New("plan contains generated user turns; --agent-model is required")
	}
	if testPlan.NeedsJudge() && c.JudgeModel == "" {
		return result, errors.New("plan contains semantic judge dimensions; --judge-model is required")
	}
	adminSecret, err := c.AdminKey.Read(stdin)
	if err != nil {
		return result, err
	}
	adminKeys, err := server.KeyPairFromText(adminSecret)
	if err != nil {
		return result, err
	}
	adminConn, info, err := server.Dial(ctx, c.Server, adminKeys, "raidtest-admin-"+runID, nil)
	if err != nil {
		return result, reportError(err, adminSecret, nil)
	}
	defer adminConn.Close()
	result.Server = report.Server{Endpoint: c.Server, PublicKey: info.AuthoritativePublicKey.String(), Version: info.Version}
	api, err := adminConn.Client.ServerAdminClient()
	if err != nil {
		return result, err
	}
	admin := provision.AdminClient{API: api}
	var profile catalog.RuntimeProfile
	if c.RuntimeProfileFile != "" {
		profile, err = catalog.LoadRuntimeProfile(c.RuntimeProfileFile)
	} else {
		response, getErr := api.GetRuntimeProfileWithResponse(ctx, c.RuntimeProfile)
		if getErr != nil {
			return result, getErr
		}
		if response.JSON200 == nil {
			return result, fmt.Errorf("get RuntimeProfile %s returned HTTP %d", c.RuntimeProfile, response.StatusCode())
		}
		profile = catalog.RuntimeProfileFrom(response.JSON200.Id, response.JSON200.Spec)
	}
	if err != nil {
		return result, err
	}
	layouts := make([]catalog.MemoryLayout, 0, len(c.MemoryLayouts))
	for _, path := range c.MemoryLayouts {
		layout, loadErr := catalog.LoadMemoryLayout(path)
		if loadErr != nil {
			return result, loadErr
		}
		layouts = append(layouts, layout)
	}
	closure, err := catalog.BuildClosure(workflow, profile, layouts, runID)
	if err != nil {
		return result, err
	}
	result.Resources.Workflow = report.ResourceRef{SourceID: workflow.Source.Metadata.ID, ShadowID: closure.WorkflowID, SourceDigest: catalog.Digest(workflow.Source.Spec), ShadowDigest: catalog.Digest(workflow.Source.Spec)}
	result.Resources.RuntimeProfile = report.ResourceRef{SourceID: profile.Source.Metadata.ID, ShadowID: closure.ProfileID, SourceDigest: catalog.Digest(profile.Source.Spec), ShadowDigest: catalog.Digest(closure.Profile.Source.Spec)}
	for _, layout := range layouts {
		result.Resources.MemoryLayouts = append(result.Resources.MemoryLayouts, report.ResourceRef{SourceID: layout.Source.Metadata.ID, ShadowID: closure.MemoryIDs[layout.Source.Metadata.ID], SourceDigest: catalog.Digest(layout.Source.Spec), ShadowDigest: catalog.Digest(layout.Source.Spec)})
	}
	token, err := randomID(24)
	if err != nil {
		return result, err
	}
	setup := provision.Setup{Closure: closure, TokenID: "raidtest-token-" + runID, Token: token, WorkspaceID: "raidtest-workspace-" + runID, WorkspaceName: "raidtest-workspace-" + runID}
	lifecycle := provision.New(admin, c.Keep)
	defer func() {
		cleanupCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		cleanupErr := lifecycle.Cleanup(cleanupCtx)
		result.Lifecycle = append([]report.Lifecycle(nil), lifecycle.Ledger...)
		if cleanupErr != nil {
			if runErr == nil {
				runErr = cleanupErr
			} else {
				runErr = errors.Join(runErr, cleanupErr)
			}
		}
		runErr = reportError(runErr, adminSecret, []byte(token))
	}()
	if err := lifecycle.CreateClosure(ctx, setup); err != nil {
		return result, err
	}
	peerKeys, err := giznet.GenerateKeyPair()
	if err != nil {
		return result, err
	}
	peerConn, _, err := server.Dial(ctx, c.Server, peerKeys, "raidtest-peer-"+runID, nil)
	if err != nil {
		return result, err
	}
	defer peerConn.Close()
	registration, err := peerConn.Client.Register(ctx, "raidtest-register-"+runID, token)
	if err != nil {
		return result, fmt.Errorf("register temporary peer: %w", err)
	}
	if registration.GetRuntimeProfileName() != closure.ProfileID {
		return result, fmt.Errorf("temporary peer bound RuntimeProfile %q, want shadow profile %q", registration.GetRuntimeProfileName(), closure.ProfileID)
	}
	lifecycle.RecordPeer(peerKeys.Public.String())
	if workflow.Driver == "pet" {
		petName := "raidtest-pet-" + runID
		adopted, adoptErr := peerConn.Client.AdoptPet(ctx, "raidtest-adopt-"+runID, rpcapi.RuntimeAdoptRequest{Name: petName, DisplayName: "Raidtest Pet"})
		if adoptErr != nil {
			return result, fmt.Errorf("adopt temporary pet: %w", adoptErr)
		}
		setup.WorkspaceName = adopted.Pet.WorkspaceName
		lifecycle.Record(report.Lifecycle{ResourceType: "Pet", ID: petName, Action: "create", Status: "pass"})
		lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: setup.WorkspaceName, Action: "create", Status: "pass"})
		defer func() {
			if c.Keep {
				return
			}
			cleanupCtx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			defer cancel()
			_, deleteErr := peerConn.Client.DeletePet(cleanupCtx, "raidtest-delete-pet-"+runID, rpcapi.ServerPetDeleteRequest{Name: petName})
			status, detail := "pass", ""
			if deleteErr != nil {
				status, detail = "fail", deleteErr.Error()
				if runErr == nil {
					runErr = deleteErr
				} else {
					runErr = errors.Join(runErr, deleteErr)
				}
			}
			lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: setup.WorkspaceName, Action: "delete", Status: status, Error: detail})
			lifecycle.Record(report.Lifecycle{ResourceType: "Pet", ID: petName, Action: "delete", Status: status, Error: detail})
		}()
	} else if err := lifecycle.CreateWorkspace(ctx, setup.WorkspaceID, setup.WorkspaceName, closure.WorkflowID); err != nil {
		return result, err
	}
	target := &conversation.PeerTarget{Client: peerConn.Client, Timeout: c.Timeout, RequireAudio: workflow.Driver == "ast-translate"}
	if err := target.Select(ctx, setup.WorkspaceName, closure.WorkflowID); err != nil {
		return result, fmt.Errorf("select candidate Workspace: %w", err)
	}
	var simulation *agent.Agent
	if c.AgentModel != "" || c.JudgeModel != "" {
		key, keyErr := c.OpenAIKey.Read(stdin)
		if keyErr != nil {
			return result, keyErr
		}
		client := openaiapi.Client{BaseURL: c.OpenAIBaseURL, APIKey: string(key)}
		models, modelsErr := client.Models(ctx)
		if modelsErr != nil {
			return result, reportError(modelsErr, adminSecret, key)
		}
		if c.AgentModel != "" {
			result.Models["agent"] = chooseModel(c.AgentModel, models)
		}
		if c.JudgeModel != "" {
			result.Models["judge"] = chooseModel(c.JudgeModel, models)
		}
		simulation = &agent.Agent{Client: client, Model: result.Models["agent"]}
		defer func() { runErr = reportError(runErr, key) }()
	}
	runner := conversation.Runner{Target: target}
	if simulation != nil {
		if c.AgentModel != "" {
			runner.Agent = simulation
		}
		if c.JudgeModel != "" {
			judge := *simulation
			judge.Model = result.Models["judge"]
			runner.Judge = judge
		}
	}
	result.Cases = runner.Run(ctx, testPlan)
	for _, caseResult := range result.Cases {
		if caseResult.Status != "pass" {
			runErr = errors.New("one or more acceptance cases failed")
			break
		}
	}
	return result, runErr
}

func randomID(bytes int) (string, error) {
	b := make([]byte, bytes)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}
func driverMatches(workflow, planned string) bool {
	mapping := map[string]string{"flowcraft": "flowcraft", "doubao-realtime": "realtime", "ast-translate": "translate", "pet": "pet"}
	return mapping[workflow] == planned
}
func chooseModel(explicit string, models []string) string {
	if explicit != "" {
		return explicit
	}
	if len(models) > 0 {
		return models[0]
	}
	return ""
}
func reportError(err error, secrets ...[]byte) error {
	if err == nil {
		return nil
	}
	return errors.New(report.Redact(err.Error(), secrets...))
}

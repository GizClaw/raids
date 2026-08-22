package main

import (
	"bytes"
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

	"github.com/GizClaw/gizclaw-go/pkgs/audio/codec/ogg"
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
	if err := result.WriteCaseReports(cfg.Report); err != nil {
		fmt.Fprintf(stderr, "write case reports: %v\n", err)
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
	var astInputModes stringsFlag
	var pairIDs stringsFlag
	fs := flag.NewFlagSet("raidtest run", flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.StringVar(&c.Server, "server", "", "GizClaw Admin Server host:port")
	fs.StringVar(&c.PeerServer, "peer-server", "", "GizClaw Peer/Edge host:port (default: --server)")
	fs.StringVar(&c.Suite, "suite", "", "paired acceptance suite YAML")
	fs.Var(&pairIDs, "pair", "paired suite target ID to run (repeatable; default: all)")
	fs.StringVar(&c.Workflow, "workflow", "", "local Workflow YAML")
	fs.StringVar(&c.RuntimeProfile, "runtime-profile", "default", "deployed base RuntimeProfile ID")
	fs.StringVar(&c.RuntimeProfileFile, "runtime-profile-file", os.Getenv("RAIDTEST_RUNTIME_PROFILE_FILE"), "optional local RuntimeProfile YAML (or RAIDTEST_RUNTIME_PROFILE_FILE); suite mode creates a run-owned profile")
	fs.Var(&memories, "memory-layout", "optional local MemoryLayout YAML (repeatable)")
	fs.StringVar(&c.Plan, "plan", "", "acceptance plan YAML")
	fs.StringVar(&c.Report, "report", "raidtest-report.json", "JSON report path")
	fs.StringVar(&c.OpenAIBaseURL, "openai-base-url", "", "GizClaw OpenAI-compatible base URL")
	fs.StringVar(&c.AgentModel, "agent-model", "", "human-simulation model ID")
	fs.StringVar(&c.JudgeModel, "judge-model", "", "semantic judge model ID")
	fs.StringVar(&c.InputTTSModel, "input-tts-model", "", "OpenAI speech model for realtime/translation input")
	fs.StringVar(&c.InputTTSVoice, "input-tts-voice", "alloy", "OpenAI speech voice")
	fs.Var(&astInputModes, "ast-input-mode", "AST Workspace input mode; repeat to override the default push-to-talk,realtime matrix")
	fs.StringVar(&c.AdminKey.Env, "admin-private-key-env", "", "environment variable containing the Admin private key")
	fs.StringVar(&c.AdminKey.File, "admin-private-key-file", "", "file containing the Admin private key")
	fs.BoolVar(&c.AdminKey.Stdin, "admin-private-key-stdin", false, "read the Admin private key from stdin")
	fs.StringVar(&c.OpenAIKey.Env, "openai-api-key-env", "", "environment variable containing the OpenAI-compatible key")
	fs.StringVar(&c.OpenAIKey.File, "openai-api-key-file", "", "file containing the OpenAI-compatible key")
	fs.BoolVar(&c.OpenAIKey.Stdin, "openai-api-key-stdin", false, "read the OpenAI-compatible key from stdin")
	fs.BoolVar(&c.Keep, "keep", false, "retain run-owned resources for debugging")
	fs.DurationVar(&c.Timeout, "timeout", 2*time.Minute, "per-turn timeout")
	fs.IntVar(&c.CaseParallelism, "case-parallelism", 1, "paired suite case concurrency (1..8)")
	fs.DurationVar(&c.CaseRampUp, "case-ramp-up", 0, "minimum delay between paired suite admissions")
	fs.DurationVar(&c.DiagnosticProbeInterval, "diagnostic-probe-interval", 0, "Peer /server-info probe interval (0 disables; minimum 100ms)")
	if err := fs.Parse(args); err != nil {
		return c, err
	}
	if fs.NArg() != 0 {
		return c, fmt.Errorf("unexpected positional arguments: %s", strings.Join(fs.Args(), " "))
	}
	c.MemoryLayouts = memories
	c.ASTInputModes = astInputModes
	c.Pairs = pairIDs
	fs.Visit(func(f *flag.Flag) {
		switch f.Name {
		case "case-parallelism":
			c.CaseParallelismSet = true
		case "case-ramp-up":
			c.CaseRampUpSet = true
		case "diagnostic-probe-interval":
			c.DiagnosticProbeIntervalSet = true
		}
	})
	if c.AdminKey.Stdin && c.OpenAIKey.Stdin {
		return c, errors.New("admin and OpenAI keys cannot both use stdin")
	}
	return c, c.Validate()
}

func run(ctx context.Context, c config.Config, stdin io.Reader) (result report.Report, runErr error) {
	if c.Suite != "" {
		// The paired suite protocol (per-engine `<target>-test` Testers driven
		// through the raidtest_acceptance_report Tool) was replaced by the
		// relay-protocol Testers under workflows/<raid>/test.yaml and the
		// declarative scenarios under tests/giztest; run those with
		// `gizclaw test run` instead.
		return report.New("unknown"), errors.New("--suite is superseded by tests/giztest (gizclaw test run); the legacy paired runner was retired with the raid package layout")
	}
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
	if (workflow.Driver == "ast-translate" || workflow.Driver == "doubao-realtime") && c.InputTTSModel == "" {
		return result, fmt.Errorf("Workflow driver %q requires --input-tts-model for audio input", workflow.Driver)
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
	result.Server = report.Server{Endpoint: c.Server, PeerEndpoint: c.PeerServer, PublicKey: info.AuthoritativePublicKey.String(), Version: info.Version}
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
	peerConn, _, err := server.Dial(ctx, c.PeerServer, peerKeys, "raidtest-peer-"+runID, nil)
	if err != nil {
		return result, err
	}
	defer peerConn.Close()
	registration, err := peerConn.Client.Register(ctx, "raidtest-register-"+runID, token)
	if err != nil {
		return result, fmt.Errorf("register temporary peer: %w", err)
	}
	if err := recordPeerAndValidateProfile(lifecycle, peerKeys.Public.String(), registration.GetRuntimeProfileName(), closure.ProfileID); err != nil {
		return result, err
	}
	type testWorkspace struct {
		name      string
		inputMode string
		caseIndex int
	}
	var testWorkspaces []testWorkspace
	if workflow.Driver == "pet" {
		if len(testPlan.Cases) != 1 {
			return result, errors.New("pet driver currently requires exactly one Case because each adopted pet owns one persistent Workspace")
		}
		petName := "raidtest-pet-" + runID
		adopted, adoptErr := peerConn.Client.AdoptPet(ctx, "raidtest-adopt-"+runID, rpcapi.RuntimeAdoptRequest{Name: petName, DisplayName: "Raidtest Pet"})
		if adoptErr != nil {
			return result, fmt.Errorf("adopt temporary pet: %w", adoptErr)
		}
		setup.WorkspaceName = adopted.Pet.WorkspaceName
		testWorkspaces = append(testWorkspaces, testWorkspace{name: setup.WorkspaceName, caseIndex: -1})
		lifecycle.Record(report.Lifecycle{ResourceType: "Pet", ID: petName, Action: "create", Status: "pass"})
		lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: setup.WorkspaceName, Action: "create", Status: "pass"})
		defer func() {
			if c.Keep {
				lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: setup.WorkspaceName, Action: "retain", Status: "pass"})
				lifecycle.Record(report.Lifecycle{ResourceType: "Pet", ID: petName, Action: "retain", Status: "pass"})
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
	} else {
		if closure.Collection == "" || closure.WorkflowAlias == "" {
			return result, fmt.Errorf("Workflow %q is not bound to a RuntimeProfile collection", workflow.Source.Metadata.ID)
		}
		inputModes := []string{""}
		if workflow.Driver == "ast-translate" {
			inputModes = c.ASTInputModes
		}
		defer func() {
			for index := len(testWorkspaces) - 1; index >= 0; index-- {
				workspace := testWorkspaces[index]
				if c.Keep {
					lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: workspace.name, Action: "retain", Status: "pass"})
					continue
				}
				cleanupCtx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
				requestID := fmt.Sprintf("raidtest-delete-workspace-%s-%s-case-%02d", runID, workspaceModeSuffix(workspace.inputMode), workspace.caseIndex+1)
				_, deleteErr := peerConn.Client.DeleteWorkspace(cleanupCtx, requestID, rpcapi.WorkspaceDeleteRequest{Name: workspace.name})
				cancel()
				status, detail := "pass", ""
				if deleteErr != nil {
					status, detail = "fail", deleteErr.Error()
					if runErr == nil {
						runErr = deleteErr
					} else {
						runErr = errors.Join(runErr, deleteErr)
					}
				}
				lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: workspace.name, Action: "delete", Status: status, Error: detail})
			}
		}()
		for _, inputMode := range inputModes {
			parameters, parametersErr := workspaceParameters(workflow.Driver, inputMode, workflowStartsAgent(workflow))
			if parametersErr != nil {
				return result, parametersErr
			}
			for caseIndex, plannedCase := range testPlan.Cases {
				caseSuffix := fmt.Sprintf("case-%02d", caseIndex+1)
				workspaceName := setup.WorkspaceName + "-" + caseSuffix
				if inputMode != "" {
					workspaceName += "-" + workspaceModeSuffix(inputMode)
				}
				requestID := "raidtest-create-workspace-" + runID + "-" + workspaceModeSuffix(inputMode) + "-" + caseSuffix
				created, createErr := peerConn.Client.CreateWorkspace(ctx, requestID, rpcapi.WorkspaceCreateRequest{
					Name: workspaceName, Collection: closure.Collection, WorkflowName: closure.WorkflowAlias, Parameters: parameters,
				})
				if createErr != nil {
					result.Cases = append(result.Cases, report.Case{ID: modeCaseID(inputMode, plannedCase.ID+"-workspace-setup"), InputMode: inputMode, Status: "fail", Error: fmt.Sprintf("create temporary Workspace: %v", createErr)})
					continue
				}
				testWorkspaces = append(testWorkspaces, testWorkspace{name: created.Name, inputMode: inputMode, caseIndex: caseIndex})
				lifecycle.Record(report.Lifecycle{ResourceType: "Workspace", ID: created.Name, Action: "create", Status: "pass"})
			}
		}
		if len(testWorkspaces) == 0 {
			return result, errors.New("no temporary Workspace could be created")
		}
	}
	target := &conversation.PeerTarget{Client: peerConn.Client, Timeout: c.Timeout, RequireAudio: workflow.Driver == "ast-translate"}
	defer func() {
		if closeErr := target.Close(); closeErr != nil {
			if runErr == nil {
				runErr = closeErr
			} else {
				runErr = errors.Join(runErr, closeErr)
			}
		}
	}()
	var simulation *agent.Agent
	if c.AgentModel != "" || c.JudgeModel != "" || c.InputTTSModel != "" {
		clusterSession := !c.OpenAIKey.Configured()
		var key []byte
		if clusterSession {
			key, err = openaiapi.LoginPeer(ctx, c.OpenAIBaseURL, peerKeys, info.AuthoritativePublicKey, token)
		} else {
			key, err = c.OpenAIKey.Read(stdin)
		}
		if err != nil {
			return result, err
		}
		// Install redaction before any authenticated request. Preflight failures
		// can include provider response bodies and must not escape with this key.
		defer func() { runErr = reportError(runErr, key) }()
		client := openaiapi.Client{BaseURL: c.OpenAIBaseURL, APIKey: string(key)}
		if c.AgentModel != "" || c.JudgeModel != "" || (!clusterSession && c.InputTTSModel != "") {
			models, modelsErr := client.Models(ctx)
			if modelsErr != nil {
				return result, fmt.Errorf("list models for OpenAI simulation: %w", modelsErr)
			}
			requested := []string{c.AgentModel, c.JudgeModel}
			if !clusterSession {
				requested = append(requested, c.InputTTSModel)
			}
			if modelErr := requireAvailable("model", models, requested...); modelErr != nil {
				return result, modelErr
			}
		}
		if clusterSession && c.InputTTSModel != "" {
			voices, voicesErr := client.Voices(ctx)
			if voicesErr != nil {
				return result, fmt.Errorf("list voices for cluster input speech: %w", voicesErr)
			}
			if voiceErr := requireAvailable("voice", voices, c.InputTTSVoice); voiceErr != nil {
				return result, voiceErr
			}
		}
		if c.AgentModel != "" {
			result.Models["agent"] = c.AgentModel
		}
		if c.JudgeModel != "" {
			result.Models["judge"] = c.JudgeModel
		}
		if c.InputTTSModel != "" {
			result.Models["input_tts"] = c.InputTTSModel
			target.InputAudio = conversation.CacheAudioInput(func(ctx context.Context, text string) (conversation.AudioInput, error) {
				encoded, speechErr := client.Speech(ctx, result.Models["input_tts"], c.InputTTSVoice, text)
				if speechErr != nil {
					return conversation.AudioInput{}, speechErr
				}
				frames, decodeErr := opusFrames(encoded)
				return conversation.AudioInput{MIMEType: "audio/opus", Frames: frames}, decodeErr
			})
		}
		simulation = &agent.Agent{Client: client, Model: result.Models["agent"]}
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
	for _, workspace := range testWorkspaces {
		target.InputMode = workspace.inputMode
		opening, err := target.Select(ctx, workspace.name, closure.WorkflowID, workflowStartsAgent(workflow))
		if err != nil {
			result.Cases = append(result.Cases, report.Case{
				ID: modeCaseID(workspace.inputMode, "workspace-select"), InputMode: workspace.inputMode, Status: "fail",
				Error: fmt.Sprintf("select candidate Workspace: %v", err),
			})
			continue
		}
		workspacePlan := testPlan
		if workspace.caseIndex >= 0 {
			workspacePlan.Cases = []plan.Case{testPlan.Cases[workspace.caseIndex]}
		}
		cases := runner.Run(ctx, workspacePlan)
		for index := range cases {
			if opening.Text != "" {
				openingTurn := report.Turn{
					ID: "agent-opening", Assistant: opening.Text, FirstResponse: opening.FirstResponse,
					TotalResponse: opening.TotalResponse, RuneCount: len([]rune(opening.Text)),
					Evidence: opening.Evidence, Status: "pass",
				}
				if budget := firstResponseBudget(workspacePlan); budget > 0 {
					status := "pass"
					if opening.FirstResponse > budget {
						status = "fail"
						openingTurn.Status = "fail"
						cases[index].Status = "fail"
					}
					openingTurn.Checks = []report.Check{{Name: "first_response", Status: status, Detail: fmt.Sprintf("got=%s max=%s", opening.FirstResponse, budget)}}
				}
				cases[index].Turns = append([]report.Turn{openingTurn}, cases[index].Turns...)
			}
			cases[index].InputMode = workspace.inputMode
			cases[index].ID = modeCaseID(workspace.inputMode, cases[index].ID)
		}
		result.Cases = append(result.Cases, cases...)
	}
	for _, caseResult := range result.Cases {
		if caseResult.Status != "pass" {
			runErr = errors.New("one or more acceptance cases failed")
			break
		}
	}
	return result, runErr
}

func requireAvailable(kind string, available []string, requested ...string) error {
	found := make(map[string]bool, len(available))
	for _, resource := range available {
		found[resource] = true
	}
	for _, resource := range requested {
		if resource != "" && !found[resource] {
			return fmt.Errorf("OpenAI simulation %s alias %q is unavailable; available aliases: %s", kind, resource, strings.Join(available, ", "))
		}
	}
	return nil
}

func workspaceParameters(driver, inputMode string, agentStarts bool) (*rpcapi.WorkspaceParameters, error) {
	if agentStarts && (driver == "flowcraft" || driver == "eino") {
		initiative := rpcapi.FlowcraftConversationParametersInitiativeAgent
		policy := rpcapi.FlowcraftConversationParametersAgentInitiativePolicyOnReload
		conversation := &rpcapi.FlowcraftConversationParameters{Initiative: &initiative, AgentInitiativePolicy: &policy}
		parameters := rpcapi.WorkspaceParameters{}
		if driver == "flowcraft" {
			if err := parameters.FromFlowcraftWorkspaceParameters(rpcapi.FlowcraftWorkspaceParameters{
				AgentType: rpcapi.FlowcraftWorkspaceParametersAgentTypeFlowcraft, Conversation: conversation,
			}); err != nil {
				return nil, fmt.Errorf("encode Flowcraft agent-start Workspace parameters: %w", err)
			}
		} else if err := parameters.FromEinoWorkspaceParameters(rpcapi.EinoWorkspaceParameters{
			AgentType: rpcapi.EinoWorkspaceParametersAgentTypeEino, Conversation: conversation,
		}); err != nil {
			return nil, fmt.Errorf("encode Eino agent-start Workspace parameters: %w", err)
		}
		return &parameters, nil
	}
	if driver != "ast-translate" {
		return nil, nil
	}
	input := rpcapi.WorkspaceInputMode(inputMode)
	if !input.Valid() {
		return nil, fmt.Errorf("unsupported AST Workspace input mode %q", inputMode)
	}
	parameters := rpcapi.WorkspaceParameters{}
	if err := parameters.FromASTTranslateWorkspaceParameters(rpcapi.ASTTranslateWorkspaceParameters{
		AgentType: rpcapi.ASTTranslateWorkspaceParametersAgentTypeAstTranslate,
		Input:     &input,
	}); err != nil {
		return nil, fmt.Errorf("encode AST push-to-talk Workspace parameters: %w", err)
	}
	return &parameters, nil
}

func opusFrames(encoded []byte) ([][]byte, error) {
	packets, err := ogg.ReadAllPackets(bytes.NewReader(encoded))
	if err != nil {
		return nil, fmt.Errorf("decode OpenAI speech Ogg Opus: %w", err)
	}
	frames := make([][]byte, 0, len(packets))
	for _, packet := range packets {
		if bytes.HasPrefix(packet.Data, []byte("OpusHead")) || bytes.HasPrefix(packet.Data, []byte("OpusTags")) || len(packet.Data) == 0 {
			continue
		}
		frames = append(frames, append([]byte(nil), packet.Data...))
	}
	if len(frames) == 0 {
		return nil, errors.New("OpenAI speech Ogg contained no Opus audio packets")
	}
	return frames, nil
}

func recordPeerAndValidateProfile(lifecycle *provision.Lifecycle, publicKey, actualProfile, expectedProfile string) error {
	// Register creates the peer even when the returned binding is wrong. Record it
	// before validation so deferred cleanup owns every successful mutation.
	lifecycle.RecordPeer(publicKey)
	if actualProfile != expectedProfile {
		return fmt.Errorf("temporary peer bound RuntimeProfile %q, want shadow profile %q", actualProfile, expectedProfile)
	}
	return nil
}

func randomID(bytes int) (string, error) {
	b := make([]byte, bytes)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}
func workspaceModeSuffix(mode string) string {
	switch mode {
	case "push-to-talk":
		return "ptt"
	case "realtime":
		return "realtime"
	default:
		return "default"
	}
}
func modeCaseID(mode, id string) string {
	if mode == "" {
		return id
	}
	return workspaceModeSuffix(mode) + ":" + id
}
func driverMatches(workflow, planned string) bool {
	if planned == "scripted-comparison" {
		return workflow == "flowcraft" || workflow == "eino"
	}
	mapping := map[string]string{"flowcraft": "flowcraft", "eino": "eino", "doubao-realtime": "realtime", "ast-translate": "translate", "pet": "pet"}
	return mapping[workflow] == planned
}

func workflowStartsAgent(workflow catalog.Workflow) bool {
	switch workflow.Driver {
	case "flowcraft":
		return workflow.Source.Spec.Flowcraft != nil && workflow.Source.Spec.Flowcraft.Conversation != nil &&
			workflow.Source.Spec.Flowcraft.Conversation.Starts != nil && string(*workflow.Source.Spec.Flowcraft.Conversation.Starts) == "agent"
	case "eino":
		return workflow.Source.Spec.Eino != nil && workflow.Source.Spec.Eino.Conversation != nil &&
			workflow.Source.Spec.Eino.Conversation.Starts != nil && string(*workflow.Source.Spec.Eino.Conversation.Starts) == "agent"
	default:
		return false
	}
}

func firstResponseBudget(p plan.Plan) time.Duration {
	if len(p.Cases) == 0 || len(p.Cases[0].Turns) == 0 {
		return 0
	}
	return p.Cases[0].Turns[0].FirstResponse
}
func reportError(err error, secrets ...[]byte) error {
	if err == nil {
		return nil
	}
	return errors.New(report.Redact(err.Error(), secrets...))
}

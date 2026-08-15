package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
	"github.com/GizClaw/raids/tools/raidtest/internal/acceptance"
	"github.com/GizClaw/raids/tools/raidtest/internal/catalog"
	"github.com/GizClaw/raids/tools/raidtest/internal/config"
	"github.com/GizClaw/raids/tools/raidtest/internal/conversation"
	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/provision"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
	"github.com/GizClaw/raids/tools/raidtest/internal/server"
	"github.com/GizClaw/raids/tools/raidtest/internal/suite"
)

type pairedResources struct {
	profile catalog.GenericResource
	token   catalog.GenericResource
	tool    catalog.GenericResource
	pairs   map[string]pairedPairResources
}

type pairedPairResources struct {
	target        catalog.Workflow
	tester        catalog.Workflow
	targetGeneric catalog.GenericResource
	testerGeneric catalog.GenericResource
	profile       catalog.GenericResource
	tool          catalog.GenericResource
	turns         []plan.Turn
}

type testerEnvelope struct {
	Type                string              `json:"type"`
	CaseID              string              `json:"case_id"`
	TargetWorkflowID    string              `json:"target_workflow_id"`
	ResponseID          string              `json:"response_id"`
	ResponseIndex       int                 `json:"response_index"`
	ExpectedResponses   int                 `json:"expected_responses"`
	CheckpointID        string              `json:"checkpoint_id"`
	TargetRequest       string              `json:"target_request"`
	TargetResponse      string              `json:"target_response,omitempty"`
	TargetHistory       []testerHistoryTurn `json:"target_history,omitempty"`
	FirstResponseMillis int64               `json:"first_response_ms,omitempty"`
	TotalResponseMillis int64               `json:"total_response_ms,omitempty"`
	ToolRetry           int                 `json:"tool_retry,omitempty"`
	PreviousToolError   string              `json:"previous_tool_error,omitempty"`
}

type testerHistoryTurn struct {
	CheckpointID string `json:"checkpoint_id"`
	User         string `json:"user,omitempty"`
	Assistant    string `json:"assistant"`
}

func runPaired(ctx context.Context, c config.Config, stdin io.Reader) (result report.Report, runErr error) {
	runID, err := randomID(6)
	if err != nil {
		return report.New("unknown"), err
	}
	result = report.New(runID)
	loadedSuite, err := suite.Load(c.Suite)
	if err != nil {
		return result, err
	}
	result.SuiteID = loadedSuite.ID
	resources, err := loadPairedResources(loadedSuite)
	if err != nil {
		return result, err
	}
	tokenResource, err := resources.token.Source.AsRegistrationTokenResource()
	if err != nil {
		return result, fmt.Errorf("decode testing RegistrationToken: %w", err)
	}
	if tokenResource.Spec.RuntimeProfileId != loadedSuite.RuntimeProfile.ID {
		return result, fmt.Errorf("testing RegistrationToken binds RuntimeProfile %q, want %q", tokenResource.Spec.RuntimeProfileId, loadedSuite.RuntimeProfile.ID)
	}
	token := tokenResource.Spec.Token
	if strings.TrimSpace(token) == "" {
		return result, errors.New("testing RegistrationToken contains an empty token")
	}
	adminSecret, err := c.AdminKey.Read(stdin)
	if err != nil {
		return result, err
	}
	defer func() {
		runErr = reportError(runErr, adminSecret, []byte(token))
		result.CredentialScan = "pass"
		encoded, encodeErr := json.Marshal(result)
		secret := bytes.TrimSpace(adminSecret)
		if encodeErr != nil {
			result.CredentialScan = "fail"
			runErr = errors.Join(runErr, fmt.Errorf("credential scan encode report: %w", encodeErr))
		} else if len(secret) > 0 && bytes.Contains(encoded, secret) {
			result.CredentialScan = "fail"
			runErr = errors.Join(runErr, errors.New("credential scan found the Admin private key in report evidence"))
		}
	}()
	adminKeys, err := server.KeyPairFromText(adminSecret)
	if err != nil {
		return result, err
	}
	adminConn, info, err := server.Dial(ctx, c.Server, adminKeys, "raidtest-paired-admin-"+runID, nil)
	if err != nil {
		return result, err
	}
	defer adminConn.Close()
	result.Server = report.Server{Endpoint: c.Server, PeerEndpoint: c.PeerServer, PublicKey: info.AuthoritativePublicKey.String(), Version: info.Version}
	api, err := adminConn.Client.ServerAdminClient()
	if err != nil {
		return result, err
	}
	admin := provision.AdminClient{API: api}
	if err := admin.GetReference(ctx, "Workflow", "chatroom"); err != nil {
		return result, fmt.Errorf("verify Admin access with retained Workflow/chatroom: %w", err)
	}
	profileResponse, err := api.GetRuntimeProfileWithResponse(ctx, loadedSuite.RuntimeProfile.ID)
	if err != nil {
		return result, fmt.Errorf("read stable testing RuntimeProfile: %w", err)
	}
	switch profileResponse.StatusCode() {
	case 200:
		if profileResponse.JSON200 == nil {
			return result, errors.New("stable testing RuntimeProfile returned HTTP 200 without a body")
		}
		resources.profile, err = preserveLiveProfileMemories(resources.profile, *profileResponse.JSON200)
		if err != nil {
			return result, err
		}
		result.Lifecycle = append(result.Lifecycle, report.Lifecycle{
			ResourceType: "RuntimeProfile", ID: loadedSuite.RuntimeProfile.ID,
			Action: "reuse-live-memory-bindings", Status: "pass",
		})
	case 404:
		// The checked-in testing profile is the bootstrap source. Subsequent runs
		// preserve the live memory provider connections installed from it.
	default:
		return result, fmt.Errorf("read stable testing RuntimeProfile returned HTTP %d", profileResponse.StatusCode())
	}
	for id, pairResources := range resources.pairs {
		pairResources.profile = resources.profile
		resources.pairs[id] = pairResources
	}
	result.Models, err = pairedModelBindings(resources.profile, loadedSuite.Pairs)
	if err != nil {
		return result, err
	}
	if err := applyPairedResources(ctx, admin, loadedSuite, resources, &result, []byte(token)); err != nil {
		return result, err
	}
	selectedPairs, err := selectSuitePairs(loadedSuite.Pairs, c.Pairs)
	if err != nil {
		return result, err
	}

	var failures []error
	for _, pair := range selectedPairs {
		for repeat := 1; repeat <= pair.Repeats; repeat++ {
			caseID := fmt.Sprintf("%s-%02d", pair.ID, repeat)
			caseResult, caseErr := runPairedCase(ctx, c, admin, loadedSuite, pair, resources.pairs[pair.ID], token, runID, caseID, &result)
			result.Cases = append(result.Cases, caseResult)
			if caseErr != nil {
				failures = append(failures, fmt.Errorf("%s: %w", caseID, caseErr))
			}
		}
	}
	if len(failures) > 0 {
		return result, fmt.Errorf("%d paired acceptance cases failed: %w", len(failures), errors.Join(failures...))
	}
	return result, nil
}

func pairedModelBindings(profileResource catalog.GenericResource, pairs []suite.Pair) (map[string]string, error) {
	profile, err := profileResource.Source.AsRuntimeProfileResource()
	if err != nil {
		return nil, fmt.Errorf("decode testing RuntimeProfile models: %w", err)
	}
	if profile.Spec.Resources.Models == nil {
		return nil, errors.New("testing RuntimeProfile has no model bindings")
	}
	models := make(map[string]string, len(pairs)*2)
	for _, pair := range pairs {
		for _, alias := range []string{pair.TargetWorkflowID + ".model", pair.TesterWorkflowID + ".model"} {
			binding, ok := (*profile.Spec.Resources.Models)[alias]
			if !ok || strings.TrimSpace(binding.ResourceId) == "" {
				return nil, fmt.Errorf("testing RuntimeProfile is missing model binding %q", alias)
			}
			models[alias] = binding.ResourceId
		}
	}
	return models, nil
}

func preserveLiveProfileMemories(local catalog.GenericResource, live apitypes.RuntimeProfile) (catalog.GenericResource, error) {
	if live.Id != local.ID {
		return catalog.GenericResource{}, fmt.Errorf("live RuntimeProfile id %q, want %q", live.Id, local.ID)
	}
	profile, err := local.Source.AsRuntimeProfileResource()
	if err != nil {
		return catalog.GenericResource{}, fmt.Errorf("decode checked-in testing RuntimeProfile: %w", err)
	}
	for _, alias := range []string{"story-teller", "adventure"} {
		if live.Spec.Resources.Memories == nil {
			return catalog.GenericResource{}, errors.New("live testing RuntimeProfile has no memory bindings")
		}
		binding, ok := (*live.Spec.Resources.Memories)[alias]
		if !ok || strings.TrimSpace(binding.LayoutId) == "" {
			return catalog.GenericResource{}, fmt.Errorf("live testing RuntimeProfile is missing memory binding %q", alias)
		}
	}
	profile.Spec.Workflows.Collections = mergeWorkflowCollections(live.Spec.Workflows.Collections, profile.Spec.Workflows.Collections)
	profile.Spec.Resources.Models = mergeBindingMaps(live.Spec.Resources.Models, profile.Spec.Resources.Models)
	profile.Spec.Resources.Tools = mergeBindingMaps(live.Spec.Resources.Tools, profile.Spec.Resources.Tools)
	profile.Spec.Resources.Voices = mergeBindingMaps(live.Spec.Resources.Voices, profile.Spec.Resources.Voices)
	profile.Spec.Resources.PetDefs = mergeBindingMaps(live.Spec.Resources.PetDefs, profile.Spec.Resources.PetDefs)
	profile.Spec.Resources.GameDefs = mergeBindingMaps(live.Spec.Resources.GameDefs, profile.Spec.Resources.GameDefs)
	profile.Spec.Resources.BadgeDefs = mergeBindingMaps(live.Spec.Resources.BadgeDefs, profile.Spec.Resources.BadgeDefs)
	// Existing live Memory bindings win byte-for-byte, including their provider
	// credentials. A missing baseline alias may be added, but raidtest never
	// replaces an already deployed driver or connection.
	profile.Spec.Resources.Memories = mergeBindingMaps(profile.Spec.Resources.Memories, live.Spec.Resources.Memories)
	if err := local.Source.FromRuntimeProfileResource(profile); err != nil {
		return catalog.GenericResource{}, fmt.Errorf("preserve live testing RuntimeProfile memory bindings: %w", err)
	}
	local.Digest = catalog.Digest(local.Source)
	return local, nil
}

func mergeWorkflowCollections(live, desired apitypes.RuntimeProfileWorkflowCollections) apitypes.RuntimeProfileWorkflowCollections {
	merged := make(apitypes.RuntimeProfileWorkflowCollections, len(live)+len(desired))
	for collection, bindings := range live {
		merged[collection] = mergeMap(bindings, nil)
	}
	for collection, bindings := range desired {
		merged[collection] = mergeMap(merged[collection], bindings)
	}
	return merged
}

func mergeBindingMaps[T any](live, desired *map[string]T) *map[string]T {
	if live == nil && desired == nil {
		return nil
	}
	var liveValues, desiredValues map[string]T
	if live != nil {
		liveValues = *live
	}
	if desired != nil {
		desiredValues = *desired
	}
	merged := mergeMap(liveValues, desiredValues)
	return &merged
}

func mergeMap[T any](live, desired map[string]T) map[string]T {
	merged := make(map[string]T, len(live)+len(desired))
	for key, value := range live {
		merged[key] = value
	}
	for key, value := range desired {
		merged[key] = value
	}
	return merged
}

func selectSuitePairs(all []suite.Pair, requested []string) ([]suite.Pair, error) {
	if len(requested) == 0 {
		return all, nil
	}
	index := make(map[string]suite.Pair, len(all))
	for _, pair := range all {
		index[pair.ID] = pair
	}
	selected := make([]suite.Pair, 0, len(requested))
	for _, id := range requested {
		pair, ok := index[id]
		if !ok {
			return nil, fmt.Errorf("suite pair %q does not exist", id)
		}
		selected = append(selected, pair)
	}
	return selected, nil
}

func loadPairedResources(s suite.Suite) (pairedResources, error) {
	loadGeneric := func(ref suite.ResourceRef) (catalog.GenericResource, error) {
		resource, err := catalog.LoadResource(s.Resolve(ref.File))
		if err != nil {
			return catalog.GenericResource{}, err
		}
		if resource.ID != ref.ID {
			return catalog.GenericResource{}, fmt.Errorf("resource %s has metadata.id %q, want %q", ref.File, resource.ID, ref.ID)
		}
		return resource, nil
	}
	profile, err := loadGeneric(s.RuntimeProfile)
	if err != nil {
		return pairedResources{}, err
	}
	token, err := loadGeneric(s.RegistrationToken)
	if err != nil {
		return pairedResources{}, err
	}
	tool, err := loadGeneric(s.Tool)
	if err != nil {
		return pairedResources{}, err
	}
	loaded := pairedResources{profile: profile, token: token, tool: tool, pairs: map[string]pairedPairResources{}}
	for _, pair := range s.Pairs {
		target, err := catalog.LoadWorkflow(s.Resolve(pair.TargetWorkflowFile))
		if err != nil {
			return pairedResources{}, err
		}
		tester, err := catalog.LoadWorkflow(s.Resolve(pair.TesterWorkflowFile))
		if err != nil {
			return pairedResources{}, err
		}
		if target.Source.Metadata.ID != pair.TargetWorkflowID || tester.Source.Metadata.ID != pair.TesterWorkflowID || tester.Driver != "eino" {
			return pairedResources{}, fmt.Errorf("pair %q Workflow identity or Tester driver mismatch", pair.ID)
		}
		targetGeneric, err := catalog.LoadResource(s.Resolve(pair.TargetWorkflowFile))
		if err != nil {
			return pairedResources{}, err
		}
		testerGeneric, err := catalog.LoadResource(s.Resolve(pair.TesterWorkflowFile))
		if err != nil {
			return pairedResources{}, err
		}
		loadedPlan, err := plan.Load(s.Resolve(pair.PlanFile))
		if err != nil {
			return pairedResources{}, err
		}
		loadedPlan, err = loadedPlan.ForWorkflow(pair.TargetWorkflowID)
		if err != nil || len(loadedPlan.Cases) != 1 {
			return pairedResources{}, fmt.Errorf("pair %q plan selection failed: %v", pair.ID, err)
		}
		if !loadedPlan.Paired {
			return pairedResources{}, fmt.Errorf("pair %q external plan must set paired: true", pair.ID)
		}
		loaded.pairs[pair.ID] = pairedPairResources{
			target: target, tester: tester, targetGeneric: targetGeneric, testerGeneric: testerGeneric,
			profile: profile, tool: tool, turns: loadedPlan.Cases[0].Turns,
		}
	}
	return loaded, nil
}

func applyPairedResources(ctx context.Context, admin provision.AdminClient, s suite.Suite, resources pairedResources, result *report.Report, secrets ...[]byte) error {
	ordered := []catalog.GenericResource{resources.tool}
	for _, pair := range s.Pairs {
		target, err := catalog.LoadResource(s.Resolve(pair.TargetWorkflowFile))
		if err != nil {
			return err
		}
		tester, err := catalog.LoadResource(s.Resolve(pair.TesterWorkflowFile))
		if err != nil {
			return err
		}
		ordered = append(ordered, target, tester)
	}
	ordered = append(ordered, resources.profile, resources.token)
	for _, resource := range ordered {
		entry := report.Lifecycle{ResourceType: resource.Kind, ID: resource.ID, Action: "apply", Status: "pass"}
		if resource.Kind == "RuntimeProfile" {
			profile, err := resource.Source.AsRuntimeProfileResource()
			if err != nil {
				return fmt.Errorf("decode stable testing RuntimeProfile: %w", err)
			}
			if err := admin.VerifyProfileReferences(ctx, profile.Spec); err != nil {
				entry.Action, entry.Status, entry.Error = "verify-live-dependencies", "fail", report.Redact(err.Error(), secrets...)
				result.Lifecycle = append(result.Lifecycle, entry)
				return fmt.Errorf("verify stable testing RuntimeProfile dependencies: %w", err)
			}
			result.Lifecycle = append(result.Lifecycle, report.Lifecycle{
				ResourceType: "RuntimeProfile", ID: resource.ID, Action: "verify-live-dependencies", Status: "pass",
			})
		}
		if err := admin.ApplyResource(ctx, resource); err != nil {
			entry.Status, entry.Error = "fail", report.Redact(err.Error(), secrets...)
			result.Lifecycle = append(result.Lifecycle, entry)
			return fmt.Errorf("apply stable testing resource %s/%s: %w", resource.Kind, resource.ID, err)
		}
		liveDigest, err := admin.ReadResourceDigest(ctx, resource)
		if err != nil {
			entry.Status, entry.Error = "fail", report.Redact(err.Error(), secrets...)
			result.Lifecycle = append(result.Lifecycle, entry)
			return fmt.Errorf("read back stable testing resource %s/%s: %w", resource.Kind, resource.ID, err)
		}
		candidateChanged := liveDigest != resource.Digest
		result.Resources.Paired = append(result.Resources.Paired, report.ResourceRef{
			Kind: resource.Kind, SourceID: resource.ID, ShadowID: resource.ID,
			SourceDigest: resource.Digest, ShadowDigest: liveDigest, LiveDigest: liveDigest,
			CandidateChanged: candidateChanged,
		})
		if candidateChanged {
			entry.Status, entry.Error = "fail", "candidate_changed after apply/readback"
			result.Lifecycle = append(result.Lifecycle, entry)
			return fmt.Errorf("candidate_changed for %s/%s after apply/readback", resource.Kind, resource.ID)
		}
		result.Lifecycle = append(result.Lifecycle, entry)
	}
	return nil
}

func runPairedCase(
	ctx context.Context,
	c config.Config,
	admin provision.AdminClient,
	s suite.Suite,
	pair suite.Pair,
	resources pairedPairResources,
	token, runID, caseID string,
	result *report.Report,
) (caseResult report.Case, runErr error) {
	caseResult = report.Case{ID: caseID, InputMode: "paired-eino-tester", Status: "fail"}
	defer func() {
		if runErr != nil && caseResult.Owner == "" {
			caseResult.Owner = pairedFailureOwner(caseResult.Error)
		}
		if runErr == nil || len(caseResult.Turns) >= len(resources.turns) {
			return
		}
		reason := strings.TrimSpace(caseResult.Error)
		if reason == "" {
			reason = runErr.Error()
		}
		for len(caseResult.Turns) < len(resources.turns) {
			planned := resources.turns[len(caseResult.Turns)]
			caseResult.Turns = append(caseResult.Turns, report.Turn{
				ID: planned.ID, TargetWorkflowID: pair.TargetWorkflowID, TesterWorkflowID: pair.TesterWorkflowID,
				Status: "fail", Owner: caseResult.Owner, Error: "not executed after prior checkpoint failure: " + reason,
			})
		}
	}()
	targetKeys, err := giznet.GenerateKeyPair()
	if err != nil {
		caseResult.Error = err.Error()
		return caseResult, err
	}
	testerKeys, err := giznet.GenerateKeyPair()
	if err != nil {
		caseResult.Error = err.Error()
		return caseResult, err
	}
	targetConn, _, err := server.Dial(ctx, c.PeerServer, targetKeys, "raidtest-target-"+caseID, nil)
	if err != nil {
		caseResult.Error = err.Error()
		return caseResult, err
	}
	defer targetConn.Close()
	testerConn, _, err := server.Dial(ctx, c.PeerServer, testerKeys, "raidtest-tester-"+caseID, nil)
	if err != nil {
		caseResult.Error = err.Error()
		return caseResult, err
	}
	defer testerConn.Close()

	defer func() {
		if c.Keep {
			for _, publicKey := range []string{targetKeys.Public.String(), testerKeys.Public.String()} {
				result.Lifecycle = append(result.Lifecycle, report.Lifecycle{ResourceType: "Peer", ID: publicKey, Action: "retain", Status: "pass"})
			}
			return
		}
		cleanupCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
		defer cancel()
		for _, publicKey := range []string{targetKeys.Public.String(), testerKeys.Public.String()} {
			entry := report.Lifecycle{ResourceType: "Peer", ID: publicKey, Action: "delete", Status: "pass"}
			if err := admin.DeletePeer(cleanupCtx, publicKey); err != nil {
				entry.Status, entry.Error = "fail", err.Error()
				if runErr == nil {
					runErr = fmt.Errorf("delete temporary peer %s: %w", publicKey, err)
				}
			}
			result.Lifecycle = append(result.Lifecycle, entry)
		}
	}()
	for _, registration := range []struct {
		role     string
		register func() (string, error)
	}{
		{role: "target", register: func() (string, error) {
			response, err := targetConn.Client.Register(ctx, "raidtest-register-target-"+caseID, token)
			if err != nil {
				return "", err
			}
			return response.GetRuntimeProfileName(), nil
		}},
		{role: "tester", register: func() (string, error) {
			response, err := testerConn.Client.Register(ctx, "raidtest-register-tester-"+caseID, token)
			if err != nil {
				return "", err
			}
			return response.GetRuntimeProfileName(), nil
		}},
	} {
		profile, err := registration.register()
		if err != nil {
			caseResult.Error = fmt.Sprintf("register %s peer: %v", registration.role, err)
			return caseResult, errors.New(caseResult.Error)
		}
		if profile != s.RuntimeProfile.ID {
			caseResult.Error = fmt.Sprintf("%s peer bound RuntimeProfile %q, want %q", registration.role, profile, s.RuntimeProfile.ID)
			return caseResult, errors.New(caseResult.Error)
		}
		publicKey := targetKeys.Public.String()
		if registration.role == "tester" {
			publicKey = testerKeys.Public.String()
		}
		result.Lifecycle = append(result.Lifecycle, report.Lifecycle{
			ResourceType: "Peer", ID: publicKey, Action: "create", Status: "pass",
		})
	}

	var handler acceptance.Handler
	if err := testerConn.Client.HandleTool(s.Tool.InvokeName, handler.Handle); err != nil {
		caseResult.Error = fmt.Sprintf("mount Tester Tool: %v", err)
		return caseResult, errors.New(caseResult.Error)
	}
	targetWorkspace := pairedWorkspaceName("target", runID, caseID)
	testerWorkspace := pairedWorkspaceName("tester", runID, caseID)
	caseResult.TargetPeerID = targetKeys.Public.String()
	caseResult.TesterPeerID = testerKeys.Public.String()
	caseResult.TargetWorkspaceID = targetWorkspace
	caseResult.TesterWorkspaceID = testerWorkspace
	emptyTools := []string{}
	testerTools := []string{"raidtest-acceptance-report"}
	targetParameters, err := workspaceParameters(resources.target.Driver, "", workflowStartsAgent(resources.target))
	if err != nil {
		caseResult.Error = err.Error()
		return caseResult, err
	}
	if err := validateWorkflowToolkit(resources.target.Source.Spec.Toolkit, emptyTools); err != nil {
		caseResult.Error = "target Workflow Toolkit: " + err.Error()
		return caseResult, errors.New(caseResult.Error)
	}
	if err := validateWorkflowToolkit(resources.tester.Source.Spec.Toolkit, testerTools); err != nil {
		caseResult.Error = "Tester Workflow Toolkit: " + err.Error()
		return caseResult, errors.New(caseResult.Error)
	}
	targetCreated, testerCreated := false, false
	defer func() {
		if c.Keep {
			for _, item := range []struct {
				name    string
				created bool
			}{{targetWorkspace, targetCreated}, {testerWorkspace, testerCreated}} {
				if item.created {
					result.Lifecycle = append(result.Lifecycle, report.Lifecycle{ResourceType: "Workspace", ID: item.name, Action: "retain", Status: "pass"})
				}
			}
			return
		}
		cleanupCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
		defer cancel()
		for _, item := range []struct {
			client interface {
				DeleteWorkspace(context.Context, string, rpcapi.WorkspaceDeleteRequest) (*rpcapi.WorkspaceDeleteResponse, error)
			}
			name    string
			created bool
		}{
			{client: targetConn.Client, name: targetWorkspace, created: targetCreated},
			{client: testerConn.Client, name: testerWorkspace, created: testerCreated},
		} {
			if !item.created {
				continue
			}
			entry := report.Lifecycle{ResourceType: "Workspace", ID: item.name, Action: "delete", Status: "pass"}
			if _, err := item.client.DeleteWorkspace(cleanupCtx, "raidtest-delete-"+item.name, rpcapi.WorkspaceDeleteRequest{Name: item.name}); err != nil {
				entry.Status, entry.Error = "fail", err.Error()
				if runErr == nil {
					runErr = fmt.Errorf("delete temporary Workspace %s: %w", item.name, err)
				}
			}
			result.Lifecycle = append(result.Lifecycle, entry)
		}
	}()
	if _, err := targetConn.Client.CreateWorkspace(ctx, "raidtest-create-target-"+caseID, rpcapi.WorkspaceCreateRequest{
		Name: targetWorkspace, Collection: "raidtest-targets", WorkflowName: pair.TargetWorkflowID,
		Parameters: targetParameters, Toolkit: &rpcapi.ToolkitPolicy{ToolNames: &emptyTools},
	}); err != nil {
		caseResult.Error = fmt.Sprintf("create target Workspace: %v", err)
		return caseResult, errors.New(caseResult.Error)
	}
	targetCreated = true
	result.Lifecycle = append(result.Lifecycle, report.Lifecycle{ResourceType: "Workspace", ID: targetWorkspace, Action: "create", Status: "pass"})
	if _, err := testerConn.Client.CreateWorkspace(ctx, "raidtest-create-tester-"+caseID, rpcapi.WorkspaceCreateRequest{
		Name: testerWorkspace, Collection: "raidtest-testers", WorkflowName: pair.TesterWorkflowID,
		Toolkit: &rpcapi.ToolkitPolicy{ToolNames: &testerTools},
	}); err != nil {
		caseResult.Error = fmt.Sprintf("create Tester Workspace: %v", err)
		return caseResult, errors.New(caseResult.Error)
	}
	testerCreated = true
	result.Lifecycle = append(result.Lifecycle, report.Lifecycle{ResourceType: "Workspace", ID: testerWorkspace, Action: "create", Status: "pass"})
	result.Lifecycle = append(result.Lifecycle,
		report.Lifecycle{ResourceType: "Workflow", ID: pair.TargetWorkflowID, Action: "verify-toolkit-deny-all", Status: "pass"},
		report.Lifecycle{ResourceType: "Workflow", ID: pair.TesterWorkflowID, Action: "verify-toolkit-acceptance-only", Status: "pass"},
	)

	target := &conversation.PeerTarget{Client: targetConn.Client, Timeout: c.Timeout}
	tester := &conversation.PeerTarget{Client: testerConn.Client, Timeout: c.Timeout}
	defer target.Close()
	defer tester.Close()
	if err := verifyPairedCandidate(ctx, admin, resources.targetGeneric, resources.testerGeneric, resources.tool, resources.profile); err != nil {
		caseResult.Error = err.Error()
		return caseResult, err
	}
	if _, err := tester.Select(ctx, testerWorkspace, pair.TesterWorkflowID, false); err != nil {
		caseResult.Error = fmt.Sprintf("select Tester Workspace: %v", err)
		return caseResult, errors.New(caseResult.Error)
	}
	opening, err := target.Select(ctx, targetWorkspace, pair.TargetWorkflowID, workflowStartsAgent(resources.target))
	if err != nil {
		caseResult.Error = fmt.Sprintf("select target Workspace: %v", err)
		return caseResult, errors.New(caseResult.Error)
	}

	nextMessage := ""
	responseIndex := 0
	if strings.TrimSpace(opening.Text) == "" {
		submission, _, err := askTester(ctx, tester, &handler, testerEnvelope{
			Type: "BOOTSTRAP", CaseID: caseID, TargetWorkflowID: pair.TargetWorkflowID,
			ResponseID: "bootstrap", CheckpointID: "bootstrap", ExpectedResponses: pair.ExpectedTargetResponses,
		})
		if err != nil {
			caseResult.Error = err.Error()
			return caseResult, err
		}
		if submission.Action != acceptance.ActionContinue {
			caseResult.Error = "Tester did not continue from BOOTSTRAP"
			return caseResult, errors.New(caseResult.Error)
		}
		nextMessage = submission.NextMessage
	} else {
		responseIndex = 1
		submission, testerText, err := evaluateTargetResponse(ctx, tester, &handler, s, pair, caseID, responseIndex, "", caseResult.Turns, opening)
		turn := pairedReportTurn(s, pair, resources.turns[responseIndex-1], "", opening, testerText, submission)
		caseResult.Turns = append(caseResult.Turns, turn)
		if err != nil {
			caseResult.Error = err.Error()
			return caseResult, err
		}
		if err := validatePairedAction(pair, responseIndex, submission); err != nil {
			caseResult.Error = err.Error()
			return caseResult, err
		}
		nextMessage = submission.NextMessage
	}

	for responseIndex < pair.ExpectedTargetResponses {
		if err := verifyPairedCandidate(ctx, admin, resources.targetGeneric, resources.testerGeneric, resources.tool, resources.profile); err != nil {
			caseResult.Error = err.Error()
			return caseResult, err
		}
		nextIndex := responseIndex + 1
		if reload, ok := reloadBefore(pair, resources.turns[nextIndex-1], nextIndex); ok {
			if len(reload.RequiredFacts) > 0 {
				timeout, _ := reload.Duration()
				if err := target.WaitForRecall(ctx, reload.RequiredFacts, timeout); err != nil {
					caseResult.Error = fmt.Sprintf("persistence barrier before response %d: %v", nextIndex, err)
					return caseResult, errors.New(caseResult.Error)
				}
			}
			if err := target.Reload(ctx); err != nil {
				caseResult.Error = fmt.Sprintf("reload target before response %d: %v", nextIndex, err)
				return caseResult, errors.New(caseResult.Error)
			}
		}
		responseID := fmt.Sprintf("%s-response-%02d", caseID, nextIndex)
		response, err := target.Send(ctx, responseID, nextMessage)
		if err != nil {
			caseResult.Error = fmt.Sprintf("target response %d: %v", nextIndex, err)
			failedTurn := pairedTargetErrorTurn(
				s, pair, resources.turns[nextIndex-1], nextMessage, response, caseResult.Error,
			)
			caseResult.Turns = append(caseResult.Turns, failedTurn)
			caseResult.Owner = failedTurn.Owner
			return caseResult, errors.New(caseResult.Error)
		}
		responseIndex = nextIndex
		submission, testerText, judgeErr := evaluateTargetResponse(ctx, tester, &handler, s, pair, caseID, responseIndex, nextMessage, caseResult.Turns, response)
		caseResult.Turns = append(caseResult.Turns, pairedReportTurn(s, pair, resources.turns[responseIndex-1], nextMessage, response, testerText, submission))
		if judgeErr != nil {
			caseResult.Error = judgeErr.Error()
			return caseResult, judgeErr
		}
		if err := validatePairedAction(pair, responseIndex, submission); err != nil {
			caseResult.Error = err.Error()
			return caseResult, err
		}
		nextMessage = submission.NextMessage
	}
	var failedTurns []string
	for _, turn := range caseResult.Turns {
		if turn.Status != "pass" {
			failedTurns = append(failedTurns, turn.ID)
		}
	}
	if len(failedTurns) > 0 {
		for _, turn := range caseResult.Turns {
			if turn.Status != "pass" && turn.Owner != "" {
				caseResult.Owner = turn.Owner
				break
			}
		}
		caseResult.Error = fmt.Sprintf("external timing or Tester checks failed on %s", strings.Join(failedTurns, ", "))
		return caseResult, errors.New(caseResult.Error)
	}
	caseResult.Status = "pass"
	return caseResult, nil
}

func pairedTargetErrorTurn(s suite.Suite, pair suite.Pair, planned plan.Turn, user string, response conversation.Response, detail string) report.Turn {
	turn := pairedReportTurn(s, pair, planned, user, response, "", acceptance.Submission{})
	turn.Status = "fail"
	turn.Error = detail
	phase := "first_response"
	turn.Owner = "transport"
	if response.FirstResponse > 0 || strings.TrimSpace(response.Text) != "" {
		phase = "total_response"
		turn.Owner = "model_provider"
	} else if strings.Contains(strings.ToLower(detail), "context deadline exceeded") {
		turn.Owner = "model_provider"
		for index := range turn.Checks {
			if turn.Checks[index].Name == "first_response" {
				turn.Checks[index].Status = "fail"
				turn.Checks[index].Detail = "no target response before the per-turn deadline"
			}
		}
	}
	if turn.Evidence == nil {
		turn.Evidence = map[string]string{}
	}
	turn.Evidence["timeout_phase"] = phase
	turn.Checks = append(turn.Checks, report.Check{
		Name: "response_complete", Status: "fail", Detail: detail,
		Evidence: fmt.Sprintf("phase=%s captured_runes=%d", phase, turn.RuneCount),
	})
	return turn
}

func validateWorkflowToolkit(policy *apitypes.ToolkitPolicy, want []string) error {
	if policy == nil || policy.ToolIds == nil {
		return errors.New("explicit Workflow Toolkit policy is required")
	}
	got := *policy.ToolIds
	if len(got) != len(want) {
		return fmt.Errorf("Workflow Toolkit has %d tools, want %d", len(got), len(want))
	}
	for index := range want {
		if got[index] != want[index] {
			return fmt.Errorf("Workflow Toolkit tool %d is %q, want %q", index, got[index], want[index])
		}
	}
	return nil
}

func verifyPairedCandidate(ctx context.Context, admin provision.AdminClient, resources ...catalog.GenericResource) error {
	for _, resource := range resources {
		operationCtx, cancel := context.WithTimeout(ctx, 15*time.Second)
		liveDigest, err := admin.ReadResourceDigest(operationCtx, resource)
		cancel()
		if err != nil {
			return fmt.Errorf("candidate_changed: read %s/%s: %w", resource.Kind, resource.ID, err)
		}
		if liveDigest != resource.Digest {
			return fmt.Errorf("candidate_changed: %s/%s digest drifted", resource.Kind, resource.ID)
		}
	}
	return nil
}

func pairedWorkspaceName(role, runID, caseID string) string {
	digest := sha256.Sum256([]byte(caseID))
	return fmt.Sprintf("raidtest-%s-%s-%x", role, runID, digest[:6])
}

func askTester(ctx context.Context, tester *conversation.PeerTarget, handler *acceptance.Handler, envelope testerEnvelope) (acceptance.Submission, string, error) {
	started := time.Now()
	var previousError string
	const (
		maxAttempts               = 3
		acceptanceSubmissionGrace = 2 * time.Second
	)
	for attempt := 0; attempt < maxAttempts; attempt++ {
		result, err := handler.Arm(acceptance.Expectation{
			CaseID: envelope.CaseID, TargetWorkflowID: envelope.TargetWorkflowID, ResponseID: envelope.ResponseID, TurnID: envelope.CheckpointID,
		})
		if err != nil {
			return acceptance.Submission{}, "", err
		}
		envelope.ToolRetry = attempt
		envelope.PreviousToolError = previousError
		if attempt > 0 {
			envelope.Type = "TOOL_RETRY"
		}
		body, err := json.Marshal(envelope)
		if err != nil {
			handler.Cancel()
			return acceptance.Submission{}, "", err
		}
		response, err := tester.Send(ctx, fmt.Sprintf("tester-%s-%d", envelope.ResponseID, attempt), string(body))
		submission, submitted, waitErr := waitForAcceptance(ctx, result, acceptanceSubmissionGrace)
		if waitErr != nil {
			handler.Cancel()
			return acceptance.Submission{}, response.Text, fmt.Errorf("wait for Tester Tool submission for %s: %w", envelope.ResponseID, waitErr)
		}
		if submitted {
			submission.DecisionLatency = time.Since(started)
			return submission, response.Text, nil
		} else {
			toolErr := handler.Cancel()
			if toolErr != nil {
				previousError = toolErr.Error()
			} else if err != nil {
				// A Tester may correctly finish with only the Tool call and no
				// assistant prose. That empty-text error is irrelevant when a
				// correlated submission arrived above, but remains useful evidence
				// when the Tool call is also missing.
				previousError = err.Error()
			} else {
				previousError = "Tester did not call the acceptance Tool"
			}
			if attempt == maxAttempts-1 {
				return acceptance.Submission{}, response.Text, fmt.Errorf("Tester Tool submission for %s failed after %d attempts: %s", envelope.ResponseID, maxAttempts, previousError)
			}
		}
	}
	return acceptance.Submission{}, "", errors.New("unreachable Tester retry state")
}

func waitForAcceptance(ctx context.Context, result <-chan acceptance.Submission, grace time.Duration) (acceptance.Submission, bool, error) {
	timer := time.NewTimer(grace)
	defer timer.Stop()
	select {
	case submission, ok := <-result:
		if !ok {
			return acceptance.Submission{}, false, errors.New("Tester acceptance channel closed without a submission")
		}
		return submission, true, nil
	case <-timer.C:
		return acceptance.Submission{}, false, nil
	case <-ctx.Done():
		return acceptance.Submission{}, false, ctx.Err()
	}
}

func evaluateTargetResponse(
	ctx context.Context,
	tester *conversation.PeerTarget,
	handler *acceptance.Handler,
	s suite.Suite,
	pair suite.Pair,
	caseID string,
	responseIndex int,
	request string,
	priorTurns []report.Turn,
	response conversation.Response,
) (acceptance.Submission, string, error) {
	if strings.TrimSpace(response.Text) == "" {
		return acceptance.Submission{}, "", fmt.Errorf("target response %d is empty", responseIndex)
	}
	responseID := fmt.Sprintf("%s-response-%02d", caseID, responseIndex)
	return askTester(ctx, tester, handler, testerEnvelope{
		Type: "TARGET_RESPONSE", CaseID: caseID, TargetWorkflowID: pair.TargetWorkflowID,
		ResponseID: responseID, ResponseIndex: responseIndex, ExpectedResponses: pair.ExpectedTargetResponses,
		CheckpointID: pair.Checkpoints[responseIndex-1], TargetRequest: request,
		TargetResponse: response.Text, TargetHistory: buildTesterHistory(priorTurns),
		FirstResponseMillis: response.FirstResponse.Milliseconds(),
		TotalResponseMillis: response.TotalResponse.Milliseconds(),
	})
}

func buildTesterHistory(prior []report.Turn) []testerHistoryTurn {
	history := make([]testerHistoryTurn, 0, len(prior))
	for _, turn := range prior {
		history = append(history, testerHistoryTurn{CheckpointID: turn.ID, User: turn.User, Assistant: turn.Assistant})
	}
	return history
}

func validatePairedAction(pair suite.Pair, responseIndex int, submission acceptance.Submission) error {
	if responseIndex < pair.ExpectedTargetResponses {
		if submission.Action != acceptance.ActionContinue {
			return fmt.Errorf("Tester ended at response %d/%d with action %q: %s", responseIndex, pair.ExpectedTargetResponses, submission.Action, submission.Summary)
		}
		return nil
	}
	if submission.Action != acceptance.ActionPass && submission.Action != acceptance.ActionFail {
		return fmt.Errorf("Tester final response %d/%d has non-terminal action %q: %s", responseIndex, pair.ExpectedTargetResponses, submission.Action, submission.Summary)
	}
	return nil
}

func pairedReportTurn(s suite.Suite, pair suite.Pair, planned plan.Turn, user string, response conversation.Response, testerText string, submission acceptance.Submission) report.Turn {
	turn := report.Turn{
		ID: planned.ID, ResponseID: submission.ResponseID,
		TargetWorkflowID: pair.TargetWorkflowID, TesterWorkflowID: pair.TesterWorkflowID,
		User: user, Assistant: response.Text, Tester: testerText, JudgeSummary: submission.Summary,
		TesterDecision: submission.DecisionLatency,
		FirstResponse:  response.FirstResponse, TotalResponse: response.TotalResponse,
		RuneCount: len([]rune(response.Text)), Status: "pass", Evidence: response.Evidence,
	}
	deterministic := planned
	deterministic.FirstResponse = 0
	deterministic.TotalResponse = 0
	turn.Checks = append(turn.Checks, conversation.DeterministicChecks(deterministic, response)...)
	for _, check := range turn.Checks {
		if check.Status != "pass" {
			turn.Status = "fail"
			turn.Owner = "raids_target"
		}
	}
	for _, timing := range []struct {
		name string
		got  time.Duration
		max  time.Duration
	}{
		{name: "first_response", got: response.FirstResponse, max: s.Timing.FirstResponse},
		{name: "total_response", got: response.TotalResponse, max: s.Timing.TotalResponse},
	} {
		status := "pass"
		if timing.got > timing.max {
			status = "fail"
			turn.Status = "fail"
			if turn.Owner == "" {
				turn.Owner = "model_provider"
			}
		}
		turn.Checks = append(turn.Checks, report.Check{
			Name: timing.name, Status: status,
			Detail: fmt.Sprintf("got=%s max=%s", timing.got, timing.max),
		})
	}
	for _, check := range submission.Checks {
		turn.Checks = append(turn.Checks, report.Check{Name: check.Name, Status: check.Status, Detail: check.Detail, Evidence: check.Evidence})
		if check.Status != "pass" {
			turn.Status = "fail"
			turn.Owner = "raids_target"
		}
	}
	if submission.Action == acceptance.ActionFail {
		turn.Checks = append(turn.Checks, report.Check{Name: "tester_verdict", Status: "fail", Detail: submission.Summary})
		turn.Status = "fail"
		turn.Owner = "raids_target"
	}
	return turn
}

func pairedFailureOwner(detail string) string {
	lower := strings.ToLower(detail)
	switch {
	case strings.Contains(lower, "persistence barrier"), strings.Contains(lower, "recall"):
		return "memory_provider"
	case strings.Contains(lower, "tester"), strings.Contains(lower, "acceptance tool"):
		return "raids_tester"
	case strings.Contains(lower, "context deadline exceeded"), strings.Contains(lower, "timed out"), strings.Contains(lower, "timeout"):
		return "environment_dependency"
	case strings.Contains(lower, "register"), strings.Contains(lower, "workspace"), strings.Contains(lower, "reload"):
		return "gizclaw_runtime"
	case strings.Contains(lower, "target response"), strings.Contains(lower, "dial"):
		return "transport"
	case strings.Contains(lower, "digest"), strings.Contains(lower, "candidate"):
		return "deploy_stale"
	default:
		return "raidtest"
	}
}

func reloadBefore(pair suite.Pair, planned plan.Turn, response int) (suite.Reload, bool) {
	for _, reload := range pair.Reloads {
		if reload.BeforeResponse == response {
			return reload, true
		}
	}
	if planned.ReloadBefore {
		reload := suite.Reload{BeforeResponse: response, RequiredFacts: planned.PersistedBeforeReload}
		if planned.PersistenceTimeout > 0 {
			reload.Timeout = planned.PersistenceTimeout.String()
		}
		return reload, true
	}
	return suite.Reload{}, false
}

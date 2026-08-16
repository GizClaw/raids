package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/audio/codec/ogg"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
	"github.com/GizClaw/raids/tools/raidtest/internal/acceptance"
	"github.com/GizClaw/raids/tools/raidtest/internal/catalog"
	"github.com/GizClaw/raids/tools/raidtest/internal/conversation"
	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/provision"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
	"github.com/GizClaw/raids/tools/raidtest/internal/suite"
)

func TestOpusFramesDropsOggHeaders(t *testing.T) {
	var pages []*ogg.Page
	sequence := uint32(0)
	for index, packet := range [][]byte{[]byte("OpusHead"), []byte("OpusTags"), {1, 2, 3}} {
		built, err := ogg.BuildPacketPages(7, sequence, packet, uint64(index*960), index == 0, index == 2)
		if err != nil {
			t.Fatal(err)
		}
		pages = append(pages, built...)
		sequence += uint32(len(built))
	}
	encoded, err := ogg.MarshalPages(pages)
	if err != nil {
		t.Fatal(err)
	}
	frames, err := opusFrames(encoded)
	if err != nil || len(frames) != 1 || !bytes.Equal(frames[0], []byte{1, 2, 3}) {
		t.Fatalf("frames=%#v err=%v", frames, err)
	}
}

func TestASTWorkspaceUsesRequestedInputMode(t *testing.T) {
	for _, mode := range []rpcapi.WorkspaceInputMode{rpcapi.WorkspaceInputModePushToTalk, rpcapi.WorkspaceInputModeRealtime} {
		parameters, err := workspaceParameters("ast-translate", string(mode), false)
		if err != nil {
			t.Fatal(err)
		}
		typed, err := parameters.AsASTTranslateWorkspaceParameters()
		if err != nil || typed.Input == nil || *typed.Input != mode {
			t.Fatalf("mode=%s parameters=%#v typed=%#v err=%v", mode, parameters, typed, err)
		}
	}
	if _, err := workspaceParameters("ast-translate", "text", false); err == nil {
		t.Fatal("unsupported AST input mode was accepted")
	}
	other, err := workspaceParameters("flowcraft", "", false)
	if err != nil || other != nil {
		t.Fatalf("flowcraft parameters=%#v err=%v", other, err)
	}
}

func TestAgentStartWorkspaceParametersAreExplicit(t *testing.T) {
	flowcraft, err := workspaceParameters("flowcraft", "", true)
	if err != nil {
		t.Fatal(err)
	}
	flowcraftTyped, err := flowcraft.AsFlowcraftWorkspaceParameters()
	if err != nil || flowcraftTyped.Conversation == nil || flowcraftTyped.Conversation.Initiative == nil ||
		*flowcraftTyped.Conversation.Initiative != rpcapi.FlowcraftConversationParametersInitiativeAgent ||
		flowcraftTyped.Conversation.AgentInitiativePolicy == nil ||
		*flowcraftTyped.Conversation.AgentInitiativePolicy != rpcapi.FlowcraftConversationParametersAgentInitiativePolicyOnReload {
		t.Fatalf("Flowcraft parameters=%#v typed=%#v err=%v", flowcraft, flowcraftTyped, err)
	}
	eino, err := workspaceParameters("eino", "", true)
	if err != nil {
		t.Fatal(err)
	}
	einoTyped, err := eino.AsEinoWorkspaceParameters()
	if err != nil || einoTyped.Conversation == nil || einoTyped.Conversation.Initiative == nil ||
		*einoTyped.Conversation.Initiative != rpcapi.FlowcraftConversationParametersInitiativeAgent {
		t.Fatalf("Eino parameters=%#v typed=%#v err=%v", eino, einoTyped, err)
	}
}

func TestModeCaseIDIsDistinctAndPreservesNonASTIDs(t *testing.T) {
	if got := modeCaseID("push-to-talk", "workspace-setup"); got != "ptt:workspace-setup" {
		t.Fatalf("PTT case ID = %q", got)
	}
	if got := modeCaseID("realtime", "workspace-setup"); got != "realtime:workspace-setup" {
		t.Fatalf("realtime case ID = %q", got)
	}
	if got := modeCaseID("", "assistant"); got != "assistant" {
		t.Fatalf("non-AST case ID = %q", got)
	}
}

func TestParseFlagsAcceptsOnlySecretSources(t *testing.T) {
	t.Setenv("RAIDTEST_ADMIN", "private")
	var stderr bytes.Buffer
	cfg, err := parseFlags([]string{
		"--server", "admin.example:9820",
		"--peer-server", "edge.example:9821",
		"--workflow", "workflow.yaml",
		"--plan", "plan.yaml",
		"--ast-input-mode", "realtime",
		"--ast-input-mode", "push-to-talk",
		"--admin-private-key-env", "RAIDTEST_ADMIN",
	}, &stderr)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.AdminKey.Env != "RAIDTEST_ADMIN" || cfg.PeerServer != "edge.example:9821" || cfg.OpenAIBaseURL != "http://edge.example:9821/openai/v1" ||
		len(cfg.ASTInputModes) != 2 || cfg.ASTInputModes[0] != "realtime" || cfg.ASTInputModes[1] != "push-to-talk" {
		t.Fatalf("config=%#v", cfg.Redacted())
	}
	stderr.Reset()
	if _, err := parseFlags([]string{"--admin-private-key", "raw-secret"}, &stderr); err == nil {
		t.Fatal("raw private-key argv flag was accepted")
	}
}

func TestParseFlagsTracksExplicitSuiteOnlyControls(t *testing.T) {
	base := []string{"--server", "edge.example:9821", "--workflow", "workflow.yaml", "--plan", "plan.yaml", "--admin-private-key-env", "RAIDTEST_ADMIN"}
	for _, explicit := range [][]string{{"--case-parallelism", "1"}, {"--case-ramp-up", "0"}, {"--diagnostic-probe-interval", "0"}} {
		args := append(append([]string{}, base...), explicit...)
		if _, err := parseFlags(args, &bytes.Buffer{}); err == nil {
			t.Fatalf("explicit suite-only default %v was accepted outside suite mode", explicit)
		}
	}
	cfg, err := parseFlags([]string{"--server", "edge.example:9821", "--suite", "suite.yaml", "--admin-private-key-env", "RAIDTEST_ADMIN", "--case-parallelism", "4", "--case-ramp-up", "250ms", "--diagnostic-probe-interval", "1s"}, &bytes.Buffer{})
	if err != nil {
		t.Fatal(err)
	}
	if cfg.CaseParallelism != 4 || cfg.CaseRampUp != 250*time.Millisecond || cfg.DiagnosticProbeInterval != time.Second {
		t.Fatalf("config=%#v", cfg.Redacted())
	}
}

func TestParseFlagsAcceptsSuiteRuntimeProfileFromEnvironment(t *testing.T) {
	t.Setenv("RAIDTEST_RUNTIME_PROFILE_FILE", "/tmp/volc-mem0-profile.yaml")
	cfg, err := parseFlags([]string{"--server", "edge.example:9821", "--suite", "suite.yaml", "--admin-private-key-env", "RAIDTEST_ADMIN"}, &bytes.Buffer{})
	if err != nil {
		t.Fatal(err)
	}
	if cfg.RuntimeProfileFile != "/tmp/volc-mem0-profile.yaml" {
		t.Fatalf("runtime profile file = %q", cfg.RuntimeProfileFile)
	}
}

func TestRequireAvailableRejectsUnavailableAlias(t *testing.T) {
	if err := requireAvailable("model", []string{"chat", "judge"}, "chat", "judge", ""); err != nil {
		t.Fatal(err)
	}
	err := requireAvailable("voice", []string{"speaker-a", "speaker-b"}, "missing")
	if err == nil || !strings.Contains(err.Error(), "available aliases: speaker-a, speaker-b") {
		t.Fatalf("error=%v", err)
	}
}

func TestReportErrorRedactsAuthenticatedPreflightCredential(t *testing.T) {
	err := reportError(errors.New("preflight echoed session-token"), []byte("session-token"))
	if err == nil || strings.Contains(err.Error(), "session-token") || !strings.Contains(err.Error(), "[REDACTED]") {
		t.Fatalf("error=%v", err)
	}
}

func TestDriverMatchesPublicWorkflowFamilies(t *testing.T) {
	for workflow, planned := range map[string]string{
		"flowcraft":       "flowcraft",
		"eino":            "eino",
		"doubao-realtime": "realtime",
		"ast-translate":   "translate",
		"pet":             "pet",
	} {
		if !driverMatches(workflow, planned) {
			t.Fatalf("driver %q did not match %q", workflow, planned)
		}
	}
	if driverMatches("flowcraft", "translate") {
		t.Fatal("mismatched driver was accepted")
	}
	for _, workflow := range []string{"flowcraft", "eino"} {
		if !driverMatches(workflow, "scripted-comparison") {
			t.Fatalf("scripted comparison rejected %q", workflow)
		}
	}
	if driverMatches("pet", "scripted-comparison") {
		t.Fatal("scripted comparison accepted non-scripted driver")
	}
}

func TestRegistrationMismatchStillRecordsPeerForCleanup(t *testing.T) {
	lifecycle := provision.New(nil, false)
	err := recordPeerAndValidateProfile(lifecycle, "peer-public-key", "wrong-profile", "shadow-profile")
	if err == nil {
		t.Fatal("mismatched RuntimeProfile was accepted")
	}
	if len(lifecycle.Ledger) != 1 || lifecycle.Ledger[0].ResourceType != "Peer" || lifecycle.Ledger[0].ID != "peer-public-key" {
		t.Fatalf("peer was not recorded before validation: %#v", lifecycle.Ledger)
	}
}

func TestValidatePairedActionRequiresExactFinalPass(t *testing.T) {
	pair := suite.Pair{ExpectedTargetResponses: 3}
	if err := validatePairedAction(pair, 1, acceptance.Submission{Action: acceptance.ActionContinue}); err != nil {
		t.Fatal(err)
	}
	if err := validatePairedAction(pair, 2, acceptance.Submission{Action: acceptance.ActionPass}); err == nil {
		t.Fatal("early pass was accepted")
	}
	if err := validatePairedAction(pair, 3, acceptance.Submission{Action: acceptance.ActionContinue}); err == nil {
		t.Fatal("non-terminal final action was accepted")
	}
	if err := validatePairedAction(pair, 3, acceptance.Submission{Action: acceptance.ActionPass}); err != nil {
		t.Fatal(err)
	}
}

func TestReloadBeforeFindsDeclaredResponse(t *testing.T) {
	pair := suite.Pair{Reloads: []suite.Reload{{BeforeResponse: 20, RequiredFacts: []string{"39码"}, Timeout: "60s"}}}
	reload, ok := reloadBefore(pair, plan.Turn{}, 20)
	if !ok || len(reload.RequiredFacts) != 1 {
		t.Fatalf("reload=%#v ok=%v", reload, ok)
	}
	if _, ok := reloadBefore(pair, plan.Turn{}, 19); ok {
		t.Fatal("undeclared reload was returned")
	}
	fromPlan, ok := reloadBefore(suite.Pair{}, plan.Turn{ReloadBefore: true}, 9)
	if !ok || fromPlan.BeforeResponse != 9 {
		t.Fatalf("plan reload=%#v ok=%v", fromPlan, ok)
	}
}

func TestValidatePairedActionAcceptsFinalSemanticFailure(t *testing.T) {
	pair := suite.Pair{ExpectedTargetResponses: 13}
	if err := validatePairedAction(pair, 13, acceptance.Submission{Action: acceptance.ActionFail, Summary: "final response failed"}); err != nil {
		t.Fatal(err)
	}
	if err := validatePairedAction(pair, 12, acceptance.Submission{Action: acceptance.ActionFail}); err == nil {
		t.Fatal("Tester ended before the final response")
	}
}

func TestPairedReportTurnTreatsFinalTesterFailureAsFailedTarget(t *testing.T) {
	turn := pairedReportTurn(
		suite.Suite{Timing: suite.Timing{FirstResponse: 6 * time.Second, TotalResponse: 90 * time.Second}},
		suite.Pair{TargetWorkflowID: "target", TesterWorkflowID: "target-test"},
		plan.Turn{ID: "conclude"}, "请总结",
		conversation.Response{Text: "结论缺少直接证据。", FirstResponse: time.Second, TotalResponse: 2 * time.Second},
		"", acceptance.Submission{Action: acceptance.ActionFail, Summary: "结论把推测写成了事实"},
	)
	if turn.Status != "fail" || turn.Owner != "raids_target" {
		t.Fatalf("turn=%#v", turn)
	}
	found := false
	for _, check := range turn.Checks {
		if check.Name == "tester_verdict" && check.Status == "fail" && check.Detail == "结论把推测写成了事实" {
			found = true
		}
	}
	if !found {
		t.Fatalf("checks=%#v", turn.Checks)
	}
}

func TestPairedTargetErrorTurnRetainsPartialResponseAndTimeoutPhase(t *testing.T) {
	turn := pairedTargetErrorTurn(
		suite.Suite{Timing: suite.Timing{FirstResponse: 6 * time.Second, TotalResponse: 90 * time.Second}},
		suite.Pair{TargetWorkflowID: "target", TesterWorkflowID: "target-test"},
		plan.Turn{ID: "inspect"}, "检查窗户",
		conversation.Response{Text: "已发布但图未结束。", FirstResponse: 2 * time.Second, TotalResponse: 2 * time.Minute},
		"target response 3: context deadline exceeded",
	)
	if turn.Status != "fail" || turn.Owner != "model_provider" || turn.Assistant != "已发布但图未结束。" || turn.Evidence["timeout_phase"] != "total_response" {
		t.Fatalf("turn=%#v", turn)
	}
	found := false
	for _, check := range turn.Checks {
		if check.Name == "response_complete" && check.Status == "fail" {
			found = true
		}
	}
	if !found {
		t.Fatalf("checks=%#v", turn.Checks)
	}
}

func TestPairedTargetErrorTurnMarksMissingFirstResponse(t *testing.T) {
	turn := pairedTargetErrorTurn(
		suite.Suite{Timing: suite.Timing{FirstResponse: 6 * time.Second, TotalResponse: 90 * time.Second}},
		suite.Pair{TargetWorkflowID: "target", TesterWorkflowID: "target-test"},
		plan.Turn{ID: "opening"}, "开始", conversation.Response{TotalResponse: 2 * time.Minute},
		"target response 1: context deadline exceeded",
	)
	if turn.Owner != "model_provider" || turn.Evidence["timeout_phase"] != "first_response" {
		t.Fatalf("turn=%#v", turn)
	}
	found := false
	for _, check := range turn.Checks {
		if check.Name == "first_response" && check.Status == "fail" {
			found = true
		}
	}
	if !found {
		t.Fatalf("checks=%#v", turn.Checks)
	}
}

func TestPairedFailureOwnerPreservesSpecificTimeoutAttribution(t *testing.T) {
	tests := map[string]string{
		"persistence barrier before response 20: timeout":               "memory_provider",
		"wait for Tester Tool submission: context deadline exceeded":    "raids_tester",
		"candidate_changed: read Workflow/x: context deadline exceeded": "environment_dependency",
		"dial target peer: server-info status 502 Bad Gateway":          "environment_dependency",
		"dial target peer: connection refused":                          "environment_dependency",
		"candidate_changed: Workflow/x digest drifted":                  "deploy_stale",
		"target response 3: peer stream closed":                         "transport",
	}
	for detail, want := range tests {
		if got := pairedFailureOwner(detail); got != want {
			t.Fatalf("detail=%q owner=%q want=%q", detail, got, want)
		}
	}
}

func TestSelectSuitePairsPreservesRequestedOrder(t *testing.T) {
	all := []suite.Pair{{ID: "one"}, {ID: "two"}}
	selected, err := selectSuitePairs(all, []string{"two", "one"})
	if err != nil {
		t.Fatal(err)
	}
	if len(selected) != 2 || selected[0].ID != "two" || selected[1].ID != "one" {
		t.Fatalf("selected=%#v", selected)
	}
	if _, err := selectSuitePairs(all, []string{"missing"}); err == nil {
		t.Fatal("missing pair was accepted")
	}
}

func TestPairedWorkspaceNameFitsRuntimeLimitAndStaysDistinct(t *testing.T) {
	first := pairedWorkspaceName("target", "123456789abc", "flowcraft-adventure-castle-mystery-01")
	second := pairedWorkspaceName("target", "123456789abc", "flowcraft-adventure-castle-mystery-02")
	if len(first) > 48 || first == second {
		t.Fatalf("first=%q second=%q", first, second)
	}
}

func TestValidateWorkflowToolkitDistinguishesDenyAllFromInheritance(t *testing.T) {
	empty := []string{}
	if err := validateWorkflowToolkit(&apitypes.ToolkitPolicy{ToolIds: &empty}, nil); err != nil {
		t.Fatal(err)
	}
	if err := validateWorkflowToolkit(nil, nil); err == nil {
		t.Fatal("omitted Workflow Toolkit was accepted as deny-all")
	}
	tester := []string{"raidtest-acceptance-report"}
	if err := validateWorkflowToolkit(&apitypes.ToolkitPolicy{ToolIds: &tester}, tester); err != nil {
		t.Fatal(err)
	}
}

func TestWaitForAcceptanceAllowsDelayedToolDelivery(t *testing.T) {
	result := make(chan acceptance.Submission, 1)
	want := acceptance.Submission{CaseID: "case-1"}
	go func() {
		time.Sleep(20 * time.Millisecond)
		result <- want
	}()
	got, submitted, err := waitForAcceptance(context.Background(), result, time.Second)
	if err != nil || !submitted || got.CaseID != want.CaseID {
		t.Fatalf("submission=%#v submitted=%t err=%v", got, submitted, err)
	}
}

func TestWaitForAcceptanceTimesOutWithoutInventingSubmission(t *testing.T) {
	result := make(chan acceptance.Submission)
	got, submitted, err := waitForAcceptance(context.Background(), result, time.Millisecond)
	if err != nil || submitted || got.CaseID != "" {
		t.Fatalf("submission=%#v submitted=%t err=%v", got, submitted, err)
	}
}

func TestTesterEnvelopeSeparatesCurrentRequestAndResponseFromPriorHistory(t *testing.T) {
	prior := []report.Turn{
		{ID: "opening", User: "先看现场", Assistant: "你看见脚印。"},
		{ID: "inspect-door", User: "检查门锁", Assistant: "门锁完好。"},
	}
	got := buildTesterHistory(prior)
	if len(got) != 2 || got[0].CheckpointID != "opening" || got[1].CheckpointID != "inspect-door" ||
		got[1].User != "检查门锁" || got[1].Assistant != "门锁完好。" {
		t.Fatalf("history=%#v", got)
	}
	for _, turn := range got {
		if turn.CheckpointID == "inspect-window" || turn.Assistant == "窗闩完好。" {
			t.Fatalf("current response was duplicated in target_history: %#v", got)
		}
	}
	payload, err := json.Marshal(testerEnvelope{
		TargetRequest:  "检查窗户",
		TargetResponse: "窗闩完好。",
		TargetHistory:  got,
	})
	if err != nil {
		t.Fatal(err)
	}
	var decoded testerEnvelope
	if err := json.Unmarshal(payload, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.TargetRequest != "检查窗户" || decoded.TargetResponse != "窗闩完好。" || len(decoded.TargetHistory) != 2 {
		t.Fatalf("payload=%s", payload)
	}
	openingPayload, err := json.Marshal(testerEnvelope{})
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Contains(openingPayload, []byte(`"target_request":""`)) {
		t.Fatalf("opening payload omitted explicit empty target_request: %s", openingPayload)
	}
}

func TestPreserveLiveProfileMemoriesKeepsProviderConnections(t *testing.T) {
	local, err := catalog.LoadResource("../../../../runtime-profiles/testing.yaml")
	if err != nil {
		t.Fatal(err)
	}
	profile, err := local.Source.AsRuntimeProfileResource()
	if err != nil {
		t.Fatal(err)
	}
	liveMemories := *profile.Spec.Resources.Memories
	story := liveMemories["story-teller"]
	story.LayoutId = "live-story-layout"
	liveMemories["story-teller"] = story
	profile.Spec.Resources.Memories = &liveMemories

	got, err := preserveLiveProfileMemories(local, apitypes.RuntimeProfile{Id: "testing", Spec: profile.Spec})
	if err != nil {
		t.Fatal(err)
	}
	gotProfile, err := got.Source.AsRuntimeProfileResource()
	if err != nil {
		t.Fatal(err)
	}
	if binding := (*gotProfile.Spec.Resources.Memories)["story-teller"]; binding.LayoutId != "live-story-layout" {
		t.Fatalf("memory binding was overwritten: %#v", binding)
	}
}

func TestConfigureTemporaryPairedIdentityRebindsTokenAndPairs(t *testing.T) {
	loadedSuite, err := suite.Load("../../suites/pr61-paired.yaml")
	if err != nil {
		t.Fatal(err)
	}
	resources, err := loadPairedResources(loadedSuite)
	if err != nil {
		t.Fatal(err)
	}
	if err := configureTemporaryPairedIdentity(&loadedSuite, &resources, "abc123"); err != nil {
		t.Fatal(err)
	}
	if loadedSuite.RuntimeProfile.ID != "raidtest-profile-abc123" || loadedSuite.RegistrationToken.ID != "raidtest-token-abc123" {
		t.Fatalf("suite identities = %#v %#v", loadedSuite.RuntimeProfile, loadedSuite.RegistrationToken)
	}
	token, err := resources.token.Source.AsRegistrationTokenResource()
	if err != nil {
		t.Fatal(err)
	}
	if token.Spec.RuntimeProfileId != loadedSuite.RuntimeProfile.ID {
		t.Fatalf("token profile = %q", token.Spec.RuntimeProfileId)
	}
	for id, pair := range resources.pairs {
		if pair.profile.ID != loadedSuite.RuntimeProfile.ID {
			t.Fatalf("pair %s profile = %q", id, pair.profile.ID)
		}
	}
}

func TestPairedModelBindingsRecordsTargetAndTesterModels(t *testing.T) {
	profile, err := catalog.LoadResource("../../../../runtime-profiles/testing.yaml")
	if err != nil {
		t.Fatal(err)
	}
	loadedSuite, err := suite.Load("../../suites/pr61-paired.yaml")
	if err != nil {
		t.Fatal(err)
	}
	models, err := pairedModelBindings(profile, loadedSuite.Pairs)
	if err != nil {
		t.Fatal(err)
	}
	if len(models) != len(loadedSuite.Pairs)*2 || models["flowcraft-murder-mystery-test.model"] == "" {
		t.Fatalf("models=%#v", models)
	}
}

func TestPreserveLiveProfileMemoriesRejectsIncompleteLiveProfile(t *testing.T) {
	local, err := catalog.LoadResource("../../../../runtime-profiles/testing.yaml")
	if err != nil {
		t.Fatal(err)
	}
	empty := map[string]apitypes.RuntimeProfileMemoryBinding{}
	_, err = preserveLiveProfileMemories(local, apitypes.RuntimeProfile{
		Id: "testing", Spec: apitypes.RuntimeProfileSpec{Resources: apitypes.RuntimeProfileResources{Memories: &empty}},
	})
	if err == nil || !strings.Contains(err.Error(), "story-teller") {
		t.Fatalf("error=%v", err)
	}
}

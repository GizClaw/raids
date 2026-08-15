package catalog

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
)

func TestLoadWorkflowSupportsEveryCandidateDriver(t *testing.T) {
	fixtures := map[string]string{
		"workflow-flowcraft.yaml": "flowcraft",
		"workflow-eino.yaml":      "eino",
		"workflow-realtime.yaml":  "doubao-realtime",
		"workflow-translate.yaml": "ast-translate",
		"workflow-pet.yaml":       "pet",
	}
	for file, driver := range fixtures {
		t.Run(driver, func(t *testing.T) {
			workflow, err := LoadWorkflow("../../testdata/" + file)
			if err != nil {
				t.Fatal(err)
			}
			if workflow.Driver != driver {
				t.Fatalf("driver=%q want=%q", workflow.Driver, driver)
			}
		})
	}
}

func TestDefaultCandidateResourcesMatchV025PublicTypes(t *testing.T) {
	root := "../../../../"
	workflows := []string{
		"workflows/eino/adventure-castle-mystery.yaml",
		"workflows/eino/adventure-monster-maze.yaml",
		"workflows/eino/adventure-space-rescue.yaml",
		"workflows/eino/journey-history.yaml",
		"workflows/eino/journey-memory-recall.yaml",
		"workflows/eino/journey-memory-async.yaml",
		"workflows/eino/story-aesop.yaml",
		"workflows/eino/story-alice.yaml",
		"workflows/flowcraft/adventure-castle-mystery.yaml",
		"workflows/flowcraft/adventure-monster-maze.yaml",
		"workflows/flowcraft/adventure-space-rescue.yaml",
		"workflows/flowcraft/chat-assistant.yaml",
		"workflows/flowcraft/journey-guide.yaml",
		"workflows/flowcraft/murder-mystery.yaml",
		"workflows/flowcraft/story-aesop.yaml",
		"workflows/flowcraft/story-alice.yaml",
		"workflows/doubao-realtime/conversation.yaml",
		"workflows/pet/pet-care.yaml",
		"workflows/ast-translate/zh-ja.yaml",
	}
	for _, path := range workflows {
		if _, err := LoadWorkflow(root + path); err != nil {
			t.Fatalf("%s: %v", path, err)
		}
	}
	for _, path := range []string{"memory-layouts/adventure.yaml", "memory-layouts/pet-care.yaml", "memory-layouts/user-chat-with-assistant.yaml"} {
		if _, err := LoadMemoryLayout(root + path); err != nil {
			t.Fatalf("%s: %v", path, err)
		}
	}
	if _, err := LoadRuntimeProfile(root + "runtime-profiles/default.yaml"); err != nil {
		t.Fatal(err)
	}
}

func TestLoadEinoJourneyCatalogWorkflows(t *testing.T) {
	for _, path := range []string{
		"../../../../workflows/eino/journey-history.yaml",
		"../../../../workflows/eino/journey-memory-recall.yaml",
		"../../../../workflows/eino/journey-memory-async.yaml",
	} {
		workflow, err := LoadWorkflow(path)
		if err != nil {
			t.Fatalf("%s: %v", path, err)
		}
		if workflow.Driver != "eino" {
			t.Fatalf("%s driver=%q want eino", path, workflow.Driver)
		}
	}
}

func TestBuildClosureRewritesWorkflowAndMemory(t *testing.T) {
	profileJSON := []byte(`{"workflows":{"system":{"pet":"pet-care","friend_chatroom":"chatroom","group_chatroom":"chatroom"},"collections":{"assistants":{"general":{"resource_id":"flowcraft-chat-assistant"}}}},"resources":{"memories":{"assistant":{"layout_id":"assistant-memory","driver":"flowcraft"}}}}`)
	var spec apitypes.RuntimeProfileSpec
	if err := json.Unmarshal(profileJSON, &spec); err != nil {
		t.Fatal(err)
	}
	alias := apitypes.WorkflowMemoryAlias("assistant")
	w := Workflow{Source: Resource[apitypes.WorkflowSpec]{Metadata: Metadata{ID: "flowcraft-chat-assistant"}, Spec: apitypes.WorkflowSpec{Memory: &alias}}}
	p := RuntimeProfile{Source: Resource[apitypes.RuntimeProfileSpec]{Metadata: Metadata{ID: "default"}, Spec: spec}}
	m := MemoryLayout{Source: Resource[apitypes.MemoryLayoutSpec]{Metadata: Metadata{ID: "assistant-memory"}}}
	closure, err := BuildClosure(w, p, []MemoryLayout{m}, "abc123")
	if err != nil {
		t.Fatal(err)
	}
	encoded, _ := json.Marshal(closure.Profile.Source.Spec)
	for _, want := range []string{closure.WorkflowID, closure.MemoryIDs["assistant-memory"]} {
		if !contains(string(encoded), want) {
			t.Fatalf("profile %s does not contain %s", encoded, want)
		}
	}
	if closure.Collection != "assistants" || closure.WorkflowAlias != "general" {
		t.Fatalf("workspace selection = %q/%q", closure.Collection, closure.WorkflowAlias)
	}
}

func TestBuildClosureRejectsAmbiguousCollectionBinding(t *testing.T) {
	var spec apitypes.RuntimeProfileSpec
	if err := json.Unmarshal([]byte(`{"workflows":{"system":{"pet":"pet","friend_chatroom":"chat","group_chatroom":"chat"},"collections":{"assistants":{"first":{"resource_id":"workflow"},"second":{"resource_id":"workflow"}}}},"resources":{}}`), &spec); err != nil {
		t.Fatal(err)
	}
	w := Workflow{Source: Resource[apitypes.WorkflowSpec]{Metadata: Metadata{ID: "workflow"}}}
	p := RuntimeProfile{Source: Resource[apitypes.RuntimeProfileSpec]{Metadata: Metadata{ID: "default"}, Spec: spec}}
	if _, err := BuildClosure(w, p, nil, "run"); err == nil {
		t.Fatal("expected ambiguous collection binding error")
	}
}

func TestBuildClosureRejectsUnboundWorkflow(t *testing.T) {
	var spec apitypes.RuntimeProfileSpec
	_ = json.Unmarshal([]byte(`{"workflows":{"system":{"pet":"pet-care","friend_chatroom":"chatroom","group_chatroom":"chatroom"},"collections":{}},"resources":{}}`), &spec)
	w := Workflow{Source: Resource[apitypes.WorkflowSpec]{Metadata: Metadata{ID: "missing"}}}
	p := RuntimeProfile{Source: Resource[apitypes.RuntimeProfileSpec]{Metadata: Metadata{ID: "default"}, Spec: spec}}
	if _, err := BuildClosure(w, p, nil, "run"); err == nil {
		t.Fatal("expected unbound workflow error")
	}
}

func TestBuildClosureRejectsUnrelatedMemoryOverlay(t *testing.T) {
	alias := apitypes.WorkflowMemoryAlias("assistant")
	workflowSpec := apitypes.WorkflowSpec{Memory: &alias}
	var profileSpec apitypes.RuntimeProfileSpec
	if err := json.Unmarshal([]byte(`{"workflows":{"system":{"pet":"pet","friend_chatroom":"chat","group_chatroom":"chat"},"collections":{"assistants":{"general":{"resource_id":"workflow"}}}},"resources":{"memories":{"assistant":{"layout_id":"selected","driver":"flowcraft","connection":{"local":{}}}}}}`), &profileSpec); err != nil {
		t.Fatal(err)
	}
	w := Workflow{Source: Resource[apitypes.WorkflowSpec]{Metadata: Metadata{ID: "workflow"}, Spec: workflowSpec}}
	p := RuntimeProfile{Source: Resource[apitypes.RuntimeProfileSpec]{Metadata: Metadata{ID: "default"}, Spec: profileSpec}}
	unrelated := MemoryLayout{Source: Resource[apitypes.MemoryLayoutSpec]{Metadata: Metadata{ID: "unrelated"}}}
	if _, err := BuildClosure(w, p, []MemoryLayout{unrelated}, "run"); err == nil {
		t.Fatal("expected unrelated memory overlay error")
	}
}

func TestBuildClosureDoesNotRewriteSameNamedModelResource(t *testing.T) {
	profileJSON := []byte(`{"workflows":{"system":{"pet":"pet-care","friend_chatroom":"chatroom","group_chatroom":"chatroom"},"collections":{"assistants":{"general":{"resource_id":"same-id"}}}},"resources":{"models":{"llm":{"resource_id":"same-id"}},"voices":{},"memories":{}}}`)
	var spec apitypes.RuntimeProfileSpec
	if err := json.Unmarshal(profileJSON, &spec); err != nil {
		t.Fatal(err)
	}
	w := Workflow{Source: Resource[apitypes.WorkflowSpec]{Metadata: Metadata{ID: "same-id"}}}
	p := RuntimeProfile{Source: Resource[apitypes.RuntimeProfileSpec]{Metadata: Metadata{ID: "default"}, Spec: spec}}
	closure, err := BuildClosure(w, p, nil, "run")
	if err != nil {
		t.Fatal(err)
	}
	b, _ := json.Marshal(closure.Profile.Source.Spec)
	if !contains(string(b), `"resource_id":"same-id"`) {
		t.Fatalf("same-named model binding was rewritten: %s", b)
	}
}

func TestShadowIDPreservesRunSuffixForLongSourceIDs(t *testing.T) {
	source := strings.Repeat("long-resource-", 8)
	first := shadowID(source, "aaaaaaaaaaaa")
	second := shadowID(source, "bbbbbbbbbbbb")
	if first == second {
		t.Fatalf("long source produced colliding IDs: %q", first)
	}
	if len(first) > 63 || !strings.HasSuffix(first, "-aaaaaaaaaaaa") {
		t.Fatalf("shadow ID does not preserve bounded run suffix: %q", first)
	}
}

func TestLoadWorkflowRejectsUnknownFields(t *testing.T) {
	path := filepath.Join(t.TempDir(), "workflow.yaml")
	data := []byte("apiVersion: gizclaw.admin/v1alpha1\nkind: Workflow\nmetadata: {id: bad}\nspec:\n  driver: flowcraft\n  made_up: true\n  flowcraft:\n    graph: {name: bad, entry: end, nodes: [], edges: []}\n")
	if err := os.WriteFile(path, data, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadWorkflow(path); err == nil {
		t.Fatal("expected unknown-field error")
	}
}

func TestLoadGenericClientRPCTool(t *testing.T) {
	resource, err := LoadResource("../../../../tool-resources/raidtest-acceptance-report.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if resource.Kind != "Tool" || resource.ID != "raidtest-acceptance-report" || resource.Digest == "" {
		t.Fatalf("resource=%#v", resource)
	}
	tool, err := resource.Source.AsToolResource()
	if err != nil {
		t.Fatal(err)
	}
	spec, err := tool.Spec.AsClientRPCToolSpec()
	if err != nil || spec.InvokeName != "raidtest_acceptance_report" {
		t.Fatalf("spec=%#v err=%v", spec, err)
	}
}

func contains(haystack, needle string) bool {
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return true
		}
	}
	return false
}

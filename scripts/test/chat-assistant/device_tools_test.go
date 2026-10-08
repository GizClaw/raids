package chatassistant

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"reflect"
	"slices"
	"strings"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/runtime/toolcatalog"
)

var profilePaths = []string{"runtime-profiles/default.yaml", "runtime-profiles/testing.yaml", "runtime-profile.example.yaml"}

type deviceCall struct {
	owner  string
	alias  string
	target map[string]any
	args   json.RawMessage
}

// Only capability observations and the device transport are controlled here.
// Alias selection, generated schemas and dispatch use the released runtime.
type deviceFixture struct {
	availability map[string]toolcatalog.Availability
	calls        []deviceCall
	nonce        string
}

func newDeviceFixture(t *testing.T) *deviceFixture {
	t.Helper()
	nonce := make([]byte, 16)
	if _, err := rand.Read(nonce); err != nil {
		t.Fatal(err)
	}
	return &deviceFixture{nonce: hex.EncodeToString(nonce)}
}

func (d *deviceFixture) Inspect(_ context.Context, owner string, _ apitypes.RuntimeProfile, tool toolcatalog.Tool) (toolcatalog.Availability, error) {
	if owner != "chat-contract-owner" {
		return toolcatalog.Availability{}, errors.New("wrong Peer owner")
	}
	if availability, ok := d.availability[tool.Alias]; ok {
		return availability, nil
	}
	return toolcatalog.Availability{Supported: true, Online: true}, nil
}

func (d *deviceFixture) Invoke(ctx context.Context, owner string, _ apitypes.RuntimeProfile, tool toolcatalog.Tool, args json.RawMessage) (json.RawMessage, error) {
	if err := tool.Authorize(ctx); err != nil {
		return nil, err
	}
	d.calls = append(d.calls, deviceCall{owner, tool.Alias, tool.Target, append(json.RawMessage(nil), args...)})
	return json.Marshal(map[string]any{"receipt": d.nonce})
}

func TestShippedInnerToolBindingsAndDispatch(t *testing.T) {
	for _, path := range profilePaths {
		t.Run(path, func(t *testing.T) {
			profile := chatProfile(t, path)
			workflow := profile.Spec.Workflows["general-assistant"]
			if workflow.Toolkit == nil || workflow.Toolkit.VerificationModel == nil ||
				*workflow.Toolkit.VerificationModel != "eino-chat-assistant.model" ||
				(*profile.Spec.Resources.Models)[*workflow.Toolkit.VerificationModel].ResourceId != "doubao-seed-2-1-lite" {
				t.Fatal("Chat device operations lost their bound verification Model")
			}
			invoker := profileSearchToolkit(t, &fixture{}, &profile, nil)
			device := newDeviceFixture(t)
			invoker.Catalog.Devices = device
			definitions, err := invoker.ResolveTools(t.Context())
			if err != nil || len(definitions) != 10 {
				t.Fatalf("supported Chat definitions=%v, error=%v", definitions, err)
			}
			encoded, err := json.Marshal(definitions)
			if err != nil {
				t.Fatal(err)
			}
			t.Logf("model catalog: %d tools, %d Workflow aliases, %d JSON bytes", len(definitions), len(profile.Spec.Workflows), len(encoded))
			catalog, err := invoker.ResolveCatalog(t.Context())
			if err != nil {
				t.Fatal(err)
			}
			bound := make(map[string]toolcatalog.Tool)
			for _, tool := range catalog {
				if !tool.Available || tool.FunctionName != strings.ReplaceAll(tool.Alias, ".", "_") {
					t.Fatalf("invalid shipped binding: %+v", tool)
				}
				bound[tool.Alias] = tool
			}

			for _, test := range []struct {
				alias, id, hwd, operation string
			}{
				{"screen.get", "display.main", "display", "read"},
				{"screen.brightness", "display.main", "display", "write"},
				{"light.get", "led.status", "led", "read"},
				{"light.brightness", "led.status", "led", "write"},
			} {
				tool := bound[test.alias]
				if tool.Source != "mhs" || tool.Target["id"] != test.id ||
					tool.Target["hwd"] != test.hwd || tool.Target["operation"] != test.operation {
					t.Fatalf("%s changed its concrete target: %+v", test.alias, tool)
				}
				if test.operation == "write" {
					if len(tool.Schema.Properties) != 1 || tool.Schema.Properties["brightness_percent"] == nil {
						t.Fatalf("%s exposes fields H106 does not support: %+v", test.alias, tool.Schema)
					}
				}
			}
			for alias, procedure := range map[string]string{
				"music.status": "audioplayer.get", "music.playlist": "audioplayer.playlist.get",
				"music.play": "audioplayer.play", "music.stop": "audioplayer.stop",
				"workflow.switch": "run.workspace.set",
			} {
				tool := bound[alias]
				if tool.Source != "client_tool" || tool.Target["name"] != procedure {
					t.Fatalf("%s changed its fixed procedure: %+v", alias, tool)
				}
			}
			switchTool := bound["workflow.switch"]
			if len(switchTool.Schema.Properties["workflow_name"].Enum) != len(profile.Spec.Workflows) ||
				switchTool.Schema.Properties["workspace_name"] != nil {
				t.Fatal("program selection must use exactly the Profile Workflow aliases")
			}
			target := "general-assistant"
			if _, ok := profile.Spec.Workflows["eino-story-aesop"]; ok {
				target = "eino-story-aesop"
				if !strings.Contains(switchTool.Description, target+" = 伊索寓言") {
					t.Fatal("model cannot map the story name to its bound alias")
				}
			}
			switchArgs, _ := json.Marshal(map[string]any{"workflow_name": target})
			for _, test := range []struct{ alias, args string }{
				{"screen.get", "{}"}, {"light.get", "{}"},
				{"screen.brightness", `{"brightness_percent":30}`},
				{"light.brightness", `{"brightness_percent":70}`},
				{"music.status", "{}"}, {"music.playlist", "{}"},
				{"music.play", "{}"}, {"music.play", `{"index":1}`}, {"music.stop", "{}"},
				{"workflow.switch", string(switchArgs)},
			} {
				before := len(device.calls)
				tool := bound[test.alias]
				result, err := invoker.InvokeTool(t.Context(), tool.FunctionName, json.RawMessage(test.args))
				var receipt map[string]string
				if err != nil || json.Unmarshal(result, &receipt) != nil || receipt["receipt"] != device.nonce ||
					len(device.calls) != before+1 {
					t.Fatalf("%s lost the actual device result: %s, %v", test.alias, result, err)
				}
				call := device.calls[before]
				if call.owner != "chat-contract-owner" || call.alias != test.alias ||
					!reflect.DeepEqual(call.target, tool.Target) || string(call.args) != test.args {
					t.Fatalf("%s misrouted arguments: %+v", test.alias, call)
				}
			}

			for _, test := range []struct{ alias, args string }{
				{"screen.get", `{"id":"display.other"}`},
				{"light.get", `{"brightness_percent":50}`},
				{"screen.brightness", "{}"},
				{"screen.brightness", `{"brightness_percent":101}`},
				{"light.brightness", `{"brightness_percent":-1}`},
				{"light.brightness", `{"brightness_percent":1.5}`},
				{"screen.brightness", `{"brightness_percent":30,"enabled":true}`},
				{"light.brightness", `{"brightness_percent":30,"id":"room.light"}`},
				{"music.play", `{"index":-1}`},
				{"music.play", `{"tool":"device.reboot"}`},
				{"music.stop", `{"peer_id":"other"}`},
				{"workflow.switch", `{"workflow_name":"unbound-story"}`},
				{"workflow.switch", `{"workspace_name":"other"}`},
			} {
				before := len(device.calls)
				result, err := invoker.InvokeTool(t.Context(), bound[test.alias].FunctionName, json.RawMessage(test.args))
				if err != nil || !strings.Contains(string(result), `"invalid_arguments"`) || len(device.calls) != before {
					t.Fatalf("%s allowed unsafe arguments %s: %s, %v", test.alias, test.args, result, err)
				}
			}
			// Revocation after definitions were already exposed must prevent a write.
			workflow.Toolkit = nil
			profile.Spec.Workflows["general-assistant"] = workflow
			before := len(device.calls)
			result, err := invoker.InvokeTool(t.Context(), "screen_brightness", json.RawMessage(`{"brightness_percent":20}`))
			if err != nil || !strings.Contains(string(result), `"unavailable"`) || len(device.calls) != before {
				t.Fatalf("revoked write reached device: %s, %v", result, err)
			}
		})
	}
}

func TestDeviceCapabilityAvailabilityFiltersInjection(t *testing.T) {
	for _, path := range profilePaths {
		t.Run(path, func(t *testing.T) {
			profile := chatProfile(t, path)
			invoker := profileSearchToolkit(t, &fixture{}, &profile, nil)
			device := newDeviceFixture(t)
			device.availability = map[string]toolcatalog.Availability{
				"screen.brightness": {Supported: true, Online: false, Reason: "offline"},
				"light.brightness":  {Online: true, Reason: "unsupported"},
				"music.play":        {Online: true, Reason: "capability_unknown"},
			}
			invoker.Catalog.Devices = device
			definitions, err := invoker.ResolveTools(t.Context())
			if err != nil || len(definitions) != 7 {
				t.Fatalf("unavailable tools leaked into model definitions: %v, %v", definitions, err)
			}
			for _, definition := range definitions {
				if slices.Contains([]string{"screen_brightness", "light_brightness", "music_play"}, definition.Name) {
					t.Fatalf("unavailable tool was injected: %s", definition.Name)
				}
			}
			catalog, err := invoker.ResolveCatalog(t.Context())
			if err != nil || len(catalog) != 10 {
				t.Fatalf("discovery lost configured unavailable tools: %v, %v", catalog, err)
			}
			for _, tool := range catalog {
				if unavailable, ok := device.availability[tool.Alias]; ok && (tool.Available || tool.Reason != unavailable.Reason) {
					t.Fatalf("discovery lost unavailable reason: %+v", tool)
				}
			}
			for _, name := range []string{"screen_brightness", "light_brightness", "music_play"} {
				result, err := invoker.InvokeTool(t.Context(), name, json.RawMessage("{}"))
				if err != nil || !strings.Contains(string(result), `"unavailable"`) || len(device.calls) != 0 {
					t.Fatalf("%s reached an unavailable device: %s, %v", name, result, err)
				}
			}
		})
	}
}

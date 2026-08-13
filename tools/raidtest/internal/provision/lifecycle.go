package provision

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"strings"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/adminhttp"
	"github.com/GizClaw/raids/tools/raidtest/internal/catalog"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
)

type Admin interface {
	EnsureAbsent(context.Context, string, string) error
	CreateWorkflow(context.Context, adminhttp.WorkflowUpsert) error
	GetWorkflow(context.Context, string) error
	DeleteWorkflow(context.Context, string) error
	CreateMemoryLayout(context.Context, adminhttp.MemoryLayoutUpsert) error
	GetMemoryLayout(context.Context, string) error
	DeleteMemoryLayout(context.Context, string) error
	CreateRuntimeProfile(context.Context, adminhttp.RuntimeProfileUpsert) error
	GetRuntimeProfile(context.Context, string) error
	DeleteRuntimeProfile(context.Context, string) error
	CreateRegistrationToken(context.Context, adminhttp.RegistrationTokenUpsert) error
	DeleteRegistrationToken(context.Context, string) error
	CreateWorkspace(context.Context, adminhttp.WorkspaceUpsert) error
	GetWorkspace(context.Context, string) error
	DeleteWorkspace(context.Context, string) error
	DeletePeer(context.Context, string) error
	GetReference(context.Context, string, string) error
}

type Resource struct{ Kind, ID string }

type Lifecycle struct {
	admin     Admin
	created   []Resource
	Ledger    []report.Lifecycle
	Keep      bool
	finalized bool
}

func New(admin Admin, keep bool) *Lifecycle { return &Lifecycle{admin: admin, Keep: keep} }

type Setup struct {
	Closure                                    catalog.Closure
	TokenID, Token, WorkspaceID, WorkspaceName string
}

func (l *Lifecycle) CreateClosure(ctx context.Context, setup Setup) error {
	if l == nil || l.admin == nil {
		return errors.New("Admin client is required")
	}
	w := setup.Closure.Workflow
	if err := l.create(ctx, "Workflow", setup.Closure.WorkflowID, func() error {
		return l.admin.CreateWorkflow(ctx, adminhttp.WorkflowUpsert{Id: setup.Closure.WorkflowID, Spec: w.Source.Spec})
	}, l.admin.GetWorkflow); err != nil {
		return err
	}
	for _, memory := range setup.Closure.MemoryLayouts {
		shadowID := setup.Closure.MemoryIDs[memory.Source.Metadata.ID]
		if err := l.create(ctx, "MemoryLayout", shadowID, func() error {
			return l.admin.CreateMemoryLayout(ctx, adminhttp.MemoryLayoutUpsert{Id: shadowID, Spec: memory.Source.Spec})
		}, l.admin.GetMemoryLayout); err != nil {
			return err
		}
	}
	if err := l.verifyProfileReferences(ctx, setup.Closure.Profile.Source.Spec); err != nil {
		return err
	}
	if err := l.create(ctx, "RuntimeProfile", setup.Closure.ProfileID, func() error {
		return l.admin.CreateRuntimeProfile(ctx, adminhttp.RuntimeProfileUpsert{Id: setup.Closure.ProfileID, Spec: setup.Closure.Profile.Source.Spec})
	}, l.admin.GetRuntimeProfile); err != nil {
		return err
	}
	if err := l.create(ctx, "RegistrationToken", setup.TokenID, func() error {
		return l.admin.CreateRegistrationToken(ctx, adminhttp.RegistrationTokenUpsert{Id: setup.TokenID, Token: setup.Token, RuntimeProfileId: setup.Closure.ProfileID})
	}, nil); err != nil {
		return err
	}
	return nil
}

func (l *Lifecycle) verifyProfileReferences(ctx context.Context, spec any) error {
	b, err := json.Marshal(spec)
	if err != nil {
		return err
	}
	var root map[string]any
	if err := json.Unmarshal(b, &root); err != nil {
		return err
	}
	refs := map[string]map[string]bool{}
	add := func(kind, id string) {
		if id == "" {
			return
		}
		if refs[kind] == nil {
			refs[kind] = map[string]bool{}
		}
		refs[kind][id] = true
	}
	workflows, _ := root["workflows"].(map[string]any)
	if system, ok := workflows["system"].(map[string]any); ok {
		for _, raw := range system {
			value, _ := raw.(string)
			add("Workflow", value)
		}
	}
	if collections, ok := workflows["collections"].(map[string]any); ok {
		for _, rawCollection := range collections {
			collection, _ := rawCollection.(map[string]any)
			for _, rawBinding := range collection {
				binding, _ := rawBinding.(map[string]any)
				value, _ := binding["resource_id"].(string)
				add("Workflow", value)
			}
		}
	}
	resources, _ := root["resources"].(map[string]any)
	for group, kind := range map[string]string{"models": "Model", "voices": "Voice", "pet_defs": "PetDef", "game_defs": "GameDef", "badge_defs": "BadgeDef"} {
		bindings, _ := resources[group].(map[string]any)
		for _, rawBinding := range bindings {
			binding, _ := rawBinding.(map[string]any)
			value, _ := binding["resource_id"].(string)
			add(kind, value)
		}
	}
	if memories, ok := resources["memories"].(map[string]any); ok {
		for _, rawBinding := range memories {
			binding, _ := rawBinding.(map[string]any)
			value, _ := binding["layout_id"].(string)
			add("MemoryLayout", value)
		}
	}
	kinds := make([]string, 0, len(refs))
	for kind := range refs {
		kinds = append(kinds, kind)
	}
	sort.Strings(kinds)
	for _, kind := range kinds {
		ids := make([]string, 0, len(refs[kind]))
		for id := range refs[kind] {
			ids = append(ids, id)
		}
		sort.Strings(ids)
		for _, id := range ids {
			if err := l.admin.GetReference(ctx, kind, id); err != nil {
				return fmt.Errorf("verify retained %s %s: %w", kind, id, err)
			}
		}
	}
	return nil
}

func (l *Lifecycle) RecordPeer(publicKey string) {
	l.created = append(l.created, Resource{Kind: "Peer", ID: publicKey})
	l.Ledger = append(l.Ledger, report.Lifecycle{ResourceType: "Peer", ID: publicKey, Action: "create", Status: "pass"})
}

func (l *Lifecycle) Record(entry report.Lifecycle) { l.Ledger = append(l.Ledger, entry) }

func (l *Lifecycle) CreateWorkspace(ctx context.Context, id, name, workflowID string) error {
	return l.create(ctx, "Workspace", id, func() error {
		return l.admin.CreateWorkspace(ctx, adminhttp.WorkspaceUpsert{Id: id, Name: name, WorkflowId: workflowID})
	}, l.admin.GetWorkspace)
}

func (l *Lifecycle) create(ctx context.Context, kind, id string, create func() error, readback func(context.Context, string) error) error {
	if err := l.admin.EnsureAbsent(ctx, kind, id); err != nil {
		l.Ledger = append(l.Ledger, report.Lifecycle{ResourceType: kind, ID: id, Action: "preflight", Status: "fail", Error: err.Error()})
		return fmt.Errorf("preflight %s %s: %w", kind, id, err)
	}
	if err := create(); err != nil {
		l.Ledger = append(l.Ledger, report.Lifecycle{ResourceType: kind, ID: id, Action: "create", Status: "fail", Error: err.Error()})
		return fmt.Errorf("create %s %s: %w", kind, id, err)
	}
	// Record immediately so later failures always roll this resource back.
	l.created = append(l.created, Resource{Kind: kind, ID: id})
	if readback != nil {
		if err := readback(ctx, id); err != nil {
			l.Ledger = append(l.Ledger, report.Lifecycle{ResourceType: kind, ID: id, Action: "readback", Status: "fail", Error: err.Error()})
			return fmt.Errorf("read back %s %s: %w", kind, id, err)
		}
	}
	l.Ledger = append(l.Ledger, report.Lifecycle{ResourceType: kind, ID: id, Action: "create", Status: "pass"})
	return nil
}

func (l *Lifecycle) Cleanup(ctx context.Context) error {
	if l == nil || l.finalized {
		return nil
	}
	if l.Keep {
		for i := len(l.created) - 1; i >= 0; i-- {
			resource := l.created[i]
			l.Ledger = append(l.Ledger, report.Lifecycle{ResourceType: resource.Kind, ID: resource.ID, Action: "retain", Status: "pass"})
		}
		l.finalized = true
		return nil
	}
	var failures []string
	var remaining []Resource
	for i := len(l.created) - 1; i >= 0; i-- {
		resource := l.created[i]
		var err error
		switch resource.Kind {
		case "Workspace":
			err = l.admin.DeleteWorkspace(ctx, resource.ID)
		case "Peer":
			err = l.admin.DeletePeer(ctx, resource.ID)
		case "RegistrationToken":
			err = l.admin.DeleteRegistrationToken(ctx, resource.ID)
		case "RuntimeProfile":
			err = l.admin.DeleteRuntimeProfile(ctx, resource.ID)
		case "MemoryLayout":
			err = l.admin.DeleteMemoryLayout(ctx, resource.ID)
		case "Workflow":
			err = l.admin.DeleteWorkflow(ctx, resource.ID)
		default:
			err = fmt.Errorf("unknown resource kind %q", resource.Kind)
		}
		entry := report.Lifecycle{ResourceType: resource.Kind, ID: resource.ID, Action: "delete", Status: "pass"}
		if err != nil {
			entry.Status, entry.Error = "fail", err.Error()
			failures = append(failures, fmt.Sprintf("%s %s: %v", resource.Kind, resource.ID, err))
			remaining = append(remaining, resource)
		}
		l.Ledger = append(l.Ledger, entry)
	}
	for left, right := 0, len(remaining)-1; left < right; left, right = left+1, right-1 {
		remaining[left], remaining[right] = remaining[right], remaining[left]
	}
	l.created = remaining
	l.finalized = len(remaining) == 0
	if len(failures) > 0 {
		return errors.New(strings.Join(failures, "; "))
	}
	return nil
}

type AdminClient struct {
	API *adminhttp.ClientWithResponses
}

func absentStatus(action string, status int, body []byte) error {
	if status == 404 {
		return nil
	}
	if status >= 200 && status < 300 {
		return fmt.Errorf("%s refused: resource already exists", action)
	}
	return statusError(action, status, body)
}

func (a AdminClient) EnsureAbsent(ctx context.Context, kind, id string) error {
	switch kind {
	case "Workflow":
		r, err := a.API.GetWorkflowWithResponse(ctx, id)
		if err != nil {
			return err
		}
		return absentStatus("check Workflow", r.StatusCode(), r.Body)
	case "MemoryLayout":
		r, err := a.API.GetMemoryLayoutWithResponse(ctx, id)
		if err != nil {
			return err
		}
		return absentStatus("check MemoryLayout", r.StatusCode(), r.Body)
	case "RuntimeProfile":
		r, err := a.API.GetRuntimeProfileWithResponse(ctx, id)
		if err != nil {
			return err
		}
		return absentStatus("check RuntimeProfile", r.StatusCode(), r.Body)
	case "RegistrationToken":
		r, err := a.API.GetRegistrationTokenWithResponse(ctx, id)
		if err != nil {
			return err
		}
		return absentStatus("check RegistrationToken", r.StatusCode(), r.Body)
	case "Workspace":
		r, err := a.API.GetWorkspaceWithResponse(ctx, id)
		if err != nil {
			return err
		}
		return absentStatus("check Workspace", r.StatusCode(), r.Body)
	default:
		return fmt.Errorf("unsupported run-owned resource kind %q", kind)
	}
}

func statusError(action string, status int, body []byte) error {
	if status >= 200 && status < 300 {
		return nil
	}
	detail := strings.TrimSpace(string(body))
	if len(detail) > 300 {
		detail = detail[:300]
	}
	return fmt.Errorf("%s returned HTTP %d: %s", action, status, detail)
}

func (a AdminClient) CreateWorkflow(ctx context.Context, v adminhttp.WorkflowUpsert) error {
	r, e := a.API.CreateWorkflowWithResponse(ctx, v)
	if e != nil {
		return e
	}
	return statusError("create Workflow", r.StatusCode(), r.Body)
}
func (a AdminClient) GetWorkflow(ctx context.Context, id string) error {
	r, e := a.API.GetWorkflowWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("get Workflow", r.StatusCode(), r.Body)
}
func (a AdminClient) DeleteWorkflow(ctx context.Context, id string) error {
	r, e := a.API.DeleteWorkflowWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("delete Workflow", r.StatusCode(), r.Body)
}
func (a AdminClient) CreateMemoryLayout(ctx context.Context, v adminhttp.MemoryLayoutUpsert) error {
	r, e := a.API.CreateMemoryLayoutWithResponse(ctx, v)
	if e != nil {
		return e
	}
	return statusError("create MemoryLayout", r.StatusCode(), r.Body)
}
func (a AdminClient) GetMemoryLayout(ctx context.Context, id string) error {
	r, e := a.API.GetMemoryLayoutWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("get MemoryLayout", r.StatusCode(), r.Body)
}
func (a AdminClient) DeleteMemoryLayout(ctx context.Context, id string) error {
	r, e := a.API.DeleteMemoryLayoutWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("delete MemoryLayout", r.StatusCode(), r.Body)
}
func (a AdminClient) CreateRuntimeProfile(ctx context.Context, v adminhttp.RuntimeProfileUpsert) error {
	r, e := a.API.CreateRuntimeProfileWithResponse(ctx, v)
	if e != nil {
		return e
	}
	return statusError("create RuntimeProfile", r.StatusCode(), r.Body)
}
func (a AdminClient) GetRuntimeProfile(ctx context.Context, id string) error {
	r, e := a.API.GetRuntimeProfileWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("get RuntimeProfile", r.StatusCode(), r.Body)
}
func (a AdminClient) DeleteRuntimeProfile(ctx context.Context, id string) error {
	r, e := a.API.DeleteRuntimeProfileWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("delete RuntimeProfile", r.StatusCode(), r.Body)
}
func (a AdminClient) CreateRegistrationToken(ctx context.Context, v adminhttp.RegistrationTokenUpsert) error {
	r, e := a.API.CreateRegistrationTokenWithResponse(ctx, v)
	if e != nil {
		return e
	}
	err := statusError("create RegistrationToken", r.StatusCode(), r.Body)
	if err == nil {
		return nil
	}
	return errors.New(strings.ReplaceAll(err.Error(), v.Token, "[REDACTED]"))
}
func (a AdminClient) DeleteRegistrationToken(ctx context.Context, id string) error {
	r, e := a.API.DeleteRegistrationTokenWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("delete RegistrationToken", r.StatusCode(), r.Body)
}
func (a AdminClient) CreateWorkspace(ctx context.Context, v adminhttp.WorkspaceUpsert) error {
	r, e := a.API.CreateWorkspaceWithResponse(ctx, v)
	if e != nil {
		return e
	}
	return statusError("create Workspace", r.StatusCode(), r.Body)
}
func (a AdminClient) GetWorkspace(ctx context.Context, id string) error {
	r, e := a.API.GetWorkspaceWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("get Workspace", r.StatusCode(), r.Body)
}
func (a AdminClient) DeleteWorkspace(ctx context.Context, id string) error {
	r, e := a.API.DeleteWorkspaceWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("delete Workspace", r.StatusCode(), r.Body)
}
func (a AdminClient) DeletePeer(ctx context.Context, id string) error {
	r, e := a.API.DeletePeerWithResponse(ctx, id)
	if e != nil {
		return e
	}
	return statusError("delete Peer", r.StatusCode(), r.Body)
}

func (a AdminClient) GetReference(ctx context.Context, kind, id string) error {
	switch kind {
	case "Workflow":
		return a.GetWorkflow(ctx, id)
	case "MemoryLayout":
		return a.GetMemoryLayout(ctx, id)
	case "Model":
		r, e := a.API.GetModelWithResponse(ctx, id)
		if e != nil {
			return e
		}
		return statusError("get Model", r.StatusCode(), r.Body)
	case "Voice":
		r, e := a.API.GetVoiceWithResponse(ctx, id)
		if e != nil {
			return e
		}
		return statusError("get Voice", r.StatusCode(), r.Body)
	case "PetDef":
		r, e := a.API.GetPetDefWithResponse(ctx, id)
		if e != nil {
			return e
		}
		return statusError("get PetDef", r.StatusCode(), r.Body)
	case "GameDef":
		r, e := a.API.GetGameDefWithResponse(ctx, id)
		if e != nil {
			return e
		}
		return statusError("get GameDef", r.StatusCode(), r.Body)
	case "BadgeDef":
		r, e := a.API.GetBadgeDefWithResponse(ctx, id)
		if e != nil {
			return e
		}
		return statusError("get BadgeDef", r.StatusCode(), r.Body)
	default:
		return fmt.Errorf("unsupported retained reference kind %q", kind)
	}
}

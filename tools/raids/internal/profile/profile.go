// Package profile installs raid packages into RuntimeProfile YAML documents.
//
// It edits the document at the yaml.v3 Node level so unrelated content,
// ordering, and flow styles survive. It never contacts a Server: Terraform or
// `gizclaw admin apply` still own deployment.
//
// A Workflow may be bound in several collections under different Peer-facing
// keys (for example `story.aesop` in `story` and `flowcraft-story-aesop` in
// `raidtest-targets`); bindings are therefore matched by `resource_id`, not by
// key.
package profile

import (
	"bytes"
	"fmt"
	"os"
	"sort"
	"strings"

	"gopkg.in/yaml.v3"

	"github.com/GizClaw/raids/tools/raids/internal/raid"
)

// Document is a RuntimeProfile loaded for editing.
type Document struct {
	Path string
	root *yaml.Node
	// explicitStart records whether the source began with `---` so the
	// rendered document keeps the same framing.
	explicitStart bool
}

// Load reads a RuntimeProfile YAML file.
func Load(path string) (*Document, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var root yaml.Node
	if err := yaml.Unmarshal(data, &root); err != nil {
		return nil, fmt.Errorf("decode %s: %w", path, err)
	}
	if root.Kind != yaml.DocumentNode || len(root.Content) != 1 || root.Content[0].Kind != yaml.MappingNode {
		return nil, fmt.Errorf("%s: expected one YAML mapping document", path)
	}
	if kind := scalarAt(root.Content[0], "kind"); kind != "RuntimeProfile" {
		return nil, fmt.Errorf("%s: kind must be RuntimeProfile, got %q", path, kind)
	}
	return &Document{Path: path, root: &root, explicitStart: bytes.HasPrefix(bytes.TrimLeft(data, "\n"), []byte("---"))}, nil
}

// Save writes the document back.
func (d *Document) Save() error {
	data, err := d.Bytes()
	if err != nil {
		return err
	}
	return os.WriteFile(d.Path, data, 0o644)
}

// Bytes renders the document without writing it.
func (d *Document) Bytes() ([]byte, error) {
	var buffer bytes.Buffer
	if d.explicitStart {
		buffer.WriteString("---\n")
	}
	encoder := yaml.NewEncoder(&buffer)
	encoder.SetIndent(2)
	if err := encoder.Encode(d.root); err != nil {
		return nil, err
	}
	if err := encoder.Close(); err != nil {
		return nil, err
	}
	return buffer.Bytes(), nil
}

// I18n is the per-language display text of one binding.
type I18n map[string]map[string]string // lang -> {display_name, description}

// Options describe one install or uninstall.
type Options struct {
	Implementation string
	Collection     string // install: target collection; uninstall: limit to this collection ("" = every collection)
	Name           string // binding key inside the collection (default: the Workflow id)
	Tester         bool
	TesterColl     string
	Models         map[string]string // alias -> Model resource id
	Voices         map[string]string // alias -> Voice resource id
	I18n           I18n              // overrides for the Workflow binding text
	TesterI18n     I18n              // overrides for the Tester binding text
}

// Install upserts one implementation (and optionally the tester) into the profile.
func (d *Document) Install(r *raid.Raid, catalog *raid.Catalog, opts Options) error {
	impl, ok := r.Implementations[opts.Implementation]
	if !ok {
		return fmt.Errorf("raid %s has no implementation %q (have %s)", r.ID, opts.Implementation, strings.Join(implementationNames(r), ", "))
	}
	if opts.Collection == "" {
		return fmt.Errorf("--collection is required")
	}
	if err := d.checkSlots(impl.Parameters, opts, catalog); err != nil {
		return err
	}
	if opts.Tester {
		if r.Tester == nil {
			return fmt.Errorf("raid %s declares no tester", r.ID)
		}
		if err := d.checkSlots(r.Tester.Parameters, opts, catalog); err != nil {
			return err
		}
	}
	if impl.Memory != nil {
		if !catalog.MemoryLayouts[impl.Memory.LayoutID] {
			return fmt.Errorf("MemoryLayout %q is not in memory-layouts/", impl.Memory.LayoutID)
		}
		if mapGet(d.path("spec", "resources", "memories"), impl.Memory.LayoutID) == nil {
			return fmt.Errorf("profile has no spec.resources.memories.%s binding; add the memory binding (driver/connection are deployment policy) before installing %s", impl.Memory.LayoutID, r.ID)
		}
	}
	key := opts.Name
	if key == "" {
		key = impl.WorkflowID
	}
	d.bindWorkflow(opts.Collection, key, impl.WorkflowID, implementationI18n(r, opts.Implementation), opts.I18n)
	d.bindAliases("models", impl.Parameters.Models, opts.Models)
	d.bindAliases("voices", impl.Parameters.Voices, opts.Voices)
	if opts.Tester {
		coll := opts.TesterColl
		if coll == "" {
			coll = "raidtest-testers"
		}
		d.bindWorkflow(coll, r.Tester.WorkflowID, r.Tester.WorkflowID, testerI18n(r), opts.TesterI18n)
		d.bindAliases("models", r.Tester.Parameters.Models, opts.Models)
	}
	return nil
}

// Uninstall removes one implementation's bindings (and its tester when requested).
// Alias slots are removed only when no binding of that Workflow remains, and
// the shared Tester only when no other implementation of the raid is bound.
func (d *Document) Uninstall(r *raid.Raid, opts Options) error {
	impl, ok := r.Implementations[opts.Implementation]
	if !ok {
		return fmt.Errorf("raid %s has no implementation %q", r.ID, opts.Implementation)
	}
	d.unbindWorkflow(impl.WorkflowID, opts.Collection)
	if len(d.bindingsOf(impl.WorkflowID)) == 0 {
		for alias := range impl.Parameters.Models {
			mapDelete(d.path("spec", "resources", "models"), alias)
		}
		for alias := range impl.Parameters.Voices {
			mapDelete(d.path("spec", "resources", "voices"), alias)
		}
	}
	if opts.Tester && r.Tester != nil {
		// The Tester is shared by every implementation of the raid: keep it
		// while any other implementation is still bound.
		for name, other := range r.Implementations {
			if name != opts.Implementation && len(d.bindingsOf(other.WorkflowID)) > 0 {
				return nil
			}
		}
		d.unbindWorkflow(r.Tester.WorkflowID, "")
		for alias := range r.Tester.Parameters.Models {
			mapDelete(d.path("spec", "resources", "models"), alias)
		}
	}
	return nil
}

// Binding is one collection entry that points at a Workflow.
type Binding struct {
	Collection string
	Key        string
	I18n       I18n
}

// Installed describes one raid implementation found in the profile.
type Installed struct {
	Raid           string
	Implementation string
	WorkflowID     string
	Bindings       []Binding
	TesterBindings []Binding
	Models         map[string]string // alias -> bound resource id (implementation + tester)
	Voices         map[string]string
	Missing        []string // slot aliases without a binding
	Unknown        []string // bound resource ids absent from the catalog
}

// Inspect lists every raid implementation bound in the profile.
func (d *Document) Inspect(root string, catalog *raid.Catalog) ([]Installed, error) {
	ids, err := raid.List(root)
	if err != nil {
		return nil, err
	}
	var result []Installed
	for _, id := range ids {
		r, err := raid.Load(root, id)
		if err != nil {
			return nil, err
		}
		for _, name := range implementationNames(r) {
			impl := r.Implementations[name]
			bindings := d.bindingsOf(impl.WorkflowID)
			if len(bindings) == 0 {
				continue
			}
			entry := Installed{Raid: id, Implementation: name, WorkflowID: impl.WorkflowID, Bindings: bindings, Models: map[string]string{}, Voices: map[string]string{}}
			if r.Tester != nil {
				entry.TesterBindings = d.bindingsOf(r.Tester.WorkflowID)
			}
			d.collectSlots(impl.Parameters, catalog, &entry)
			if len(entry.TesterBindings) > 0 {
				d.collectSlots(r.Tester.Parameters, catalog, &entry)
			}
			if impl.Memory != nil && mapGet(d.path("spec", "resources", "memories"), impl.Memory.LayoutID) == nil {
				entry.Missing = append(entry.Missing, "memory:"+impl.Memory.LayoutID)
			}
			sort.Strings(entry.Missing)
			sort.Strings(entry.Unknown)
			result = append(result, entry)
		}
	}
	return result, nil
}

func (d *Document) checkSlots(p raid.Parameters, opts Options, catalog *raid.Catalog) error {
	var missing []string
	check := func(section string, slots map[string]raid.Slot, values map[string]string, known map[string]bool) error {
		for alias := range slots {
			id := values[alias]
			if id == "" {
				if mapGet(d.path("spec", "resources", section), alias) != nil {
					continue // keep the existing binding
				}
				missing = append(missing, strings.TrimSuffix(section, "s")+"."+alias)
				continue
			}
			if !known[id] {
				return fmt.Errorf("%s %q for slot %s is not in %s/", strings.TrimSuffix(section, "s"), id, alias, section)
			}
		}
		return nil
	}
	if err := check("models", p.Models, opts.Models, catalog.Models); err != nil {
		return err
	}
	if err := check("voices", p.Voices, opts.Voices, catalog.Voices); err != nil {
		return err
	}
	if len(missing) > 0 {
		sort.Strings(missing)
		return fmt.Errorf("missing slot values: %s (pass --set <slot>=<resource id>)", strings.Join(missing, ", "))
	}
	return nil
}

func (d *Document) collectSlots(p raid.Parameters, catalog *raid.Catalog, entry *Installed) {
	for alias := range p.Models {
		node := mapGet(d.path("spec", "resources", "models"), alias)
		if node == nil {
			entry.Missing = append(entry.Missing, "model."+alias)
			continue
		}
		id := scalarAt(node, "resource_id")
		entry.Models[alias] = id
		if !catalog.Models[id] {
			entry.Unknown = append(entry.Unknown, "model."+alias+"="+id)
		}
	}
	for alias := range p.Voices {
		node := mapGet(d.path("spec", "resources", "voices"), alias)
		if node == nil {
			entry.Missing = append(entry.Missing, "voice."+alias)
			continue
		}
		id := scalarAt(node, "resource_id")
		entry.Voices[alias] = id
		if !catalog.Voices[id] {
			entry.Unknown = append(entry.Unknown, "voice."+alias+"="+id)
		}
	}
}

// implementationI18n is the default binding text for one implementation: the
// raid title, suffixed with the engine when the raid ships several engines so
// product collections can tell them apart (for example "伊索寓言（Eino）").
func implementationI18n(r *raid.Raid, implementation string) I18n {
	title := map[string]string{}
	for lang, v := range r.Title {
		title[lang] = v
	}
	if len(r.Implementations) > 1 && implementation != "flowcraft" {
		label := strings.ToUpper(implementation[:1]) + implementation[1:]
		for lang, v := range title {
			if lang == "zh-CN" {
				title[lang] = v + "（" + label + "）"
			} else {
				title[lang] = v + " (" + label + ")"
			}
		}
	}
	return defaultI18n(title, r.Summary)
}

// testerI18n is the default binding text for the raid's Tester.
func testerI18n(r *raid.Raid) I18n {
	title := map[string]string{}
	for lang, v := range r.Title {
		if lang == "zh-CN" {
			title[lang] = v + " 验收"
		} else {
			title[lang] = v + " tester"
		}
	}
	return defaultI18n(title, nil)
}

func defaultI18n(title, summary map[string]string) I18n {
	out := I18n{}
	for _, lang := range []string{"en", "zh-CN"} {
		entry := map[string]string{}
		if title[lang] != "" {
			entry["display_name"] = title[lang]
		}
		if summary != nil && summary[lang] != "" {
			entry["description"] = summary[lang]
		}
		if len(entry) > 0 {
			out[lang] = entry
		}
	}
	return out
}

// bindWorkflow upserts collections[collection][key]. A new binding receives the
// default text (or the overrides); an existing binding keeps its text unless
// overrides are given.
func (d *Document) bindWorkflow(collection, key, workflowID string, defaults, overrides I18n) {
	coll := ensureMapping(d.ensurePath("spec", "workflows", "collections"), collection)
	existing := mapGet(coll, key) != nil
	binding := ensureMapping(coll, key)
	setScalar(binding, "resource_id", workflowID)
	text := overrides
	if !existing && len(text) == 0 {
		text = defaults
	}
	if len(text) == 0 {
		return
	}
	fresh := mapGet(binding, "i18n") == nil
	i18n := ensureMapping(binding, "i18n")
	for _, lang := range sortedKeys(text) {
		entry := ensureMapping(i18n, lang)
		for _, field := range []string{"display_name", "description"} {
			if value := text[lang][field]; value != "" {
				setScalar(entry, field, value)
			}
		}
		if mapGet(entry, "display_name") == nil {
			setScalar(entry, "display_name", workflowID)
		}
	}
	if fresh {
		compact(i18n)
	}
}

func (d *Document) unbindWorkflow(workflowID, collection string) {
	collections := d.path("spec", "workflows", "collections")
	if collections == nil {
		return
	}
	for i := 0; i+1 < len(collections.Content); i += 2 {
		if collection != "" && collections.Content[i].Value != collection {
			continue
		}
		coll := collections.Content[i+1]
		for j := 0; j+1 < len(coll.Content); {
			if scalarAt(coll.Content[j+1], "resource_id") == workflowID {
				coll.Content = append(coll.Content[:j], coll.Content[j+2:]...)
				continue
			}
			j += 2
		}
	}
}

func (d *Document) bindAliases(section string, slots map[string]raid.Slot, values map[string]string) {
	for _, alias := range sortedSlotKeys(slots) {
		id := values[alias]
		if id == "" {
			continue
		}
		parent := d.ensurePath("spec", "resources", section)
		existing := mapGet(parent, alias) != nil
		entry := ensureMapping(parent, alias)
		setScalar(entry, "resource_id", id)
		if existing {
			continue
		}
		label := slots[alias].Role
		if label == "" {
			label = alias
		}
		i18n := ensureMapping(entry, "i18n")
		setScalar(ensureMapping(i18n, "en"), "display_name", strings.ToUpper(label[:1])+label[1:])
		setScalar(ensureMapping(i18n, "zh-CN"), "display_name", label)
		compact(i18n)
	}
}

// bindingsOf returns every collection entry whose resource_id is workflowID.
func (d *Document) bindingsOf(workflowID string) []Binding {
	collections := d.path("spec", "workflows", "collections")
	if collections == nil {
		return nil
	}
	var result []Binding
	for i := 0; i+1 < len(collections.Content); i += 2 {
		coll := collections.Content[i+1]
		for j := 0; j+1 < len(coll.Content); j += 2 {
			if scalarAt(coll.Content[j+1], "resource_id") != workflowID {
				continue
			}
			binding := Binding{Collection: collections.Content[i].Value, Key: coll.Content[j].Value, I18n: I18n{}}
			if i18n := mapGet(coll.Content[j+1], "i18n"); i18n != nil {
				for k := 0; k+1 < len(i18n.Content); k += 2 {
					lang := i18n.Content[k].Value
					binding.I18n[lang] = map[string]string{}
					for _, field := range []string{"display_name", "description"} {
						if value := scalarAt(i18n.Content[k+1], field); value != "" {
							binding.I18n[lang][field] = value
						}
					}
				}
			}
			result = append(result, binding)
		}
	}
	return result
}

// ---- yaml.Node helpers ----

func (d *Document) path(keys ...string) *yaml.Node {
	node := d.root.Content[0]
	for _, key := range keys {
		node = mapGet(node, key)
		if node == nil {
			return nil
		}
	}
	return node
}

func (d *Document) ensurePath(keys ...string) *yaml.Node {
	node := d.root.Content[0]
	for _, key := range keys {
		node = ensureMapping(node, key)
	}
	return node
}

func mapGet(mapping *yaml.Node, key string) *yaml.Node {
	if mapping == nil || mapping.Kind != yaml.MappingNode {
		return nil
	}
	for i := 0; i+1 < len(mapping.Content); i += 2 {
		if mapping.Content[i].Value == key {
			return mapping.Content[i+1]
		}
	}
	return nil
}

func mapDelete(mapping *yaml.Node, key string) bool {
	if mapping == nil || mapping.Kind != yaml.MappingNode {
		return false
	}
	for i := 0; i+1 < len(mapping.Content); i += 2 {
		if mapping.Content[i].Value == key {
			mapping.Content = append(mapping.Content[:i], mapping.Content[i+2:]...)
			return true
		}
	}
	return false
}

func ensureMapping(parent *yaml.Node, key string) *yaml.Node {
	if existing := mapGet(parent, key); existing != nil {
		if existing.Kind == yaml.MappingNode {
			return existing
		}
		// Replace a null placeholder with a block mapping.
		existing.Kind = yaml.MappingNode
		existing.Tag = "!!map"
		existing.Value = ""
		existing.Content = nil
		existing.Style = 0
		return existing
	}
	keyNode := &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: key}
	valueNode := &yaml.Node{Kind: yaml.MappingNode, Tag: "!!map"}
	// A mapping that receives a nested mapping must render in block style;
	// otherwise an emptied `{}` collection would grow into one endless line.
	parent.Style = 0
	parent.Content = append(parent.Content, keyNode, valueNode)
	return valueNode
}

// compact renders a freshly created mapping (and its children) in flow style,
// matching the `i18n: {en: {display_name: …}, zh-CN: {…}}` convention of the
// committed profiles.
func compact(node *yaml.Node) {
	node.Style = yaml.FlowStyle
	for i := 1; i < len(node.Content); i += 2 {
		if node.Content[i].Kind == yaml.MappingNode {
			node.Content[i].Style = yaml.FlowStyle
		}
	}
}

func setScalar(mapping *yaml.Node, key, value string) {
	if existing := mapGet(mapping, key); existing != nil {
		existing.Kind = yaml.ScalarNode
		existing.Tag = "!!str"
		existing.Value = value
		existing.Content = nil
		return
	}
	mapping.Content = append(mapping.Content,
		&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: key},
		&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: value},
	)
}

func scalarAt(mapping *yaml.Node, key string) string {
	node := mapGet(mapping, key)
	if node == nil || node.Kind != yaml.ScalarNode {
		return ""
	}
	return node.Value
}

func implementationNames(r *raid.Raid) []string {
	names := make([]string, 0, len(r.Implementations))
	for name := range r.Implementations {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func sortedKeys(m I18n) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

func sortedSlotKeys(m map[string]raid.Slot) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

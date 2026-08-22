// Command raids manages raid packages: the per-scenario directories under
// workflows/<raid>/ described by raid.json. It installs, removes, lists, and
// checks raid implementations inside RuntimeProfile YAML files without
// contacting any Server.
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/GizClaw/raids/tools/raids/internal/profile"
	"github.com/GizClaw/raids/tools/raids/internal/raid"
)

const usage = `raids — Raids package manager (edits RuntimeProfile YAML only)

Usage:
  raids install <raid> --impl <name> --profile <file> --collection <name> [--name <binding key>]
                [--tester] [--tester-collection <name>]
                [--set model.<alias>=<model id>] [--set voice.<alias>=<voice id>]
                [--display-name <lang>=<text>] [--description <lang>=<text>]
  raids uninstall <raid> --impl <name> --profile <file> [--collection <name>] [--tester]
  raids list --profile <file>
  raids check --profile <file> [--profile <file>...]
  raids validate [<raid>...]            validate raid.json manifests (all when none given)
  raids generate --plan <file> [--check] regenerate the plan's output profile from its base (--check only diffs)

Every command resolves the repository root from the working directory or --root.
`

type multiFlag []string

func (m *multiFlag) String() string     { return strings.Join(*m, ",") }
func (m *multiFlag) Set(v string) error { *m = append(*m, v); return nil }

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "raids:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		fmt.Print(usage)
		return nil
	}
	command, rest := args[0], args[1:]
	switch command {
	case "install", "uninstall":
		return runInstall(command, rest)
	case "list", "check":
		return runInspect(command, rest)
	case "validate":
		return runValidate(rest)
	case "generate":
		return runGenerate(rest)
	default:
		fmt.Print(usage)
		return fmt.Errorf("unknown command %q", command)
	}
}

// splitLeadingArg lets the positional raid id precede the flags.
func splitLeadingArg(args []string) (string, []string) {
	if len(args) > 0 && !strings.HasPrefix(args[0], "-") {
		return args[0], args[1:]
	}
	return "", args
}

func resolveRoot(root string) (string, error) {
	if root == "" {
		root = "."
	}
	return raid.FindRoot(root)
}

func parseSets(sets []string) (models, voices map[string]string, err error) {
	models, voices = map[string]string{}, map[string]string{}
	for _, item := range sets {
		key, value, ok := strings.Cut(item, "=")
		if !ok || value == "" {
			return nil, nil, fmt.Errorf("--set expects <slot>=<resource id>, got %q", item)
		}
		switch {
		case strings.HasPrefix(key, "model."):
			models[strings.TrimPrefix(key, "model.")] = value
		case strings.HasPrefix(key, "voice."):
			voices[strings.TrimPrefix(key, "voice.")] = value
		default:
			return nil, nil, fmt.Errorf("--set slot %q must start with model. or voice.", key)
		}
	}
	return models, voices, nil
}

func runInstall(command string, args []string) error {
	fs := flag.NewFlagSet(command, flag.ContinueOnError)
	root := fs.String("root", "", "repository root (default: discovered)")
	impl := fs.String("impl", "", "implementation name, for example flowcraft or eino")
	profilePath := fs.String("profile", "", "RuntimeProfile YAML file to edit")
	collection := fs.String("collection", "", "collection that receives the Workflow binding")
	tester := fs.Bool("tester", false, "also install/uninstall the raid's Tester Workflow")
	testerColl := fs.String("tester-collection", "raidtest-testers", "collection for the Tester binding")
	dryRun := fs.Bool("dry-run", false, "print the resulting profile instead of writing it")
	name := fs.String("name", "", "binding key inside the collection (default: the Workflow id)")
	var sets, names, descriptions multiFlag
	fs.Var(&sets, "set", "slot value: model.<alias>=<id> or voice.<alias>=<id> (repeatable)")
	fs.Var(&names, "display-name", "display name override: <lang>=<text> (repeatable)")
	fs.Var(&descriptions, "description", "description override: <lang>=<text> (repeatable)")
	raidID, args := splitLeadingArg(args)
	if err := fs.Parse(args); err != nil {
		return err
	}
	if raidID == "" && fs.NArg() == 1 {
		raidID = fs.Arg(0)
	} else if fs.NArg() != 0 {
		return fmt.Errorf("%s expects exactly one raid id", command)
	}
	if raidID == "" {
		return fmt.Errorf("%s expects exactly one raid id", command)
	}
	if *impl == "" || *profilePath == "" {
		return fmt.Errorf("--impl and --profile are required")
	}
	repo, err := resolveRoot(*root)
	if err != nil {
		return err
	}
	r, err := raid.Load(repo, raidID)
	if err != nil {
		return err
	}
	doc, err := profile.Load(*profilePath)
	if err != nil {
		return err
	}
	models, voices, err := parseSets(sets)
	if err != nil {
		return err
	}
	i18n := profile.I18n{}
	for field, items := range map[string]multiFlag{"display_name": names, "description": descriptions} {
		for _, item := range items {
			lang, text, ok := strings.Cut(item, "=")
			if !ok {
				return fmt.Errorf("--%s expects <lang>=<text>, got %q", strings.ReplaceAll(field, "_", "-"), item)
			}
			if i18n[lang] == nil {
				i18n[lang] = map[string]string{}
			}
			i18n[lang][field] = text
		}
	}
	opts := profile.Options{Implementation: *impl, Collection: *collection, Name: *name, Tester: *tester, TesterColl: *testerColl, Models: models, Voices: voices, I18n: i18n}
	if command == "install" {
		catalog, err := raid.LoadCatalog(repo)
		if err != nil {
			return err
		}
		if err := doc.Install(r, catalog, opts); err != nil {
			return err
		}
	} else if err := doc.Uninstall(r, opts); err != nil {
		return err
	}
	if *dryRun {
		data, err := doc.Bytes()
		if err != nil {
			return err
		}
		_, err = os.Stdout.Write(data)
		return err
	}
	if err := doc.Save(); err != nil {
		return err
	}
	fmt.Printf("%sed %s/%s in %s\n", command, r.ID, *impl, *profilePath)
	return nil
}

func runInspect(command string, args []string) error {
	fs := flag.NewFlagSet(command, flag.ContinueOnError)
	root := fs.String("root", "", "repository root (default: discovered)")
	var profiles multiFlag
	fs.Var(&profiles, "profile", "RuntimeProfile YAML file (repeatable)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if len(profiles) == 0 {
		return fmt.Errorf("--profile is required")
	}
	repo, err := resolveRoot(*root)
	if err != nil {
		return err
	}
	catalog, err := raid.LoadCatalog(repo)
	if err != nil {
		return err
	}
	failed := false
	for _, path := range profiles {
		doc, err := profile.Load(path)
		if err != nil {
			return err
		}
		installed, err := doc.Inspect(repo, catalog)
		if err != nil {
			return err
		}
		fmt.Printf("%s: %d raid implementations\n", path, len(installed))
		for _, entry := range installed {
			status := "ok"
			if len(entry.Missing) > 0 || len(entry.Unknown) > 0 {
				status = "INCOMPLETE"
				failed = true
			}
			var places []string
			for _, b := range entry.Bindings {
				places = append(places, b.Collection+"/"+b.Key)
			}
			line := fmt.Sprintf("  %-10s %s/%s (%s) in %s", status, entry.Raid, entry.Implementation, entry.WorkflowID, strings.Join(places, ", "))
			if len(entry.TesterBindings) > 0 {
				line += " +tester"
			}
			fmt.Println(line)
			for _, m := range entry.Missing {
				fmt.Printf("             missing %s\n", m)
			}
			for _, u := range entry.Unknown {
				fmt.Printf("             unknown resource %s\n", u)
			}
		}
	}
	if command == "check" && failed {
		return fmt.Errorf("profile check failed")
	}
	return nil
}

func runValidate(args []string) error {
	fs := flag.NewFlagSet("validate", flag.ContinueOnError)
	root := fs.String("root", "", "repository root (default: discovered)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	repo, err := resolveRoot(*root)
	if err != nil {
		return err
	}
	ids := fs.Args()
	if len(ids) == 0 {
		ids, err = raid.List(repo)
		if err != nil {
			return err
		}
	}
	for _, id := range ids {
		if _, err := raid.Load(repo, id); err != nil {
			return err
		}
	}
	fmt.Printf("validated %d raid manifests\n", len(ids))
	return nil
}

func runGenerate(args []string) error {
	fs := flag.NewFlagSet("generate", flag.ContinueOnError)
	root := fs.String("root", "", "repository root (default: discovered)")
	check := fs.Bool("check", false, "compare with the existing output instead of writing it")
	var plans multiFlag
	fs.Var(&plans, "plan", "plan file (repeatable)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if len(plans) == 0 {
		return fmt.Errorf("--plan is required")
	}
	repo, err := resolveRoot(*root)
	if err != nil {
		return err
	}
	catalog, err := raid.LoadCatalog(repo)
	if err != nil {
		return err
	}
	failed := false
	for _, planPath := range plans {
		plan, err := profile.LoadPlan(planPath)
		if err != nil {
			return err
		}
		data, err := profile.Generate(repo, planPath, plan, catalog)
		if err != nil {
			return err
		}
		output := planPath[:len(planPath)-len(filepath.Base(planPath))] + plan.Output
		if *check {
			existing, err := os.ReadFile(output)
			if err != nil {
				return err
			}
			if string(existing) != string(data) {
				fmt.Printf("%s: OUT OF DATE (run raids generate --plan %s)\n", output, planPath)
				failed = true
				continue
			}
			fmt.Printf("%s: up to date\n", output)
			continue
		}
		if err := os.WriteFile(output, data, 0o644); err != nil {
			return err
		}
		fmt.Printf("generated %s from %s (%d installs)\n", output, planPath, len(plan.Installs))
	}
	if failed {
		return fmt.Errorf("generated profiles differ from the committed files")
	}
	return nil
}

package profile

import (
	"fmt"
	"reflect"
	"sort"
	"testing"

	"gopkg.in/yaml.v3"
)

func sameYAML(t *testing.T, a, b []byte) bool {
	t.Helper()
	var left, right any
	if err := yaml.Unmarshal(a, &left); err != nil {
		t.Fatal(err)
	}
	if err := yaml.Unmarshal(b, &right); err != nil {
		t.Fatal(err)
	}
	if reflect.DeepEqual(left, right) {
		return true
	}
	diffs := []string{}
	describeDiff("$", left, right, &diffs)
	sort.Strings(diffs)
	for i, d := range diffs {
		if i >= 20 {
			t.Logf("... %d more differences", len(diffs)-20)
			break
		}
		t.Log(d)
	}
	return false
}

func describeDiff(path string, a, b any, out *[]string) {
	am, aok := a.(map[string]any)
	bm, bok := b.(map[string]any)
	if aok && bok {
		keys := map[string]bool{}
		for k := range am {
			keys[k] = true
		}
		for k := range bm {
			keys[k] = true
		}
		for k := range keys {
			av, aexists := am[k]
			bv, bexists := bm[k]
			switch {
			case !aexists:
				*out = append(*out, fmt.Sprintf("%s.%s: added %v", path, k, short(bv)))
			case !bexists:
				*out = append(*out, fmt.Sprintf("%s.%s: removed %v", path, k, short(av)))
			default:
				describeDiff(path+"."+k, av, bv, out)
			}
		}
		return
	}
	if !reflect.DeepEqual(a, b) {
		*out = append(*out, fmt.Sprintf("%s: %v != %v", path, short(a), short(b)))
	}
}

func short(v any) string {
	s := fmt.Sprintf("%v", v)
	if len(s) > 80 {
		return s[:80] + "…"
	}
	return s
}

// stripAliasText removes the cosmetic display text of model/voice aliases so
// structural comparisons focus on bindings and resource ids.
func stripAliasText(data []byte) []byte {
	var doc map[string]any
	if err := yaml.Unmarshal(data, &doc); err != nil {
		return data
	}
	spec, _ := doc["spec"].(map[string]any)
	resources, _ := spec["resources"].(map[string]any)
	for _, section := range []string{"models", "voices"} {
		entries, _ := resources[section].(map[string]any)
		for _, entry := range entries {
			if m, ok := entry.(map[string]any); ok {
				delete(m, "i18n")
			}
		}
	}
	out, err := yaml.Marshal(doc)
	if err != nil {
		return data
	}
	return out
}

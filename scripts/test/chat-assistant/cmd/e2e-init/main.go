// Initialize disposable Docker identities and a CLI context, never provider keys.
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
)

func main() {
	if len(os.Args) != 3 {
		panic("usage: e2e-init STATE TEMPLATE_DIRECTORY")
	}
	state, templates := os.Args[1], os.Args[2]
	values := map[string]string{}
	for _, role := range []string{"SERVER", "EDGE", "ADMIN"} {
		key, err := giznet.GenerateKeyPair()
		if err != nil {
			panic(err)
		}
		values["E2E_"+role+"_PRIVATE_KEY"] = key.Private.String()
		values["E2E_"+role+"_PUBLIC_KEY"] = key.Public.String()
	}
	for _, role := range []string{"server", "edge"} {
		data, err := os.ReadFile(filepath.Join(templates, role+".yaml"))
		if err != nil {
			panic(err)
		}
		config := os.Expand(string(data), func(key string) string {
			value, ok := values[key]
			if !ok {
				panic("unknown fixture variable " + key)
			}
			return value
		})
		write(filepath.Join(state, role, "config.yaml"), config)
	}
	config := fmt.Sprintf("identity:\n  private-key: %s\nserver:\n  endpoint: http://server:9820\n", values["E2E_ADMIN_PRIVATE_KEY"])
	write(filepath.Join(state, "cli", "gizclaw", "raids-e2e", "config.yaml"), config)
	write(filepath.Join(state, "public-keys.txt"), strings.Join([]string{values["E2E_SERVER_PUBLIC_KEY"], values["E2E_EDGE_PUBLIC_KEY"]}, "\n")+"\n")
}

func write(path, value string) {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		panic(err)
	}
	if err := os.WriteFile(path, []byte(value), 0600); err != nil {
		panic(err)
	}
}

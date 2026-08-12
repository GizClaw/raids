package config

import (
	"errors"
	"fmt"
	"io"
	"net"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

type SecretSource struct {
	Env   string
	File  string
	Stdin bool
}

func (s SecretSource) Validate(required bool) error {
	configured := 0
	if strings.TrimSpace(s.Env) != "" {
		configured++
	}
	if strings.TrimSpace(s.File) != "" {
		configured++
	}
	if s.Stdin {
		configured++
	}
	if !required && configured == 0 {
		return nil
	}
	if configured != 1 {
		return errors.New("exactly one secret source is required")
	}
	return nil
}

func (s SecretSource) Read(stdin io.Reader) ([]byte, error) {
	if err := s.Validate(true); err != nil {
		return nil, err
	}
	var value []byte
	var err error
	switch {
	case s.Env != "":
		value = []byte(os.Getenv(s.Env))
		if len(value) == 0 {
			return nil, fmt.Errorf("secret environment variable %q is empty", s.Env)
		}
	case s.File != "":
		value, err = os.ReadFile(s.File)
	case s.Stdin:
		value, err = io.ReadAll(stdin)
	}
	if err != nil {
		return nil, fmt.Errorf("read secret source: %w", err)
	}
	value = []byte(strings.TrimSpace(string(value)))
	if len(value) == 0 {
		return nil, errors.New("secret source is empty")
	}
	return value, nil
}

type Config struct {
	Server             string
	Workflow           string
	RuntimeProfile     string
	RuntimeProfileFile string
	MemoryLayouts      []string
	Plan               string
	Report             string
	OpenAIBaseURL      string
	AgentModel         string
	JudgeModel         string
	AdminKey           SecretSource
	OpenAIKey          SecretSource
	Keep               bool
	Timeout            time.Duration
}

func (c *Config) Validate() error {
	c.Server = strings.TrimSpace(c.Server)
	if c.Server == "" || strings.Contains(c.Server, "://") {
		return errors.New("server must be host:port without a URL scheme")
	}
	host, port, err := net.SplitHostPort(c.Server)
	if err != nil || strings.TrimSpace(host) == "" {
		return errors.New("server must be host:port without a URL scheme")
	}
	portNumber, err := strconv.Atoi(port)
	if err != nil || portNumber < 1 || portNumber > 65535 {
		return errors.New("server port must be between 1 and 65535")
	}
	if strings.TrimSpace(c.Workflow) == "" {
		return errors.New("workflow is required")
	}
	if strings.TrimSpace(c.Plan) == "" {
		return errors.New("plan is required")
	}
	if c.RuntimeProfile == "" {
		c.RuntimeProfile = "default"
	}
	if c.Report == "" {
		c.Report = "raidtest-report.json"
	}
	if c.Timeout <= 0 {
		c.Timeout = 2 * time.Minute
	}
	if c.OpenAIBaseURL == "" {
		c.OpenAIBaseURL = "http://" + c.Server + "/openai/v1"
	}
	parsed, err := url.Parse(c.OpenAIBaseURL)
	if err != nil || parsed.Host == "" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		return errors.New("openai base URL must be an absolute http(s) URL")
	}
	if err := c.AdminKey.Validate(true); err != nil {
		return fmt.Errorf("admin private key: %w", err)
	}
	if err := c.OpenAIKey.Validate(c.AgentModel != "" || c.JudgeModel != ""); err != nil {
		return fmt.Errorf("OpenAI API key: %w", err)
	}
	return nil
}

func (c Config) Redacted() map[string]any {
	return map[string]any{
		"server": c.Server, "workflow": c.Workflow, "runtime_profile": c.RuntimeProfile,
		"runtime_profile_file": c.RuntimeProfileFile, "memory_layouts": c.MemoryLayouts,
		"plan": c.Plan, "report": c.Report, "openai_base_url": c.OpenAIBaseURL,
		"agent_model": c.AgentModel, "judge_model": c.JudgeModel, "keep": c.Keep,
	}
}

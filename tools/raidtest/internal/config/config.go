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

func (s SecretSource) Configured() bool {
	return strings.TrimSpace(s.Env) != "" || strings.TrimSpace(s.File) != "" || s.Stdin
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
	PeerServer         string
	Workflow           string
	RuntimeProfile     string
	RuntimeProfileFile string
	MemoryLayouts      []string
	Plan               string
	Report             string
	OpenAIBaseURL      string
	AgentModel         string
	JudgeModel         string
	InputTTSModel      string
	InputTTSVoice      string
	AdminKey           SecretSource
	OpenAIKey          SecretSource
	Keep               bool
	Timeout            time.Duration
}

func (c *Config) Validate() error {
	c.Server = strings.TrimSpace(c.Server)
	if err := validateServer("server", c.Server); err != nil {
		return err
	}
	c.PeerServer = strings.TrimSpace(c.PeerServer)
	if c.PeerServer == "" {
		c.PeerServer = c.Server
	}
	if err := validateServer("peer server", c.PeerServer); err != nil {
		return err
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
	if c.InputTTSModel != "" && strings.TrimSpace(c.InputTTSVoice) == "" {
		c.InputTTSVoice = "alloy"
	}
	parsed, err := url.Parse(c.OpenAIBaseURL)
	if err != nil || parsed.Host == "" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		return errors.New("openai base URL must be an absolute http(s) URL")
	}
	if err := c.AdminKey.Validate(true); err != nil {
		return fmt.Errorf("admin private key: %w", err)
	}
	if err := c.OpenAIKey.Validate(false); err != nil {
		return fmt.Errorf("OpenAI API key: %w", err)
	}
	needsOpenAI := c.AgentModel != "" || c.JudgeModel != "" || c.InputTTSModel != ""
	defaultOpenAIBaseURL := "http://" + c.Server + "/openai/v1"
	if needsOpenAI && !c.OpenAIKey.Configured() && c.OpenAIBaseURL != defaultOpenAIBaseURL {
		return errors.New("OpenAI API key is required for a custom OpenAI base URL")
	}
	return nil
}

func validateServer(name, endpoint string) error {
	if endpoint == "" || strings.Contains(endpoint, "://") {
		return fmt.Errorf("%s must be host:port without a URL scheme", name)
	}
	host, port, err := net.SplitHostPort(endpoint)
	if err != nil || strings.TrimSpace(host) == "" {
		return fmt.Errorf("%s must be host:port without a URL scheme", name)
	}
	portNumber, err := strconv.Atoi(port)
	if err != nil || portNumber < 1 || portNumber > 65535 {
		return fmt.Errorf("%s port must be between 1 and 65535", name)
	}
	return nil
}

func (c Config) Redacted() map[string]any {
	return map[string]any{
		"server": c.Server, "peer_server": c.PeerServer, "workflow": c.Workflow, "runtime_profile": c.RuntimeProfile,
		"runtime_profile_file": c.RuntimeProfileFile, "memory_layouts": c.MemoryLayouts,
		"plan": c.Plan, "report": c.Report, "openai_base_url": c.OpenAIBaseURL,
		"agent_model": c.AgentModel, "judge_model": c.JudgeModel,
		"input_tts_model": c.InputTTSModel, "input_tts_voice": c.InputTTSVoice, "keep": c.Keep,
	}
}

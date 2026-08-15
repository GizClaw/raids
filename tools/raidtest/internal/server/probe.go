package server

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"strings"
	"syscall"
	"time"
)

const maxProbeBody = 64 << 10

type ProbeSample struct {
	State      string
	ObservedAt time.Time
	HTTPStatus int
	ErrorClass string
}

func (s ProbeSample) Healthy() bool { return s.State == "healthy" }

func ProbeServerInfo(ctx context.Context, endpoint string, client *http.Client) ProbeSample {
	sample := ProbeSample{ObservedAt: time.Now().UTC()}
	if client == nil {
		client = http.DefaultClient
	}
	probeClient := *client
	probeClient.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, "http://"+endpoint+"/server-info", nil)
	if err != nil {
		sample.State, sample.ErrorClass = "transport_error", "other"
		return sample
	}
	resp, err := probeClient.Do(req)
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) || errors.Is(ctx.Err(), context.DeadlineExceeded) {
			sample.State = "timeout"
			return sample
		}
		if errors.Is(err, context.Canceled) || errors.Is(ctx.Err(), context.Canceled) {
			sample.State = "canceled"
			return sample
		}
		sample.State, sample.ErrorClass = "transport_error", classifyProbeError(err)
		return sample
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxProbeBody))
	sample.HTTPStatus = resp.StatusCode
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		sample.State = "healthy"
	} else {
		sample.State = "http_error"
	}
	return sample
}

func SampleServerInfo(ctx context.Context, endpoint string, interval time.Duration, client *http.Client) <-chan ProbeSample {
	samples := make(chan ProbeSample)
	go func() {
		defer close(samples)
		for {
			started := time.Now()
			timeout := interval / 2
			if timeout > 2*time.Second {
				timeout = 2 * time.Second
			}
			probeCtx, cancel := context.WithTimeout(ctx, timeout)
			sample := ProbeServerInfo(probeCtx, endpoint, client)
			cancel()
			if sample.State == "canceled" && ctx.Err() != nil {
				return
			}
			select {
			case samples <- sample:
			case <-ctx.Done():
				return
			}
			delay := interval - time.Since(started)
			if delay < 0 {
				delay = 0
			}
			timer := time.NewTimer(delay)
			select {
			case <-timer.C:
			case <-ctx.Done():
				if !timer.Stop() {
					select {
					case <-timer.C:
					default:
					}
				}
				return
			}
		}
	}()
	return samples
}

func classifyProbeError(err error) string {
	var dns *net.DNSError
	if errors.As(err, &dns) {
		return "dns"
	}
	switch {
	case errors.Is(err, syscall.ECONNREFUSED):
		return "connection_refused"
	case errors.Is(err, syscall.ECONNRESET):
		return "connection_reset"
	case errors.Is(err, syscall.ENETUNREACH), errors.Is(err, syscall.EHOSTUNREACH):
		return "network_unreachable"
	case errors.Is(err, io.EOF), strings.Contains(strings.ToLower(err.Error()), "unexpected eof"):
		return "eof"
	default:
		return "other"
	}
}

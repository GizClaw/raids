package server

import (
	"context"
	"errors"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestProbeServerInfoClassifiesHTTPAndBoundsBody(t *testing.T) {
	for _, status := range []int{http.StatusOK, http.StatusBadGateway} {
		t.Run(http.StatusText(status), func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
				w.WriteHeader(status)
				_, _ = w.Write([]byte(strings.Repeat("x", maxProbeBody*2)))
			}))
			defer server.Close()
			sample := ProbeServerInfo(context.Background(), strings.TrimPrefix(server.URL, "http://"), server.Client())
			want := "healthy"
			if status != http.StatusOK {
				want = "http_error"
			}
			if sample.State != want || sample.HTTPStatus != status {
				t.Fatalf("sample=%#v", sample)
			}
		})
	}
}

func TestProbeServerInfoDoesNotFollowRedirects(t *testing.T) {
	var reached atomic.Bool
	target := httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) { reached.Store(true) }))
	defer target.Close()
	redirect := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, request *http.Request) {
		http.Redirect(w, request, target.URL, http.StatusFound)
	}))
	defer redirect.Close()
	sample := ProbeServerInfo(context.Background(), strings.TrimPrefix(redirect.URL, "http://"), redirect.Client())
	if reached.Load() || sample.State != "http_error" || sample.HTTPStatus != http.StatusFound {
		t.Fatalf("reached=%t sample=%#v", reached.Load(), sample)
	}
}

func TestProbeServerInfoClassifiesTimeoutAndSanitizesTransport(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond)
	defer cancel()
	client := &http.Client{Transport: roundTripFunc(func(*http.Request) (*http.Response, error) {
		<-ctx.Done()
		return nil, ctx.Err()
	})}
	if sample := ProbeServerInfo(ctx, "example.invalid:80", client); sample.State != "timeout" || sample.ErrorClass != "" {
		t.Fatalf("timeout sample=%#v", sample)
	}
	client.Transport = roundTripFunc(func(*http.Request) (*http.Response, error) {
		return nil, &net.OpError{Op: "dial", Err: errors.New("secret host detail")}
	})
	if sample := ProbeServerInfo(context.Background(), "example.invalid:80", client); sample.State != "transport_error" || sample.ErrorClass != "other" {
		t.Fatalf("transport sample=%#v", sample)
	}
}

func TestSampleServerInfoSamplesImmediatelyAndStops(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) }))
	defer server.Close()
	ctx, cancel := context.WithCancel(context.Background())
	samples := SampleServerInfo(ctx, strings.TrimPrefix(server.URL, "http://"), 100*time.Millisecond, server.Client())
	select {
	case sample := <-samples:
		if !sample.Healthy() {
			t.Fatalf("sample=%#v", sample)
		}
	case <-time.After(50 * time.Millisecond):
		t.Fatal("initial sample was not immediate")
	}
	cancel()
	select {
	case _, ok := <-samples:
		if ok {
			t.Fatal("sampler emitted after cancellation")
		}
	case <-time.After(time.Second):
		t.Fatal("sampler did not stop")
	}
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(request *http.Request) (*http.Response, error) { return f(request) }

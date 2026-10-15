// Bridge native Giztest audio captures to bounded, real ASR of the audible tail.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
	"github.com/GizClaw/gizclaw-go/sdk/go/gizcli/contextconn"
)

const tailBytes = 20 * 16000 * 2

type tailBuffer struct {
	data  []byte
	at    int
	size  int
	total int
}

type tailJob struct {
	done   chan struct{}
	result map[string]any
	err    error
}

func (b *tailBuffer) Write(p []byte) (int, error) {
	if b.total+len(p) > 32<<20 {
		return 0, errors.New("decoded audio exceeds limit")
	}
	b.total += len(p)
	n := len(p)
	if n == 0 {
		return 0, nil
	}
	if b.data == nil {
		b.data = make([]byte, tailBytes)
	}
	if n >= tailBytes {
		copy(b.data, p[n-tailBytes:])
		b.at, b.size = 0, tailBytes
	} else {
		copied := copy(b.data[b.at:], p)
		copy(b.data, p[copied:])
		b.at = (b.at + n) % tailBytes
		b.size = min(tailBytes, b.size+n)
	}
	return n, nil
}

func (b *tailBuffer) Bytes() []byte {
	if b.size < tailBytes {
		return append([]byte(nil), b.data[:b.size]...)
	}
	return append(append(make([]byte, 0, tailBytes), b.data[b.at:]...), b.data[:b.at]...)
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run() error {
	endpoint, token := os.Getenv("GIZCLAW_TEST_ENDPOINT"), os.Getenv("GIZCLAW_TEST_REGISTRATION_TOKEN")
	if endpoint == "" || token == "" {
		return errors.New("test endpoint and registration token are required")
	}
	if _, err := exec.LookPath("ffmpeg"); err != nil {
		return err
	}
	root, err := os.MkdirTemp("", "raids-news-tail-context-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(root)
	key, err := giznet.GenerateKeyPair()
	if err != nil {
		return err
	}
	if err := os.Mkdir(filepath.Join(root, "tail"), 0700); err != nil {
		return err
	}
	config := fmt.Sprintf("identity:\n  private-key: %s\nserver:\n  endpoint: %s\n", key.Private.String(), endpoint)
	if err := os.WriteFile(filepath.Join(root, "tail", "config.yaml"), []byte(config), 0600); err != nil {
		return err
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	client, err := contextconn.Connect(ctx, contextconn.Options{ConfigDir: root, Context: "tail"})
	if err != nil {
		return err
	}
	defer client.Close()
	registerCtx, registerCancel := context.WithTimeout(ctx, 15*time.Second)
	_, err = client.Register(registerCtx, "news-tail-register", token)
	registerCancel()
	if err != nil {
		return err
	}
	defer func() {
		cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cleanupCancel()
		_, err := client.DeletePeer(cleanupCtx, "news-tail-delete", rpcapi.ServerPeerDeleteRequest{})
		fmt.Fprintf(os.Stderr, "tail_peer_cleanup_passed=%t\n", err == nil)
	}()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return err
	}
	done := make(chan struct{})
	var once sync.Once
	closeBridge := func() { once.Do(func() { close(done) }) }
	mux := http.NewServeMux()
	transcribe := func(requestCtx context.Context, audio []byte, id string) (map[string]any, error) {
		requestCtx, requestCancel := context.WithTimeout(requestCtx, 75*time.Second)
		defer requestCancel()
		var pcm tailBuffer
		decode := exec.CommandContext(requestCtx, "ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ar", "16000", "-ac", "1", "pipe:1")
		decode.Stdin, decode.Stdout, decode.Stderr = bytes.NewReader(audio), &pcm, io.Discard
		if err := decode.Run(); err != nil || pcm.size == 0 {
			return nil, errors.New("cannot decode received audio")
		}
		pcmTail := pcm.Bytes()
		result, err := client.TranscribeSpeech(requestCtx, id, rpcapi.SpeechTranscribeRequest{ModelName: "asr", ContentType: "audio/L16;rate=16000;channels=1"}, bytes.NewReader(pcmTail))
		if err != nil {
			fmt.Fprintf(os.Stderr, "tail_transcription_error=%T\n", err)
			return nil, errors.New("tail transcription failed")
		}
		proof := map[string]any{"source_sha256": fmt.Sprintf("%x", sha256.Sum256(audio)), "tail_sha256": fmt.Sprintf("%x", sha256.Sum256(pcmTail)), "source_duration_ms": pcm.total / 32, "tail_duration_ms": len(pcmTail) / 32, "transcript_sha256": fmt.Sprintf("%x", sha256.Sum256([]byte(result.Transcript)))}
		encoded, _ := json.Marshal(proof)
		fmt.Fprintln(os.Stderr, "tail_receipt", string(encoded))
		proof["transcript"] = result.Transcript
		return proof, nil
	}
	readAudio := func(w http.ResponseWriter, r *http.Request) []byte {
		var input struct {
			Audio []byte `json:"audio"`
		}
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<20)).Decode(&input); err != nil || len(input.Audio) == 0 {
			http.Error(w, `{"error":"received audio is required"}`, http.StatusBadRequest)
			return nil
		}
		return input.Audio
	}
	mux.HandleFunc("POST /tail", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		audio := readAudio(w, r)
		if audio == nil {
			return
		}
		proof, err := transcribe(r.Context(), audio, "news-tail-preflight")
		if err != nil {
			http.Error(w, `{"error":"tail transcription failed"}`, http.StatusBadGateway)
			return
		}
		_ = json.NewEncoder(w).Encode(proof)
	})
	jobsCtx, cancelJobs := context.WithCancel(ctx)
	defer cancelJobs()
	var jobs sync.Map
	var sequence atomic.Uint64
	var workers sync.WaitGroup
	mux.HandleFunc("POST /tail/start", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		audio := readAudio(w, r)
		if audio == nil {
			return
		}
		n := sequence.Add(1)
		if n > 8 {
			http.Error(w, `{"error":"test job limit reached"}`, http.StatusTooManyRequests)
			return
		}
		id := fmt.Sprintf("news-tail-%d", n)
		job := &tailJob{done: make(chan struct{})}
		jobs.Store(id, job)
		workers.Go(func() {
			job.result, job.err = transcribe(jobsCtx, audio, id)
			close(job.done)
		})
		_ = json.NewEncoder(w).Encode(map[string]string{"job_id": id})
	})
	mux.HandleFunc("GET /tail/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		value, ok := jobs.Load(r.PathValue("id"))
		if !ok {
			http.Error(w, `{"error":"unknown test job"}`, http.StatusNotFound)
			return
		}
		job := value.(*tailJob)
		select {
		case <-job.done:
		case <-r.Context().Done():
			return
		}
		jobs.Delete(r.PathValue("id"))
		if job.err != nil {
			http.Error(w, `{"error":"tail transcription failed"}`, http.StatusBadGateway)
			return
		}
		_ = json.NewEncoder(w).Encode(job.result)
	})
	mux.HandleFunc("POST /close", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = io.WriteString(w, `{"closing":true}`)
		closeBridge()
	})
	server := &http.Server{Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		if err := server.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
			closeBridge()
		}
	}()
	_ = json.NewEncoder(os.Stdout).Encode(map[string]string{"endpoint": "http://" + listener.Addr().String()})
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(signals)
	select {
	case <-done:
	case <-signals:
	}
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()
	err = server.Shutdown(shutdownCtx)
	cancelJobs()
	workers.Wait()
	return err
}

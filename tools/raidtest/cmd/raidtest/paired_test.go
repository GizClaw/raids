package main

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/GizClaw/raids/tools/raidtest/internal/report"
	"github.com/GizClaw/raids/tools/raidtest/internal/server"
)

func testDescriptors(count int) []pairedDescriptor {
	result := make([]pairedDescriptor, count)
	for index := range result {
		result[index] = pairedDescriptor{ordinal: index, caseID: string(rune('a' + index))}
	}
	return result
}

func TestExecutePairedDescriptorsBoundsAndOrdersResults(t *testing.T) {
	var mu sync.Mutex
	active, peak := 0, 0
	release := make(chan struct{})
	run := func(_ context.Context, descriptor pairedDescriptor) pairedExecution {
		mu.Lock()
		active++
		if active > peak {
			peak = active
		}
		mu.Unlock()
		<-release
		mu.Lock()
		active--
		mu.Unlock()
		return pairedExecution{ordinal: descriptor.ordinal, caseResult: report.Case{ID: descriptor.caseID, Status: "pass"}}
	}
	done := make(chan []pairedExecution, 1)
	go func() {
		results, admitted, reportedPeak := executePairedDescriptors(context.Background(), testDescriptors(5), 2, 0, nil, run)
		if admitted != 5 || reportedPeak != 2 {
			t.Errorf("admitted=%d peak=%d", admitted, reportedPeak)
		}
		done <- results
	}()
	deadline := time.After(time.Second)
	for {
		mu.Lock()
		got := peak
		mu.Unlock()
		if got == 2 {
			break
		}
		select {
		case <-deadline:
			t.Fatal("scheduler did not reach configured parallelism")
		default:
			time.Sleep(time.Millisecond)
		}
	}
	close(release)
	results := <-done
	if peak != 2 {
		t.Fatalf("observed peak=%d", peak)
	}
	for index, result := range results {
		if result.ordinal != index || result.caseResult.ID != string(rune('a'+index)) {
			t.Fatalf("results[%d]=%#v", index, result)
		}
	}
}

func TestExecutePairedDescriptorsHonorsRampAndIndependentFailures(t *testing.T) {
	var mu sync.Mutex
	var starts []time.Time
	run := func(_ context.Context, descriptor pairedDescriptor) pairedExecution {
		mu.Lock()
		starts = append(starts, time.Now())
		mu.Unlock()
		err := error(nil)
		if descriptor.ordinal == 0 {
			err = errors.New("independent failure")
		}
		return pairedExecution{ordinal: descriptor.ordinal, caseResult: report.Case{ID: descriptor.caseID}, err: err}
	}
	results, admitted, _ := executePairedDescriptors(context.Background(), testDescriptors(3), 1, 20*time.Millisecond, nil, run)
	if admitted != 3 || len(results) != 3 {
		t.Fatalf("admitted=%d results=%d", admitted, len(results))
	}
	for index := 1; index < len(starts); index++ {
		if delta := starts[index].Sub(starts[index-1]); delta < 15*time.Millisecond {
			t.Fatalf("admission delta=%s", delta)
		}
	}
}

func TestExecutePairedDescriptorsStopsAdmissionOnProbe(t *testing.T) {
	stop := make(chan struct{})
	close(stop)
	called := false
	results, admitted, peak := executePairedDescriptors(context.Background(), testDescriptors(3), 2, 0, stop, func(context.Context, pairedDescriptor) pairedExecution {
		called = true
		return pairedExecution{}
	})
	if called || admitted != 0 || peak != 0 {
		t.Fatalf("called=%t admitted=%d peak=%d", called, admitted, peak)
	}
	for _, result := range results {
		if result.caseResult.Status != "skip" || result.caseResult.Owner != "environment_dependency" || result.caseResult.FailureCheckpointID != "admission" {
			t.Fatalf("result=%#v", result)
		}
	}
}

func TestExecutePairedDescriptorsLetsActiveCaseFinalizeAfterProbeStop(t *testing.T) {
	stop := make(chan struct{})
	started := make(chan struct{})
	release := make(chan struct{})
	type outcome struct {
		results  []pairedExecution
		admitted int
	}
	done := make(chan outcome, 1)
	go func() {
		results, admitted, _ := executePairedDescriptors(context.Background(), testDescriptors(3), 1, 0, stop, func(_ context.Context, descriptor pairedDescriptor) pairedExecution {
			close(started)
			<-release
			return pairedExecution{ordinal: descriptor.ordinal, caseResult: report.Case{ID: descriptor.caseID, Status: "pass"}}
		})
		done <- outcome{results: results, admitted: admitted}
	}()
	<-started
	close(stop)
	close(release)
	got := <-done
	if got.admitted != 1 || got.results[0].caseResult.Status != "pass" {
		t.Fatalf("outcome=%#v", got)
	}
	for _, result := range got.results[1:] {
		if result.caseResult.Status != "skip" || result.caseResult.Owner != "environment_dependency" {
			t.Fatalf("result=%#v", result)
		}
	}
}

func TestProbeCollectorCoalescesTransitions(t *testing.T) {
	collector := newProbeCollector()
	base := time.Now().UTC()
	collector.add(server.ProbeSample{State: "healthy", HTTPStatus: 200, ObservedAt: base})
	collector.add(server.ProbeSample{State: "healthy", HTTPStatus: 200, ObservedAt: base.Add(time.Second)})
	collector.add(server.ProbeSample{State: "http_error", HTTPStatus: 502, ObservedAt: base.Add(2 * time.Second)})
	transitions := collector.snapshot()
	if len(transitions) != 2 || transitions[0].Samples != 2 || transitions[0].LastObservedAt != base.Add(time.Second) || transitions[1].HTTPStatus != 502 {
		t.Fatalf("transitions=%#v", transitions)
	}
	select {
	case <-collector.unhealthy:
	default:
		t.Fatal("unhealthy guard was not closed")
	}
}

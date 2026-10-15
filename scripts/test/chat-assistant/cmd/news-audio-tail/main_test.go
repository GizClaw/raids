package main

import (
	"bytes"
	"testing"
)

func TestTailBufferKeepsLatestAudioAcrossChunkBoundaries(t *testing.T) {
	all := make([]byte, tailBytes*2+1234)
	for i := range all {
		all[i] = byte(i % 251)
	}
	for _, chunk := range []int{1, 320, 8191, tailBytes + 1} {
		var b tailBuffer
		for start := 0; start < len(all); start += chunk {
			end := min(start+chunk, len(all))
			if _, err := b.Write(all[start:end]); err != nil {
				t.Fatal(err)
			}
		}
		if b.total != len(all) || !bytes.Equal(b.Bytes(), all[len(all)-tailBytes:]) {
			t.Fatalf("chunk %d did not retain the latest audio", chunk)
		}
	}
}

func TestTailBufferBoundsDecodedInput(t *testing.T) {
	b := tailBuffer{total: 32 << 20}
	if _, err := b.Write([]byte{0, 0}); err == nil {
		t.Fatal("oversized decoded input was accepted")
	}
}

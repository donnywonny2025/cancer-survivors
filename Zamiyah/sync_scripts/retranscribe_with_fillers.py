#!/usr/bin/env python3
"""
Re-transcribe with large-v2 and suppress_tokens=[] to capture fillers (um, uh, etc.)
Model loaded from local project folder — no downloads needed.
"""
import torch
import sys
import json
import time

# Fix PyTorch 2.6 weights_only default
_orig_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_load(*args, **kwargs)
torch.load = _patched_load

import whisperx

AUDIO = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_S34_16k_mono.wav"
MODEL = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/_multicam_framework/models/faster-whisper-large-v2"
OUTPUT = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_S34_Transcript_WhisperX.json"

print("Loading large-v2 from local folder...", flush=True)
t0 = time.time()
model = whisperx.load_model(
    MODEL, "cpu", compute_type="int8", language="en",
    asr_options={"suppress_tokens": [], "condition_on_previous_text": True},
)
print(f"Model loaded in {time.time()-t0:.1f}s", flush=True)

print("Transcribing with fillers enabled...", flush=True)
t1 = time.time()
result = model.transcribe(AUDIO, batch_size=4, language="en")
print(f"Transcription done in {time.time()-t1:.1f}s", flush=True)

print("Aligning words...", flush=True)
t2 = time.time()
model_a, metadata = whisperx.load_align_model(language_code="en", device="cpu")
result = whisperx.align(result["segments"], model_a, metadata, AUDIO, "cpu")
print(f"Alignment done in {time.time()-t2:.1f}s", flush=True)

# Count fillers
filler_words = {"um", "uh", "ums", "uhs", "hmm", "mhm", "mmm", "ah"}
filler_count = 0
total_words = 0
for seg in result.get("segments", []):
    for w in seg.get("words", []):
        total_words += 1
        if w.get("word", "").lower().strip(".,!?") in filler_words:
            filler_count += 1

print(f"\nTotal words: {total_words}", flush=True)
print(f"Fillers found: {filler_count}", flush=True)

with open(OUTPUT, "w") as f:
    json.dump(result, f, indent=2, default=str)
print(f"Saved to {OUTPUT}", flush=True)
print(f"Total time: {time.time()-t0:.1f}s", flush=True)

#!/usr/bin/env python3
"""Quick A/B test: does boosting audio help Whisper catch fillers?"""
import torch
_o = torch.load
def _p(*a, **k):
    k["weights_only"] = False
    return _o(*a, **k)
torch.load = _p

import whisperx, json, time

MODEL = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/_multicam_framework/models/faster-whisper-large-v2"
BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"

# Two clips: original vs boosted, same 35s segment (515-550s)
clips = {
    "ORIGINAL": f"{BASE}/Master_S34_16k_mono.wav",
    "BOOSTED":  f"{BASE}/Master_S34_16k_mono_boosted.wav",
}

print("Loading model...", flush=True)
model = whisperx.load_model(
    MODEL, "cpu", compute_type="int8", language="en",
    asr_options={"suppress_tokens": [], "condition_on_previous_text": True},
)
print("Model loaded.\n", flush=True)

model_a, metadata = whisperx.load_align_model(language_code="en", device="cpu")

for label, path in clips.items():
    print(f"=== {label} ===", flush=True)
    # Extract just the 35s clip
    import subprocess, os
    clip = f"{BASE}/test_{label.lower()}_clip.wav"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-ss", "515", "-t", "35", clip],
                   capture_output=True)
    
    r = model.transcribe(clip, batch_size=4, language="en")
    r = whisperx.align(r["segments"], model_a, metadata, clip, "cpu")
    
    for seg in r.get("segments", []):
        print(f'  [{seg.get("start",0):.1f}s] "{seg["text"].strip()}"', flush=True)
        for w in seg.get("words", []):
            word = w.get("word", "")
            if word.lower().strip(".,!?") in {"um","uh","hmm","ah","mhm","like"}:
                print(f'    >>> FILLER: "{word}" at {w.get("start",0):.3f}s', flush=True)
    
    os.remove(clip)
    print(flush=True)

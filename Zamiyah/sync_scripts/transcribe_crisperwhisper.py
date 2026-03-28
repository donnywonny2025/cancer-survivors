#!/usr/bin/env python3
"""
Transcribe using CrisperWhisper — verbatim transcription with fillers.
Uses model.generate() directly as recommended for long-form audio.
"""
import torch
import json
import time
import torchaudio

MODEL_DIR = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/_multicam_framework/models/CrisperWhisper"
AUDIO = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_S34_16k_mono.wav"
OUTPUT = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_S34_Transcript_CrisperWhisper.json"

print("Loading CrisperWhisper...", flush=True)
t0 = time.time()

from transformers import WhisperForConditionalGeneration, WhisperProcessor

processor = WhisperProcessor.from_pretrained(MODEL_DIR)
model = WhisperForConditionalGeneration.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float32,
)
model.eval()
print(f"Model loaded in {time.time()-t0:.1f}s", flush=True)

# Load audio
print("Loading audio...", flush=True)
waveform, sr = torchaudio.load(AUDIO)
if sr != 16000:
    waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
waveform = waveform.squeeze().numpy()
print(f"Audio: {len(waveform)/16000:.1f}s", flush=True)

# Process in 30-second chunks
print("Transcribing (verbatim with fillers)...", flush=True)
t1 = time.time()

CHUNK_S = 30
STRIDE_S = 5
all_words = []
chunk_size = CHUNK_S * 16000
stride_size = STRIDE_S * 16000

pos = 0
chunk_idx = 0
while pos < len(waveform):
    chunk = waveform[pos:pos + chunk_size]
    chunk_offset = pos / 16000.0
    
    input_features = processor(
        chunk, sampling_rate=16000, return_tensors="pt"
    ).input_features
    
    with torch.no_grad():
        predicted_ids = model.generate(
            input_features,
            return_timestamps=True,
            language="en",
            task="transcribe",
        )
    
    result = processor.batch_decode(predicted_ids, skip_special_tokens=True, output_offsets=True)
    
    # Also decode with timestamps for word-level timing
    decoded = processor.decode(predicted_ids[0], output_offsets=True)
    
    if hasattr(decoded, 'offsets') and decoded.offsets:
        for offset in decoded.offsets:
            word = offset.get("text", "").strip()
            ts = offset.get("timestamp", (0, 0))
            if word:
                w_start = (ts[0] if ts[0] else 0) + chunk_offset
                w_end = (ts[1] if ts[1] else 0) + chunk_offset
                
                # Skip words that are in the stride overlap (already captured by previous chunk)
                if pos > 0 and w_start < chunk_offset + STRIDE_S:
                    continue
                    
                all_words.append({
                    "word": word,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                })
    else:
        # Fallback: just get the text
        text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        print(f"  Chunk {chunk_idx}: {text[:80]}... (no word timestamps)", flush=True)
    
    chunk_idx += 1
    if chunk_idx % 5 == 0:
        elapsed = time.time() - t1
        progress = min(pos / len(waveform) * 100, 100)
        print(f"  {progress:.0f}% ({chunk_idx} chunks, {elapsed:.0f}s)", flush=True)
    
    pos += chunk_size - stride_size

print(f"Transcription done in {time.time()-t1:.1f}s", flush=True)

# Build WhisperX-compatible output
segments = [{"text": " ".join(w["word"] for w in all_words), "words": all_words}]
output_data = {"segments": segments}

# Count fillers
filler_words = {"um", "uh", "ums", "uhs", "hmm", "mhm", "mmm", "ah", "hm"}
filler_count = 0
filler_list = []
for w in all_words:
    clean = w["word"].lower().strip(".,!?")
    if clean in filler_words:
        filler_count += 1
        m = int(w["start"] // 60)
        s = w["start"] % 60
        filler_list.append(f'  [{m:02d}:{s:05.2f}] "{w["word"]}"')

print(f"\nTotal words: {len(all_words)}", flush=True)
print(f"Fillers found: {filler_count}", flush=True)
if filler_list:
    print("\nFiller locations:", flush=True)
    for f_str in filler_list:
        print(f_str, flush=True)

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2, default=str)
print(f"\nSaved to {OUTPUT}", flush=True)
print(f"Total time: {time.time()-t0:.1f}s", flush=True)

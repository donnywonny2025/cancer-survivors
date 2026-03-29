#!/usr/bin/env python3
"""
Deepgram Verbatim Transcription via REST API — no SDK needed.
Catches every filler word (um, uh, etc.) with word-level timestamps.
"""
import json, time, os, urllib.request

AUDIO = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_S34_16k_mono.wav"
OUTPUT = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_S34_Transcript_Deepgram.json"
API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")

# Deepgram REST API endpoint with filler words enabled
URL = "https://api.deepgram.com/v1/listen?model=nova-2&language=en&filler_words=true&punctuate=true&smart_format=false"

print("Reading audio file...", flush=True)
with open(AUDIO, "rb") as f:
    audio_data = f.read()
print(f"Audio: {len(audio_data) / 1e6:.1f} MB", flush=True)

print("Sending to Deepgram (Nova-2, filler_words=true)...", flush=True)
t0 = time.time()

req = urllib.request.Request(
    URL,
    data=audio_data,
    headers={
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "audio/wav",
    },
)

with urllib.request.urlopen(req, timeout=300) as resp:
    result = json.loads(resp.read().decode())

print(f"Transcription done in {time.time()-t0:.1f}s\n", flush=True)

# Extract words
all_words = []
for channel in result.get("results", {}).get("channels", []):
    for alt in channel.get("alternatives", []):
        for w in alt.get("words", []):
            all_words.append({
                "word": w["word"],
                "start": w["start"],
                "end": w["end"],
                "confidence": w.get("confidence", 0),
            })

# Build segments (group by pauses > 1s)  
segments = []
current_seg = {"text": "", "words": [], "start": 0, "end": 0}
for w in all_words:
    if current_seg["words"] and w["start"] - current_seg["words"][-1]["end"] > 1.0:
        current_seg["end"] = current_seg["words"][-1]["end"]
        current_seg["text"] = current_seg["text"].strip()
        segments.append(current_seg)
        current_seg = {"text": "", "words": [], "start": w["start"], "end": 0}
    current_seg["words"].append(w)
    current_seg["text"] += " " + w["word"]

if current_seg["words"]:
    current_seg["end"] = current_seg["words"][-1]["end"]
    current_seg["text"] = current_seg["text"].strip()
    segments.append(current_seg)

output_data = {"segments": segments, "source": "deepgram-nova-2"}

# Count fillers
filler_set = {"um", "uh", "ums", "uhs", "hmm", "mhm", "mmm", "ah", "hm", "mm"}
filler_count = 0
filler_list = []
for w in all_words:
    clean = w["word"].lower().strip(".,!? ")
    if clean in filler_set:
        filler_count += 1
        m = int(w["start"] // 60)
        s = w["start"] % 60
        filler_list.append(f'  [{m:02d}:{s:05.2f}] "{w["word"]}"')

print(f"Total words: {len(all_words)}", flush=True)
print(f"Total segments: {len(segments)}", flush=True)
print(f"FILLERS FOUND: {filler_count}", flush=True)
if filler_list:
    print("\nFiller locations:", flush=True)
    for f_str in filler_list:
        print(f_str, flush=True)

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to {OUTPUT}", flush=True)
print(f"Total time: {time.time()-t0:.1f}s", flush=True)

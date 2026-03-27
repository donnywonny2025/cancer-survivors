#!/usr/bin/env python3
import subprocess, numpy as np, os

def extract_audio_np(path, start_sec, dur_sec):
    """Extract audio via ffmpeg."""
    tmp = f"/tmp/_xcorr_tmp_{os.getpid()}.raw"
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start_sec), "-i", path,
        "-t", str(dur_sec), "-vn", "-ac", "1", "-ar", "16000",
        "-f", "s16le", tmp
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(tmp): return np.zeros(1)
    data = np.fromfile(tmp, dtype=np.int16).astype(np.float32) / 32768.0
    os.remove(tmp)
    return data

def find_offset_large(reference, target):
    """FFT cross-correlation."""
    n = len(reference) + len(target) - 1
    fft_size = 1
    while fft_size < n: fft_size *= 2
    ref_fft = np.fft.rfft(reference, fft_size)
    tgt_fft = np.fft.rfft(target, fft_size)
    xcorr = np.fft.irfft(ref_fft * np.conj(tgt_fft))
    peak = np.argmax(xcorr)
    if peak > fft_size // 2: peak -= fft_size
    return peak

SR = 16000
BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
MASTER_PATH = f"{BASE}/Audio/TASCAM_1087S34.wav"

print(f"Syncing against Master: {os.path.basename(MASTER_PATH)}")
# Use a massive 5-minute baseline search to be bulletproof
print("Extracting 5-minute baseline from Master...")
ref_extended = extract_audio_np(MASTER_PATH, 0, 300)

CLIPS = [
    ("Footage/Cam A", "C8826.MP4"),
    ("Footage/Cam B", "C8890.MP4"),
]

offsets = {}
for folder, name in CLIPS:
    path = f"{BASE}/{folder}/{name}"
    print(f"\nProcessing {name} (3 min candidate)...")
    target = extract_audio_np(path, 0, 180)
    
    if len(target) < 1000:
        print(f"  Error extracting {name}")
        continue
        
    lag_samples = find_offset_large(ref_extended, target)
    lag_sec = lag_samples / SR
    
    offsets[f"{folder}/{name}"] = lag_sec
    print(f"  Result: Lag = {lag_sec:.4f}s")
    if lag_sec > 0:
        print(f"  Interpretation: Camera started {lag_sec:.4f}s AFTER Master")
    else:
        print(f"  Interpretation: Camera started {abs(lag_sec):.4f}s BEFORE Master")

print("\n=== FINAL VERIFIED OFFSET TABLE ===")
for k, v in offsets.items():
    print(f"  {k}: {v:.4f}s")

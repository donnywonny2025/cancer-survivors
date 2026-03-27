#!/usr/bin/env python3
import sys, numpy as np, os
sys.path.append("/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts")
import multicam_core as core

def find_offset(reference, target, sr=16000):
    n = len(reference) + len(target) - 1
    fft_size = 1
    while fft_size < n: fft_size *= 2
    ref_fft = np.fft.rfft(reference, fft_size)
    tgt_fft = np.fft.rfft(target, fft_size)
    xcorr = np.fft.irfft(ref_fft * np.conj(tgt_fft))
    peak = np.argmax(xcorr)
    if peak > fft_size // 2: peak -= fft_size
    return peak

def main():
    MIC_PATH = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Audio/TASCAM_1087S34.wav"
    CAM_A = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Footage/Cam A/C8826.MP4"
    CAM_B = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Footage/Cam B/C8890.MP4"
    SR = 16000

    clips = [("Cam A", CAM_A), ("Cam B", CAM_B)]
    
    print("--- HEAD SYNC (0s) ---")
    ref_head = core.extract_mono(MIC_PATH, SR, "zam_ref_h")[:SR*30]
    for name, path in clips:
        target = core.extract_mono(path, SR, f"zam_{name}_h")[:SR*60]
        lag = find_offset(ref_head, target)
        print(f"  {name} Head Offset: {lag/SR:.4f}s")

    print("\n--- TAIL SYNC (1200s) ---")
    # For tail sync, we extract ref at 1200s and target at 1100s-1300s
    ref_tail = core.extract_mono(MIC_PATH, SR, "zam_ref_t")[SR*1200:SR*1230]
    for name, path in clips:
        # Check around the 1170s mark for the camera
        target = core.extract_mono(path, SR, f"zam_{name}_t")[SR*1150:SR*1250]
        lag = find_offset(ref_tail, target)
        # The lag is relative to the start of the extracted target chunk (1150)
        # and start of ref chunk (1200). 
        # offset = (1200 + lag_relative_to_ref_start) - (1150 + lag_relative_to_tgt_start)
        # Wait, if lag is x, then ref_start - tgt_start = lag
        # 1200 - (1150 + lag_relative_to_tgt_start) = lag? No.
        # Let's just use the absolute offset:
        true_offset = 1200 - (1150 + lag/SR)
        print(f"  {name} Tail Offset: {true_offset:.4f}s (Check against Head)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys, os
sys.path.append("/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts")
import multicam_core as core

def main():
    AUDIO_PATH = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Audio/TASCAM_1087S34.wav"
    OUT_DIR = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/"
    
    # Using local whisper command
    print(f"Transcribing {AUDIO_PATH}...")
    # I'll just run the whisper command via subprocess
    import subprocess
    subprocess.run([
        "whisper", AUDIO_PATH, 
        "--model", "base", 
        "--output_dir", OUT_DIR, 
        "--output_format", "json",
        "--device", "cpu"
    ])
    
    # Rename for consistency
    old_name = f"{OUT_DIR}/TASCAM_1087S34.json"
    new_name = f"{OUT_DIR}/Master_S34_Transcript.json"
    if os.path.exists(old_name):
        os.rename(old_name, new_name)
        print(f"Transcript generated: {new_name}")

if __name__ == "__main__":
    main()

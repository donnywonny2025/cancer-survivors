import whisper, torch, json, os

# Throttled to 4 cores for M2 system comfort
torch.set_num_threads(4)
# Detecting Mac Hardware Acceleration (MPS)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

# Production Standard 2026: Whisper Medium Persistence
model_dir = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Models"
# Using CPU for initial stability verification
model = whisper.load_model("medium.en", device="cpu", download_root=model_dir)

def transcribe_full(path, name):
    if not os.path.exists(path):
        print(f"⚠️ Skip: {path} not found.")
        return
        
    print(f"Starting FULL Master Transcription for {name} (MEDIUM model)...")
    tmp_wav = f"/tmp/{name}_16k.wav"
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", tmp_wav]
    subprocess.run(cmd, stdin=subprocess.DEVNULL)
    
    # word_timestamps=True allows for exact camera alignment later
    result = model.transcribe(tmp_wav, word_timestamps=True, fp16=False)
    
    out_json = f"/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Master_{name}_Transcript.json"
    with open(out_json, "w") as f:
        json.dump(result, f, indent=4)
    print(f"✅ Saved Master {name} Transcript to {out_json}")

mic2 = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/Audio/TASCAM_1087S34.wav"

transcribe_full(mic2, "S34")

print("\n--- ALL MASTER TRANSCRIPTIONS COMPLETE ---")

import whisper, torch, json, os

# Optimized for M2 (4 threads)
torch.set_num_threads(4)
model = whisper.load_model("base.en", device="cpu")

AUDIO_PATH = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Vince/Audio/Vince_Interview_16k.wav"
OUT_JSON = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Vince/Vince_Master_Transcript.json"

def transcribe():
    print(f"Starting Whisper Transcription (Base.en) for Vince Interview...")
    print(f"Source: {AUDIO_PATH}")
    
    # word_timestamps=True is critical for multicam automated cutting
    result = model.transcribe(AUDIO_PATH, word_timestamps=True, fp16=False)
    
    with open(OUT_JSON, "w") as f:
        json.dump(result, f, indent=4)
        
    print(f"✅ Saved Vince Master Transcript to {OUT_JSON}")
    print(f"Total Segments: {len(result['segments'])}")

if __name__ == "__main__":
    transcribe()

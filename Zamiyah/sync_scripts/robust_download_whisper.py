import os, subprocess

# Production Standard 2026: Whisper Medium Persistence
model_url = "https://openaipublic.azureedge.net/main/whisper/models/d7440d1dc186f76616474e0ff0b3b6b879abc9d1a4926b7adfa41db2d497ab4f/medium.en.pt"
model_dir = "/Volumes/WORK 2TB/WORK 2026/SANDBOX/Models"
model_path = os.path.join(model_dir, "medium.en.pt")

if not os.path.exists(model_dir):
    os.makedirs(model_dir, exist_ok=True)

# Remove partial file to ensure a clean resume/download
if os.path.exists(model_path):
    print(f"🧹 Clearing partial file: {model_path}")
    os.remove(model_path)

print(f"🚀 Starting ROBUST CURL download to: {model_path}")
try:
    # Using curl for better stability and resume support
    subprocess.run(["curl", "-L", "-o", model_path, model_url], check=True)
    size = os.path.getsize(model_path) / (1024**3)
    print(f"✅ DOWNLOAD COMPLETE: {model_path} ({size:.2f} GB)")
except Exception as e:
    print(f"❌ DOWNLOAD FAILED: {e}")

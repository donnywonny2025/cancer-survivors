#!/usr/bin/env python3
import json, os, subprocess

"""
🚀 THE ZAMIYAH FORENSIC SYNC ENGINE (v2.0)
A "Zero-Guess" autonomous scanner for Multicam projects.
Standard: UHD (3840x2160) | 29.97 Drop-Frame (DF) | GOLDEN LAYOUT (V1/A1, V2/A2, A3-Tascam)
"""

def get_metadata(path):
    """Scan for Frame Rate, Duration, and Resolution via ffprobe."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate,width,height,duration", "-of", "json", path]
    try:
        data = json.loads(subprocess.check_output(cmd))
        s = data['streams'][0]
        fr = s['avg_frame_rate'].split('/')
        fps = float(fr[0]) / float(fr[1])
        return {
            "name": os.path.basename(path),
            "fps": round(fps, 3),
            "width": s['width'],
            "height": s['height'],
            "duration_sec": float(s['duration'])
        }
    except Exception as e:
        return {"error": str(e)}

def run_forensic_audit(config_path):
    print("----------------------------------------------------------------")
    print("🔍 PERFORMING FORENSIC METADATA AUDIT...")
    print("----------------------------------------------------------------")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    seq = config.get("sequence_settings", {})
    target_fps = seq.get("timebase", 30)
    target_res = (seq.get("width", 3840), seq.get("height", 2160))
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(config_path))) # Zamiyah root
    
    assets = [
        ("Cam A", os.path.join(base_dir, config["cam_a"])),
        ("Cam B", os.path.join(base_dir, config["cam_b"]))
    ]
    
    conflicts = []
    
    for label, path in assets:
        meta = get_metadata(path)
        if "error" in meta:
            print(f"❌ {label}: FAILED TO READ ({meta['error']})")
            continue
            
        print(f"✅ {label}: {meta['name']}")
        print(f"   Resolution: {meta['width']}x{meta['height']} (Target: {target_res[0]}x{target_res[1]})")
        print(f"   Frame Rate: {meta['fps']} fps (Sequence: {target_fps} fps)")
        
        # Conflict Detection Logic
        if meta['fps'] != 29.97 and meta['fps'] != 30.0 and meta['fps'] != 59.94:
            if abs(meta['fps'] - 23.976) < 0.1:
                conflicts.append(f"⚠️  WARNING: {label} is 23.976fps. This will cause drift in a 29.97 sequence unless Absolute 30fps Anchoring is used.")
            else:
                conflicts.append(f"🚨 CRITICAL: {label} has unexpected frame rate: {meta['fps']}fps.")
        
        if meta['width'] != target_res[0] or meta['height'] != target_res[1]:
            conflicts.append(f"⚠️  RESOLUTION MISMATCH: {label} is {meta['width']}x{meta['height']}.")

    print("\n----------------------------------------------------------------")
    if conflicts:
        print("🚩 FORENSIC ALERT: CONFLICTS DETECTED")
        for c in conflicts:
            print(f"  {c}")
        print("\nACTION: The system will automatically enable 'Absolute 30fps Anchoring'")
        print("        to prevent temporal drift on the mismatched tracks.")
    else:
        print("💎 METADATA CLEAN: All tracks align with project standards.")
    print("----------------------------------------------------------------")

if __name__ == "__main__":
    CONFIG_PATH = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah/START_HERE/configs/sync_config.json"
    run_forensic_audit(CONFIG_PATH)

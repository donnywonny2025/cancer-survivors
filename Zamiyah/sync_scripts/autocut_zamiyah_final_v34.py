#!/usr/bin/env python3
import json, os, datetime
from urllib.parse import quote

# ============================================================
# CONFIG & FORENSIC OFFSETS (Verified v34.2)
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
TRANSCRIPT_PATH = f"{BASE}/Master_S34_Transcript.json"
MANIFEST_PATH = f"{BASE}/sync_scripts/narrative_manifest.json"
XML_OUT = f"{BASE}/Premiere/XML/Zamiyah_PRODUCTION_NARRATIVE_V34.xml"

# Forensic Sync Offsets (Seconds relative to TASCAM 0.0)
OFFSET_A = 63.3134   # Trim to match TASCAM 0.0
OFFSET_B = 75.8219   # Trim to match TASCAM 0.0

# Standards
TIMEBASE = "30"
FPS = 30 # Absolute Frame Math

# ============================================================
# UTILITIES
# ============================================================

def sec_to_f30(sec):
    return int(round(sec * 30.0))

def get_xml_clip(track_name, filename, path, start_sec, end_sec, offset_sec, clip_id):
    """Generates an XMEML clipitem with absolute 30fps math."""
    dur_sec = end_sec - start_sec
    
    # Timeline position (Absolute 30fps)
    s_frames = sec_to_f30(start_sec)
    e_frames = sec_to_f30(end_sec)
    
    # Source Media 'In' point (Absolute 30fps)
    in_frames = sec_to_f30(start_sec + offset_sec)
    out_frames = sec_to_f30(end_sec + offset_sec)
    
    url = f"file://localhost{quote(path)}"
    
    return f"""                <clipitem id="{clip_id}">
                    <name>{filename}</name>
                    <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
                    <start>{s_frames}</start>
                    <end>{e_frames}</end>
                    <in>{in_frames}</in>
                    <out>{out_frames}</out>
                    <file id="file_{filename.replace('.','_')}">
                        <name>{filename}</name>
                        <pathurl>{url}</pathurl>
                    </file>
                </clipitem>"""

# ============================================================
# EXECUTION
# ============================================================

def run_cut():
    print(f"🎬 Initializing Production Cut: {XML_OUT}")
    
    # 1. Load Data
    with open(TRANSCRIPT_PATH, "r") as f:
        transcript = json.load(f)
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
        
    segments = transcript.get("segments", [])
    gold_beats = manifest.get("gold_selects", [])
    
    # 2. Map Manifest Beats to timecodes
    # We prioritize the manifest. If a segment falls within a Gold Beat, 
    # we use the camera preference from the manifest.
    
    # 3. Build XML Header
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="4">
<sequence id="Zamiyah_Production_Narrative">
    <name>Zamiyah_NARRATIVE_PRODUCTION_V34</name>
    <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
    <media>
        <video>
            <format><samplecharacteristics>
                <width>3840</width><height>2160</height>
                <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
                <dropframe>TRUE</dropframe>
            </samplecharacteristics></format>
"""
    
    # 4. Generate Video Tracks (V1=Cam A, V2=Cam B)
    v_tracks = ["", ""]
    clip_counter = 0
    
    for seg in segments:
        s = seg['start']
        e = seg['end']
        text = seg['text'].lower()
        
        # Determine Camera Priority
        # Default: Cam A (Tight) for most. Cam B (Wide) for transitions/interviewer.
        cam_pref = "A" 
        
        # Check Manifest for specific thematic mapping
        for beat in gold_beats:
            if beat['start_text'].lower() in text:
                cam_pref = beat['cam_preference']
                break
        
        # Build clips for the stack
        for i in range(2):
            filename = "C8826.MP4" if i == 0 else "C8890.MP4"
            folder = "Footage/Cam A" if i == 0 else "Footage/Cam B"
            path = os.path.join(BASE, folder, filename)
            offset = OFFSET_A if i == 0 else OFFSET_B
            
            # Simple rule: If pref is A, only put clip on V1. If B, put on V2?
            # Actually, to maintain standard, we put the ACTIVE camera on its track
            # and leave the other empty to show the cut.
            
            is_active = (cam_pref == "A" and i == 0) or (cam_pref == "B" and i == 1)
            # REACTION SHOT: If segment > 15s, flip camera halfway
            if is_active:
                v_tracks[i] += get_xml_clip(f"V{i+1}", filename, path, s, e, offset, f"v_{clip_counter}")
                clip_counter += 1

    xml += "            <track>\n" + v_tracks[0] + "            </track>\n"
    xml += "            <track>\n" + v_tracks[1] + "            </track>\n"
    
    # 5. Build Audio Tracks (A1=Cam A, A2=Cam B, A3=TASCAM)
    xml += """        </video>
        <audio>
            <numchannels>3</numchannels>
"""
    # Track A1 (Cam A Audio - synced)
    xml += "            <track>\n"
    for seg in segments:
        v_tracks[0] # REUSE the same logic
        path = os.path.join(BASE, "Footage/Cam A/C8826.MP4")
        xml += get_xml_clip("A1", "C8826.MP4", path, seg['start'], seg['end'], OFFSET_A, f"a1_{seg['start']}")
    xml += "            </track>\n"
    
    # Track A2 (Cam B Audio - synced)
    xml += "            <track>\n"
    for seg in segments:
        path = os.path.join(BASE, "Footage/Cam B/C8890.MP4")
        xml += get_xml_clip("A2", "C8890.MP4", path, seg['start'], seg['end'], OFFSET_B, f"a2_{seg['start']}")
    xml += "            </track>\n"

    # Track A3 (MASTER TASCAM - The Gold Audio)
    xml += "            <track>\n"
    tascam_path = os.path.join(BASE, "Audio/TASCAM_1087S34.wav")
    for seg in segments:
        xml += get_xml_clip("A3", "TASCAM_1087S34.wav", tascam_path, seg['start'], seg['end'], 0.0, f"a3_{seg['start']}")
    xml += "            </track>\n"

    xml += """        </audio>
    </media>
</sequence>
</xmeml>"""

    # 6. Save
    os.makedirs(os.path.dirname(XML_OUT), exist_ok=True)
    with open(XML_OUT, "w") as f:
        f.write(xml)
    print(f"✅ PRODUCTION XML GENERATED: {XML_OUT}")

if __name__ == "__main__":
    run_cut()

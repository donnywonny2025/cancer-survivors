#!/usr/bin/env python3
import json, os, subprocess
from urllib.parse import quote

# ============================================================
# CONFIG
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
TRANSCRIPT_PATH = f"{BASE}/Master_S34_Transcript.json"

# LOCKED OFFSETS (30fps Absolute)
# We found these to be the North Star.
CAM_A_IN = 1897   # 63.3s
CAM_B_IN = 2274   # 75.8s

FPS = 29.97
TIMEBASE = 30

# ============================================================
# STEP 1: Load Transcript
# ============================================================
with open(TRANSCRIPT_PATH, "r") as f:
    data = json.load(f)

segments = data.get("segments", [])
print(f"Loaded {len(segments)} segments.")

# ============================================================
# STEP 2: Editorial Logic (Host vs Guest)
# ============================================================
# Heuristic: 
# - Host asks short questions (usually < 8s) containing '?' or starting with 'Tell me'
# - Guest answers long (usually > 10s)
# - Default to Cam A for Host, Cam B for Guest.

cuts = []
for seg in segments:
    s = seg["start"]
    e = seg["end"]
    txt = seg["text"].strip().lower()
    dur = e - s
    
    # Determine speaker
    speaker = "GUEST" # Default to Guest (Cam B)
    
    # Host heuristics
    if dur < 10.0 and ('?' in txt or txt.startswith('tell me') or txt.startswith('can you')):
        speaker = "HOST"
    elif dur < 3.0: # Short interjections/reactions
        speaker = "HOST"
        
    cuts.append({
        "start": s,
        "end": e,
        "speaker": speaker,
        "text": txt
    })

# Merge consecutive segments for same speaker
merged_cuts = []
if cuts:
    current = cuts[0]
    for i in range(1, len(cuts)):
        nxt = cuts[i]
        if nxt["speaker"] == current["speaker"]:
            current["end"] = nxt["end"]
        else:
            merged_cuts.append(current)
            current = nxt
    merged_cuts.append(current)

print(f"Generated {len(merged_cuts)} editorial cuts.")

# ============================================================
# STEP 3: Generate XML (v35)
# ============================================================
def sec_to_frames(sec): return int(round(sec * TIMEBASE))

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append('  <sequence>')
L.append('    <name>Zamiyah Intelligence Cut v35 (FINAL)</name>')
L.append('    <rate><timebase>30</timebase><ntsc>TRUE</ntsc><displayformat>DF</displayformat></rate>')
L.append('    <media>')
L.append('      <video>')
L.append('        <format><samplecharacteristics>')
L.append('          <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append('          <width>3840</width><height>2160</height>')
L.append('        </samplecharacteristics></format>')
L.append('        <track>')
L.append('          <name>V1: Intel Cut (A/B Stack)</name>')

for i, cut in enumerate(merged_cuts):
    s_sec = cut["start"]
    e_sec = cut["end"]
    spk = cut["speaker"]
    
    # Target clip parameters
    if spk == "HOST":
        name = "C8826_CamA"
        clip_in = CAM_A_IN + sec_to_frames(s_sec)
        path = "Footage/Cam A/C8826.MP4"
    else:
        name = "C8890_CamB"
        clip_in = CAM_B_IN + sec_to_frames(s_sec)
        path = "Footage/Cam B/C8890.MP4"
        
    tl_start = sec_to_frames(s_sec)
    tl_end = sec_to_frames(e_sec)
    clip_out = clip_in + (tl_end - tl_start)
    
    url = f"file://localhost{BASE}/{path}".replace(" ", "%20")
    
    L.append(f'          <clipitem id="cut_{i}">')
    L.append(f'            <name>{name}</name>')
    L.append(f'            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{tl_start}</start><end>{tl_end}</end>')
    L.append(f'            <in>{clip_in}</in><out>{clip_out}</out>')
    L.append(f'            <file id="f_{spk}_{i}">')
    L.append(f'              <name>{name}</name>')
    L.append(f'              <pathurl>{url}</pathurl>')
    L.append('              <media><video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video></media>')
    L.append('            </file>')
    L.append('          </clipitem>')

L.append('        </track>')
L.append('      </video>')
L.append('      <audio>')
L.append('        <numchannels>2</numchannels>')
L.append('        <track>')
L.append('          <name>A1: TASCAM Master (Mono L)</name>')
L.append('          <clipitem id="a1_t">')
L.append('            <name>TASCAM_1087S34.wav</name>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append('            <start>0</start><end>42836</end>')
L.append('            <in>0</in><out>42836</out>')
L.append('            <file id="f_t">')
L.append('              <name>TASCAM_1087S34.wav</name>')
L.append(f'              <pathurl>file://localhost{BASE}/Audio/TASCAM_1087S34.wav</pathurl>'.replace(" ", "%20"))
L.append('              <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
L.append('            </file>')
L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
L.append('          </clipitem>')
L.append('        </track>')
L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')

xml_content = "\n".join(L)
out_path = f"{BASE}/Premiere/XML/Zamiyah_Multicam_v35_Intelligence_Cut.xml"
with open(out_path, "w") as f:
    f.write(xml_content)

print(f"Wrote v35 Intelligence Cut to: {out_path}")

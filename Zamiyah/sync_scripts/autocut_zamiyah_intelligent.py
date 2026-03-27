#!/usr/bin/env python3
import json, os
from urllib.parse import quote

# ============================================================
# CONFIG & OFFSETS (From Forensic Engine)
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
TRANSCRIPT_PATH = f"{BASE}/Master_S34_Transcript.json"
XML_OUT = f"{BASE}/Premiere/XML/Zamiyah_INTELLIGENT_CUT_V1.xml"

# Forensic Sync Offsets (verified in gen_multicam_v34_2.py)
SYNC_OFFSET_A = -63.2819
SYNC_OFFSET_B = -75.7851

# Frame Rate Constants
FPS = 29.97
TIMEBASE = "30" # Absolute Anchor

# ============================================================
# UTILITIES
# ============================================================

def sec_to_frames_30(sec):
    """Enforce Absolute 30fps sequence anchoring to bypass scaling drift."""
    return int(round(sec * 30.0))

def is_interviewer(text):
    """Heuristic: Interviewer asks questions or gives short feedback."""
    text = text.strip()
    return text.endswith("?") or len(text.split()) < 8

# ============================================================
# LOGIC: Narrative Assembly
# ============================================================

def generate_intelligent_xml():
    print(f"Loading transcript: {TRANSCRIPT_PATH}...")
    with open(TRANSCRIPT_PATH, "r") as f:
        data = json.load(f)
    
    segments = data.get("segments", [])
    
    # We group segments into speaker blocks
    blocks = []
    if not segments: return
    
    current_speaker = "INTERVIEWER" if is_interviewer(segments[0]['text']) else "ZAMIYAH"
    current_block = {
        "speaker": current_speaker,
        "start": segments[0]['start'],
        "end": segments[0]['end'],
        "text": segments[0]['text']
    }
    
    for seg in segments[1:]:
        speaker = "INTERVIEWER" if is_interviewer(seg['text']) else "ZAMIYAH"
        # If speaker same or it's a very short interjection, keep in same block
        if speaker == current_speaker or (len(seg['text'].split()) < 3 and seg['start'] - current_block['end'] < 0.5):
            current_block['end'] = seg['end']
            current_block['text'] += " " + seg['text']
        else:
            blocks.append(current_block)
            current_speaker = speaker
            current_block = {
                "speaker": speaker,
                "start": seg['start'],
                "end": seg['end'],
                "text": seg['text']
            }
    blocks.append(current_block)

    # XML Construction
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="4">
<sequence id="Zamiyah_Intelligent_Cut">
    <name>Zamiyah_INTELLIGENT_NARRATIVE_V1</name>
    <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
    <media>
        <video>
            <format><samplecharacteristics>
                <width>3840</width><height>2160</height>
                <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
                <dropframe>TRUE</dropframe>
            </samplecharacteristics></format>
"""
    
    # Tracks:
    # V1 (Track 0): Cam A (Tight - Zamiyah)
    # V2 (Track 1): Cam B (Wide - Alt/Interviewer)
    
    tracks = [[] for _ in range(2)] # List of clips for each track
    
    curr_seq_frames = 0
    for block in blocks:
        dur = block['end'] - block['start']
        if dur < 0.5: continue # Skip glitched segments
        
        # CARDINAL RULE: Show Speaker
        # Track 0 = Cam A (Zamiyah)
        # Track 1 = Cam B (Interviewer)
        
        # Build multi-cam stack for the block
        for t_idx in range(2):
            offset = SYNC_OFFSET_A if t_idx == 0 else SYNC_OFFSET_B
            filename = "C8826.MP4" if t_idx == 0 else "C8890.MP4"
            folder = "Footage/Cam A" if t_idx == 0 else "Footage/Cam B"
            path = os.path.join(BASE, folder, filename)
            
            # Clip Timing
            # REACTION SHOT LOGIC: 
            # If Zamiyah speaks for more than 12s, insert a 2s Cam B cut halfway.
            is_reaction = False
            if t_idx == 1 and block['speaker'] == "ZAMIYAH" and dur > 12.0:
                is_reaction = True
                # Move start/end to a 2s window in the middle
                mid = block['start'] + (dur / 2.0)
                react_start = mid - 1.0
                react_end = mid + 1.0
                
                s_frames = sec_to_frames_30((curr_seq_frames + (dur/2.0 - 1.0) * 30.0) / 30.0)
                e_frames = sec_to_frames_30((curr_seq_frames + (dur/2.0 + 1.0) * 30.0) / 30.0)
                in_frames = sec_to_frames_30(react_start + offset)
                out_frames = sec_to_frames_30(react_end + offset)
            elif t_idx == 1 and block['speaker'] == "ZAMIYAH":
                continue 
            else:
                # Normal primary or interviewer block
                s_frames = sec_to_frames_30(curr_seq_frames / 30.0)
                e_frames = sec_to_frames_30((curr_seq_frames + dur * 30.0) / 30.0)
                in_frames = sec_to_frames_30(block['start'] + offset)
                out_frames = sec_to_frames_30(block['end'] + offset)
            
            tracks[t_idx].append({
                "name": filename,
                "start": s_frames,
                "end": e_frames,
                "in": in_frames,
                "out": out_frames,
                "path": f"file://localhost{quote(path)}"
            })
            
        curr_seq_frames += dur * 30.0

    # Write Video Tracks
    for i, segments in enumerate(tracks):
        xml += f"            <track>\n"
        for clip in segments:
            xml += f"""                <clipitem id="clip_{i}_{clip['start']}">
                    <name>{clip['name']}</name>
                    <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
                    <start>{clip['start']}</start>
                    <end>{clip['end']}</end>
                    <in>{clip['in']}</in>
                    <out>{clip['out']}</out>
                    <file id="file_{i}">
                        <name>{clip['name']}</name>
                        <pathurl>{clip['path']}</pathurl>
                    </file>
                </clipitem>\n"""
        xml += "            </track>\n"

    xml += """        </video>
        <audio>
            <track>
                <!-- Master TASCAM (Track A3) -->
"""
    # Audio Track Logic (TASCAM)
    curr_seq_frames = 0
    tascam_path = os.path.join(BASE, "Audio/TASCAM_1087S34.wav")
    for block in blocks:
        dur = block['end'] - block['start']
        if dur < 0.5: continue
        s_frames = sec_to_frames_30(curr_seq_frames / 30.0)
        e_frames = sec_to_frames_30((curr_seq_frames + dur * 30.0) / 30.0)
        in_frames = sec_to_frames_30(block['start'])
        out_frames = sec_to_frames_30(block['end'])
        
        xml += f"""                <clipitem id="audio_{block['start']}">
                    <name>TASCAM_1087S34.wav</name>
                    <rate><timebase>{TIMEBASE}</timebase><ntsc>TRUE</ntsc></rate>
                    <start>{s_frames}</start>
                    <end>{e_frames}</end>
                    <in>{in_frames}</in>
                    <out>{out_frames}</out>
                    <file id="file_audio">
                        <name>TASCAM_1087S34.wav</name>
                        <pathurl>file://localhost{quote(tascam_path)}</pathurl>
                    </file>
                </clipitem>\n"""
        curr_seq_frames += dur * 30.0

    xml += """            </track>
        </audio>
    </media>
</sequence>
</xmeml>"""

    os.makedirs(os.path.dirname(XML_OUT), exist_ok=True)
    with open(XML_OUT, "w") as f:
        f.write(xml)
    print(f"✅ Generated Intelligent Cut: {XML_OUT}")

if __name__ == "__main__":
    generate_intelligent_xml()

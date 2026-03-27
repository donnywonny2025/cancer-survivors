#!/usr/bin/env python3
import json, os, subprocess
from urllib.parse import quote

# ============================================================
# CONFIG
# ============================================================
BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
TRANSCRIPT_PATH = f"{BASE}/Master_1087S12_Transcript.json"

XML_OUT = f"{BASE}/Zamiyah_V4_NARRATIVE_SELECTS.xml"

SYNC_OFFSET_A = -0.2451
SYNC_OFFSET_B = -0.7935

# Editorial Selects (Time Ranges in seconds from the Master TASCAM)
# These are the "Gold" moments identified in the transcript analysis.
SELECTS = [
    (20.0, 100.0, "INTRO"),       # Name, early symptoms
    (150.0, 230.0, "PERSONALITY"), # Bubbly, music, piano/guitar
    (310.0, 390.0, "STRUGGLE"),    # Realizing something was wrong
    (430.0, 520.0, "MENTAL"),      # Impact on life, confidence
    (580.0, 680.0, "ADVICE"),      # Fear is normal, take your power back
    (690.0, 800.0, "GROWTH"),      # Mentally grown, don't take small days for granted
    (840.0, 960.0, "HEALING"),     # Writing songs, music therapy
    (1020.0, 1150.0, "SDOH"),      # Care disparity / Oncology praise
    (1240.0, 1380.0, "ADVOCACY")   # 19yo self-advocacy
]

CAM_A = ("Footage/Cam A", "C8826.MP4", SYNC_OFFSET_A)
CAM_B = ("Footage/Cam B", "C8890.MP4", SYNC_OFFSET_B)
AUDIO = ("Audio", "TASCAM_1087S34.wav", 0.0) # Master Audio

# ============================================================
# LOGIC
# ============================================================

def sec_to_frames(sec): return int(round(sec * 23.976))

def generate_xml(selects):
    xml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml SYSTEM "http://developer.apple.com/appleapplications/vxml/sw_xmeml.dtd">
<xmeml version="5">
<sequence>
    <name>Zamiyah_NARRATIVE_SELECTS_V4</name>
    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
    <media>
        <video>
"""
    
    # Video Tracks
    v_tracks = ""
    for track_idx, (folder, file, offset) in enumerate([CAM_A, CAM_B]):
        v_tracks += f'            <track>\n'
        curr_time = 0.0
        for start, end, label in selects:
            dur = end - start
            # For variety, we switch between A and B
            # In this simple logic, Cam A is even, Cam B is odd
            active = (track_idx == 0 and int(start // 30) % 2 == 0) or (track_idx == 1 and int(start // 30) % 2 != 0)
            
            # Actually, let's keep it simpler: 
            # Track 1 (V2 in Premiere) is ALWAYS Cam A
            # Track 2 (V3 in Premiere) is ALWAYS Cam B
            # We will "enable/disable" by just not putting a clip if it's not the active camera
            # BUT the user wants a multi-cam stack, so we put BOTH but the editor picks.
            # I'll put BOTH in the stack, so they are perfectly synced.
            
            clip_start = start + offset
            clip_end = end + offset
            
            v_tracks += f"""                <clipitem id="clip_{track_idx}_{start}">
                    <name>{file}</name>
                    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
                    <start>{sec_to_frames(curr_time)}</start>
                    <end>{sec_to_frames(curr_time + dur)}</end>
                    <in>{sec_to_frames(clip_start)}</in>
                    <out>{sec_to_frames(clip_end)}</out>
                    <file id="file_{track_idx}">
                        <name>{file}</name>
                        <pathurl>file://localhost{quote(os.path.join(BASE, folder, file))}</pathurl>
                    </file>
                </clipitem>\n"""
            curr_time += dur
        v_tracks += "            </track>\n"

    xml_footer = """        </video>
        <audio>
            <track>
                <!-- Master Audio Track -->
"""
    # Audio Track (Master TASCAM)
    a_track = ""
    curr_time = 0.0
    for start, end, label in selects:
        dur = end - start
        a_track += f"""                <clipitem id="audio_{start}">
                    <name>{AUDIO[1]}</name>
                    <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
                    <start>{sec_to_frames(curr_time)}</start>
                    <end>{sec_to_frames(curr_time + dur)}</end>
                    <in>{sec_to_frames(start)}</in>
                    <out>{sec_to_frames(end)}</out>
                    <file id="file_audio">
                        <name>{AUDIO[1]}</name>
                        <pathurl>file://localhost{quote(os.path.join(BASE, AUDIO[0], AUDIO[1]))}</pathurl>
                    </file>
                </clipitem>\n"""
        curr_time += dur

    final_xml = xml_header + v_tracks + xml_footer + a_track + """            </track>
        </audio>
    </media>
</sequence>
</xmeml>"""
    
    with open(XML_OUT, "w") as f:
        f.write(final_xml)

print(f"Generating narrative selects XML: {XML_OUT}...")
generate_xml(SELECTS)
print("Done.")

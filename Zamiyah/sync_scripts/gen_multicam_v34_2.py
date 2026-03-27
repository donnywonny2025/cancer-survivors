#!/usr/bin/env python3
import subprocess, os
from urllib.parse import quote

"""
Zamiyah Multicam Golden Generator (v34.2)
Standard: UHD (3840x2160) | 29.97 DF | 30fps Absolute Anchor
Layout: V1/A1 (Cam A), V2/A2 (Cam B), A3 (TASCAM)
"""

BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
AUDIO_PATH = f"{BASE}/Audio/TASCAM_1087S34.wav"

# Forensic Offsets from xcorr_fast.py (Camera started BEFORE Master)
# These represent the time (in seconds) that the camera was running 
# before the TASCAM master recording began.
CAM_A_OFFSET = 63.2819
CAM_B_OFFSET = 75.7851

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())

def sec_to_frames_30(s):
    # Use 30fps as the Absolute Anchor to prevent drift
    # Premiere parses XMEML timebase/rate combinations. 
    # For a 29.97 DF sequence, we use 30 as timebase.
    return int(round(s * 30))

print("⚙️  STAGES: Metadata Audit...")
dur_a = get_duration(f"{BASE}/Footage/Cam A/C8826.MP4")
dur_b = get_duration(f"{BASE}/Footage/Cam B/C8890.MP4")
dur_t = get_duration(AUDIO_PATH)

print(f"  Cam A Duration: {dur_a:.2f}s")
print(f"  Cam B Duration: {dur_b:.2f}s")
print(f"  Tascam Duration: {dur_t:.2f}s")

# Calculate frames at 30fps
frames_a = sec_to_frames_30(dur_a)
frames_b = sec_to_frames_30(dur_b)
frames_t = sec_to_frames_30(dur_t)

# Calculate in-points (trims)
# Since camera started BEFORE master, In-point is the offset.
in_f_a = sec_to_frames_30(CAM_A_OFFSET)
in_f_b = sec_to_frames_30(CAM_B_OFFSET)

# Sequence length is the length of the master audio
seq_frames = frames_t

# Out-points (In + Sequence length)
out_f_a = in_f_a + seq_frames
out_f_b = in_f_b + seq_frames

# Ensure we don't exceed clip duration
out_f_a = min(out_f_a, frames_a)
out_f_b = min(out_f_b, frames_b)

# Recalculate end point if clip ends early
end_f_a = out_f_a - in_f_a
end_f_b = out_f_b - in_f_b

# Build XML
L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append('  <sequence>')
L.append('    <name>Zamiyah Multicam v34.2 (GOLDEN LAYOUT)</name>')
L.append(f'    <duration>{seq_frames}</duration>')
L.append('    <rate>')
L.append('      <timebase>30</timebase>')
L.append('      <ntsc>TRUE</ntsc>')
L.append('      <displayformat>DF</displayformat>')
L.append('    </rate>')
L.append('    <media>')
L.append('      <video>')
L.append('        <format>')
L.append('          <samplecharacteristics>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append('            <width>3840</width><height>2160</height>')
L.append('            <pixelaspect>square</pixelaspect>')
L.append('            <fielddominance>none</fielddominance>')
L.append('            <colormatrix>709</colormatrix>')
L.append('          </samplecharacteristics>')
L.append('        </format>')
L.append('        <track>')
L.append('          <name>V1: Cam A</name>')
L.append('          <clipitem id="v1_a">')
L.append('            <name>C8826.MP4</name>')
L.append(f'            <duration>{frames_a}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>0</start><end>{end_f_a}</end>')
L.append(f'            <in>{in_f_a}</in><out>{out_f_a}</out>')
L.append('            <enabled>TRUE</enabled>')
L.append('            <file id="f_a">')
L.append('                <name>C8826.MP4</name>')
L.append(f'                <pathurl>file://localhost{quote(os.path.join(BASE, "Footage/Cam A/C8826.MP4"))}</pathurl>')
L.append('                <media>')
L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
L.append('                </media>')
L.append('            </file>')
L.append('          </clipitem>')
L.append('        </track>')
L.append('        <track>')
L.append('          <name>V2: Cam B</name>')
L.append('          <clipitem id="v2_b">')
L.append('            <name>C8890.MP4</name>')
L.append(f'            <duration>{frames_b}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>0</start><end>{end_f_a}</end>') # Use Cam A duration as sync reference if needed, but normally end_f_b
L.append(f'            <in>{in_f_b}</in><out>{out_f_b}</out>')
L.append('            <enabled>TRUE</enabled>')
L.append('            <file id="f_b">')
L.append('                <name>C8890.MP4</name>')
L.append(f'                <pathurl>file://localhost{quote(os.path.join(BASE, "Footage/Cam B/C8890.MP4"))}</pathurl>')
L.append('                <media>')
L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
L.append('                </media>')
L.append('            </file>')
L.append('          </clipitem>')
L.append('        </track>')
L.append('      </video>')
L.append('      <audio>')
L.append('        <numchannels>3</numchannels>')
L.append('        <track>')
L.append('          <name>A1: Cam A Scratch</name>')
L.append('          <clipitem id="a1_a">')
L.append('            <name>C8826.MP4</name>')
L.append(f'            <duration>{frames_a}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>0</start><end>{end_f_a}</end>')
L.append(f'            <in>{in_f_a}</in><out>{out_f_a}</out>')
L.append('            <file id="f_a"/>')
L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
L.append('          </clipitem>')
L.append('        </track>')
L.append('        <track>')
L.append('          <name>A2: Cam B Scratch</name>')
L.append('          <clipitem id="a2_b">')
L.append('            <name>C8890.MP4</name>')
L.append(f'            <duration>{frames_b}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>0</start><end>{end_f_b}</end>')
L.append(f'            <in>{in_f_b}</in><out>{out_f_b}</out>')
L.append('            <file id="f_b"/>')
L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
L.append('          </clipitem>')
L.append('        </track>')
L.append('        <track>')
L.append('          <name>A3: TASCAM (Master)</name>')
L.append('          <clipitem id="a3_t">')
L.append('            <name>TASCAM_1087S34.wav</name>')
L.append(f'            <duration>{frames_t}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>0</start><end>{frames_t}</end>')
L.append(f'            <in>0</in><out>{frames_t}</out>')
L.append('            <file id="f_t">')
L.append('                <name>TASCAM_1087S34.wav</name>')
L.append(f'                <pathurl>file://localhost{quote(AUDIO_PATH)}</pathurl>')
L.append('                <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
L.append('            </file>')
L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
L.append('          </clipitem>')
L.append('        </track>')
L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')

out_path = f"{BASE}/Premiere/XML/Zamiyah_SYNC_FORENSIC_FINAL.xml"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    f.write("\n".join(L))

print(f"🚀 SUCCESS: Wrote {out_path}")

#!/usr/bin/env python3
"""
Zamiyah 3-Minute Narrative — Word-Level Precision Cut
Uses the PROVEN v34.2 Golden Layout XML pattern (L.append).
Onset detector refines all Whisper timestamps to true speech start/end.
"""

import os, sys
from urllib.parse import quote

# Import onset detector from framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../_multicam_framework'))
from onset_detector import find_onset, find_offset

BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
TASCAM = os.path.join(BASE, "Audio/TASCAM_1087S34.wav")
CAM_A_OFFSET = 63.2819
CAM_B_OFFSET = 75.7851
FPS = 30

def f(s):
    return int(round(s * FPS))

# ============================================================
# WORD-LEVEL PRECISE CUTS (verified from Whisper word timestamps)
# ============================================================
EDIT = [
    # IDENTITY: Audio spike at 1404.625s. Start 300ms before = 1404.325
    # Verified from waveform: room noise until 1404.5, "Hi" vocalization at 1404.625
    (23*60+24.0, 23*60+29.64, "IDENTITY", "B"),
    (60+23.00, 60+34.12, "PERSONALITY: dancing piano guitar", "A"),
    (60+35.62, 60+44.48, "PERSONALITY: bubbly kind", "A"),
    (44.92, 53.84, "SIGNS: subtle lymph nodes", "B"),
    (55.66, 66.30, "SIGNS: fatigued drained", "A"),
    (2*60+12.68, 2*60+18.26, "MOMENT: always active dance", "A"),
    (2*60+18.68, 2*60+21.76, "MOMENT: sleeping more weird", "A"),
    (2*60+22.82, 2*60+27.12, "MOMENT: mom noticed", "A"),
    (2*60+29.48, 2*60+35.30, "MOMENT: knew something wasn't right", "B"),
    (4*60+15.60, 4*60+26.94, "COST: how much life you lose", "A"),
    (4*60+28.84, 4*60+41.00, "COST: confidence self-identity", "A"),
    (6*60+59.74, 7*60+5.46, "POWER: catch it early", "A"),
    (7*60+8.82, 7*60+19.68, "POWER: fear is normal taking power back", "A"),
    (7*60+19.68, 7*60+35.86, "POWER: knowing is better", "B"),
    (8*60+30.88, 8*60+35.70, "CHANGE: changed everything", "A"),
    (8*60+37.78, 8*60+43.62, "CHANGE: small days", "B"),
    (8*60+46.38, 8*60+56.02, "CHANGE: value rest joy people", "A"),
    (8*60+56.92, 9*60+0.34, "CHANGE: learned about myself", "A"),
    (9*60+7.20, 9*60+13.00, "CHANGE: grown as person", "A"),
    (12*60+56.92, 13*60+5.86, "MUSIC: new things sew", "A"),
    (13*60+41.82, 13*60+47.74, "MUSIC: write my own music", "A"),
    (13*60+48.72, 13*60+55.74, "MUSIC: express feelings emotions", "A"),
    (21*60+43.14, 21*60+52.86, "NURSE: love so dearly had cancer", "B"),
    (21*60+52.86, 22*60+9.52, "NURSE: somebody understands you", "A"),
    (22*60+10.96, 22*60+17.32, "NURSE: appreciate her so much", "A"),
    (11*60+15.00, 11*60+38.96, "CLOSE: stay confident be yourself", "A"),
    (11*60+38.96, 11*60+47.22, "CLOSE: stay strong break through", "A"),
    (11*60+57.28, 11*60+59.86, "CLOSE: your journey is your journey", "A"),
    (12*60+0.96, 12*60+6.32, "CLOSE: break through anything", "B"),
]

# ============================================================
# Build using the PROVEN v34.2 L.append pattern
# Onset detector corrects all Whisper timestamps first
# ============================================================

cam_a_url = f"file://localhost{quote(os.path.join(BASE, 'Footage/Cam A/C8826.MP4'))}"
cam_b_url = f"file://localhost{quote(os.path.join(BASE, 'Footage/Cam B/C8890.MP4'))}"
tascam_url = f"file://localhost{quote(os.path.join(BASE, 'Audio/TASCAM_1087S34.wav'))}"

# Pre-compute all clips with onset-corrected timestamps
print("🔍 Running onset detection on all cut points...")
tl = 0
clips = []
for i, (start, end, label, cam) in enumerate(EDIT):
    # Correct Whisper timestamps using audio energy analysis
    true_start = find_onset(TASCAM, start)
    true_end = find_offset(TASCAM, end)
    
    dur_f = f(true_end - true_start)
    tl_s = tl
    tl_e = tl + dur_f
    in_a = f(true_start + CAM_A_OFFSET)
    out_a = f(true_end + CAM_A_OFFSET)
    in_b = f(true_start + CAM_B_OFFSET)
    out_b = f(true_end + CAM_B_OFFSET)
    in_t = f(true_start)
    out_t = f(true_end)
    
    correction_ms = (start - true_start) * 1000
    clips.append({
        'i': i, 'tl_s': tl_s, 'tl_e': tl_e, 'dur_f': dur_f,
        'in_a': in_a, 'out_a': out_a,
        'in_b': in_b, 'out_b': out_b,
        'in_t': in_t, 'out_t': out_t,
        'cam': cam, 'label': label,
        'onset_correction_ms': correction_ms,
        'true_start': true_start, 'true_end': true_end
    })
    tl = tl_e

total_f = tl

# BUILD XML
L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append('  <sequence>')
L.append('    <name>Zamiyah — 3min Narrative (Word-Level)</name>')
L.append(f'    <duration>{total_f}</duration>')
L.append('    <rate>')
L.append('      <timebase>30</timebase>')
L.append('      <ntsc>TRUE</ntsc>')
L.append('      <displayformat>DF</displayformat>')
L.append('    </rate>')
L.append('    <media>')

# === VIDEO ===
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

# V1: Cam A — file definition + all clips
L.append('        <track>')
L.append('          <name>V1: Cam A</name>')
# File definition clipitem (first clip defines the file)
L.append('          <clipitem id="v1_filedef">')
L.append('            <name>C8826.MP4</name>')
L.append(f'            <duration>{clips[0]["dur_f"]}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>{clips[0]["tl_s"]}</start><end>{clips[0]["tl_e"]}</end>')
L.append(f'            <in>{clips[0]["in_a"]}</in><out>{clips[0]["out_a"]}</out>')
L.append('            <enabled>TRUE</enabled>')
L.append('            <file id="f_a">')
L.append('                <name>C8826.MP4</name>')
L.append(f'                <pathurl>{cam_a_url}</pathurl>')
L.append('                <media>')
L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
L.append('                </media>')
L.append('            </file>')
L.append('          </clipitem>')
# Remaining V1 clips
for c in clips[1:]:
    L.append(f'          <clipitem id="v1_{c["i"]}">')
    L.append('            <name>C8826.MP4</name>')
    L.append(f'            <duration>{c["dur_f"]}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_a"]}</in><out>{c["out_a"]}</out>')
    L.append('            <enabled>TRUE</enabled>')
    L.append('            <file id="f_a"/>')
    L.append('          </clipitem>')
L.append('        </track>')

# V2: Cam B — file definition + only active B clips
L.append('        <track>')
L.append('          <name>V2: Cam B</name>')
b_clips = [c for c in clips if c['cam'] == 'B']
if b_clips:
    # First B clip defines the file
    bc = b_clips[0]
    L.append(f'          <clipitem id="v2_{bc["i"]}">')
    L.append('            <name>C8890.MP4</name>')
    L.append(f'            <duration>{bc["dur_f"]}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{bc["tl_s"]}</start><end>{bc["tl_e"]}</end>')
    L.append(f'            <in>{bc["in_b"]}</in><out>{bc["out_b"]}</out>')
    L.append('            <enabled>TRUE</enabled>')
    L.append('            <file id="f_b">')
    L.append('                <name>C8890.MP4</name>')
    L.append(f'                <pathurl>{cam_b_url}</pathurl>')
    L.append('                <media>')
    L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
    L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
    L.append('                </media>')
    L.append('            </file>')
    L.append('          </clipitem>')
    for bc in b_clips[1:]:
        L.append(f'          <clipitem id="v2_{bc["i"]}">')
        L.append('            <name>C8890.MP4</name>')
        L.append(f'            <duration>{bc["dur_f"]}</duration>')
        L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'            <start>{bc["tl_s"]}</start><end>{bc["tl_e"]}</end>')
        L.append(f'            <in>{bc["in_b"]}</in><out>{bc["out_b"]}</out>')
        L.append('            <enabled>TRUE</enabled>')
        L.append('            <file id="f_b"/>')
        L.append('          </clipitem>')
L.append('        </track>')
L.append('      </video>')

# === AUDIO ===
L.append('      <audio>')
L.append('        <numchannels>3</numchannels>')

# A1: Cam A audio
L.append('        <track>')
L.append('          <name>A1: Cam A Scratch</name>')
for c in clips:
    L.append(f'          <clipitem id="a1_{c["i"]}">')
    L.append('            <name>C8826.MP4</name>')
    L.append(f'            <duration>{c["dur_f"]}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_a"]}</in><out>{c["out_a"]}</out>')
    L.append('            <enabled>FALSE</enabled>')
    L.append('            <file id="f_a"/>')
    L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
    L.append('          </clipitem>')
L.append('        </track>')

# A2: Cam B audio
L.append('        <track>')
L.append('          <name>A2: Cam B Scratch</name>')
for c in clips:
    L.append(f'          <clipitem id="a2_{c["i"]}">')
    L.append('            <name>C8890.MP4</name>')
    L.append(f'            <duration>{c["dur_f"]}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_b"]}</in><out>{c["out_b"]}</out>')
    L.append('            <enabled>FALSE</enabled>')
    L.append('            <file id="f_b"/>')
    L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
    L.append('          </clipitem>')
L.append('        </track>')

# A3: TASCAM master
L.append('        <track>')
L.append('          <name>A3: TASCAM (Master)</name>')
# First clip defines the file
L.append(f'          <clipitem id="a3_0">')
L.append('            <name>TASCAM_1087S34.wav</name>')
L.append(f'            <duration>{clips[0]["dur_f"]}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>{clips[0]["tl_s"]}</start><end>{clips[0]["tl_e"]}</end>')
L.append(f'            <in>{clips[0]["in_t"]}</in><out>{clips[0]["out_t"]}</out>')
L.append('            <file id="f_t">')
L.append('                <name>TASCAM_1087S34.wav</name>')
L.append(f'                <pathurl>{tascam_url}</pathurl>')
L.append('                <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
L.append('            </file>')
L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
L.append('          </clipitem>')
for c in clips[1:]:
    L.append(f'          <clipitem id="a3_{c["i"]}">')
    L.append('            <name>TASCAM_1087S34.wav</name>')
    L.append(f'            <duration>{c["dur_f"]}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_t"]}</in><out>{c["out_t"]}</out>')
    L.append('            <file id="f_t"/>')
    L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
    L.append('          </clipitem>')
L.append('        </track>')

L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')

# Write
out_path = os.path.join(BASE, "Premiere/XML/Zamiyah_3min_Narrative_v4.xml")
with open(out_path, "w") as fout:
    fout.write("\n".join(L))

m, s = divmod(total_f / FPS, 60)
print(f"✅ Zamiyah 3min Narrative (Word-Level Precision)")
print(f"   Duration: {int(m)}:{s:04.1f} | {len(EDIT)} segments")
print(f"   V1: {len(clips)} Cam A clips | V2: {len(b_clips)} Cam B switches")
print(f"   → {out_path}")

# EDL
print(f"\n{'='*80}")
print("EDIT DECISION LIST (with onset corrections)")
print(f"{'='*80}")
for c in clips:
    ms, ss = divmod(c['true_start'], 60)
    me, se = divmod(c['true_end'], 60)
    mt, st = divmod(c['tl_s'] / FPS, 60)
    corr = c['onset_correction_ms']
    print(f"  {int(mt):02d}:{st:04.1f} | SRC [{int(ms):02d}:{ss:04.1f}-{int(me):02d}:{se:04.1f}] {c['dur_f']/FPS:5.1f}s | Cam {c['cam']} | onset:{corr:+.0f}ms | {c['label']}")

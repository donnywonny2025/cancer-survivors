#!/usr/bin/env python3
"""
Zamiyah 3-Minute Narrative — v10 Tighter Cut (Intelligent Cut Agent)
Uses WhisperX forced-aligned word timestamps (wav2vec2).
150ms pad before first word, 100ms pad after last word.
No onset detector. No hacks. Just precise word boundaries.
"""

import os
import sys
from urllib.parse import quote

BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
CAM_A_OFFSET = 63.2819
CAM_B_OFFSET = 75.7851
FPS = 30
# NTSC frame duration: each frame = 1001/30000 seconds
# seconds → frames: seconds * 30000/1001
# This is CRITICAL: using 30 instead of 29.97 causes 1ms drift per second
# At 23:24 (1404s), that's a 1.4 SECOND error!

def f(s):
    """Convert seconds to NTSC frame number (29.97fps)."""
    return int(round(s * 30000 / 1001))

# ============================================================
# WHISPERX FORCED-ALIGNED CUT POINTS
# Source: Master_S34_Transcript_WhisperX.json (wav2vec2 alignment)
# First word start - 150ms = in-point
# Last word end + 100ms = out-point
# ============================================================
EDIT = [
    # v10: Tighter cut — redundant segments removed per Intelligent Cut rules
    # 20 segments, ~3:03 — full arc preserved
    #
    # (in_point, out_point, label, camera)
    (1404.337, 1409.673, "IDENTITY", "B"),                              # Hi, my name is Zamiyah
    (83.762, 96.912, "PERSONALITY: dancing piano guitar", "A"),          # Trimmed head, extended to 'very musical person.'
    # CUT: PERSONALITY2 — redundant with above
    (45.156, 53.977, "SIGNS: subtle lymph nodes", "B"),                  # First symptoms
    (55.669, 66.312, "SIGNS: fatigued drained", "A"),                    # How it felt
    (132.925, 138.662, "MOMENT: always active dance", "A"),              # She was active
    # CUT: MOMENT2+3 — "sleeping more" and "mom noticed" implied by MOMENT1+4
    (150.429, 155.485, "MOMENT: knew something wasn't right", "B"),      # Turning point
    (256.837, 265.139, "COST: how much life you lose", "A"),             # Clean take, no stumble
    (277.587, 281.222, "COST: confidence self-identity", "A"),           # Trimmed: skip 'routines...Sorry.' false start
    # CUT: POWER1 — "catch it early" covered by POWER2
    (429.395, 439.795, "POWER: fear is normal taking power back", "A"),  # Taking power back
    (440.346, 455.715, "POWER: knowing is better", "B"),                 # Knowledge > fear
    # CUT: CHANGE1 — "changed everything" too generic
    (517.959, 522.837, "CHANGE: small days", "B"),                       # Finding joy
    (526.803, 536.046, "CHANGE: value rest joy people", "A"),            # New values
    # CUT: CHANGE4 — "learned about myself" covered by CHANGE5
    (547.472, 552.569, "CHANGE: grown as person", "A"),                  # Growth
    # CUT: MUSIC1 — "new things sew" weakest of the three
    (821.965, 827.722, "MUSIC: write my own music", "A"),                # Trimmed: skip 'Sorry.'
    (828.253, 835.933, "MUSIC: express feelings emotions", "A"),         # Through music
    (1303.394, 1312.945, "NURSE: love so dearly had cancer", "B"),       # Trimmed: skip 'So'
    (1312.374, 1329.527, "NURSE: somebody understands you", "A"),        # Connection
    # CUT: NURSE3 — "appreciate her" covered by NURSE2
    (680.163, 695.779, "CLOSE: stay confident be yourself", "A"),        # Trimmed: skip 'Well,' + interviewer Q + 'Okay.'
    (717.756, 720.009, "CLOSE: your journey is your journey", "A"),      # Ownership
    (721.120, 725.236, "CLOSE: break through anything", "B"),            # Final word
]

# ============================================================
# Build using the PROVEN v34.2 L.append pattern
# WhisperX timestamps — no onset detector needed
# ============================================================

cam_a_url = f"file://localhost{quote(os.path.join(BASE, 'Footage/Cam A/C8826.MP4'))}"
cam_b_url = f"file://localhost{quote(os.path.join(BASE, 'Footage/Cam B/C8890.MP4'))}"
tascam_url = f"file://localhost{quote(os.path.join(BASE, 'Audio/TASCAM_1087S34.wav'))}"

# Total file durations in NTSC frames (seconds * 30000/1001)
CAM_A_TOTAL_F = int(round(1493.993 * 30000 / 1001))   # = 44775
CAM_B_TOTAL_F = int(round(1511.510 * 30000 / 1001))   # = 45300
TASCAM_TOTAL_F = int(round(1429.296 * 30000 / 1001))   # = 42836

# Premiere clip label colors (track-based)
COLOR_CAM_A = "Cerulean"    # V1 / A1 — blue
COLOR_CAM_B = "Mango"       # V2 / A2 — orange
COLOR_TASCAM = "Forest"     # A3 — green

# Narrative arc colors (per-section) — used for VIDEO clip labels
ARC_COLORS = {
    "IDENTITY":    "Iris",
    "PERSONALITY": "Lavender",
    "SIGNS":       "Rose",
    "MOMENT":      "Rose",
    "COST":        "Purple",
    "POWER":       "Caribbean",
    "CHANGE":      "Forest",
    "MUSIC":       "Cerulean",
    "NURSE":       "Mango",
    "CLOSE":       "Yellow",
}

def arc_color(label):
    """Get Premiere color for a clip's narrative section."""
    section = label.split(":")[0].strip()
    return ARC_COLORS.get(section, "Mango")

# Pre-compute all clips — straight timestamps, no processing
tl = 0
clips = []
for i, (start, end, label, cam) in enumerate(EDIT):
    dur_f = f(end - start)
    tl_s = tl
    tl_e = tl + dur_f
    in_a = f(start + CAM_A_OFFSET)
    out_a = f(end + CAM_A_OFFSET)
    in_b = f(start + CAM_B_OFFSET)
    out_b = f(end + CAM_B_OFFSET)
    in_t = f(start)
    out_t = f(end)
    clips.append({
        'i': i, 'tl_s': tl_s, 'tl_e': tl_e, 'dur_f': dur_f,
        'in_a': in_a, 'out_a': out_a,
        'in_b': in_b, 'out_b': out_b,
        'in_t': in_t, 'out_t': out_t,
        'cam': cam, 'label': label,
        'src_start': start, 'src_end': end
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

# V1: Cam A — ALL segments, enabled when cam='A', disabled when cam='B'
L.append('        <track>')
L.append('          <name>V1: Cam A</name>')
# First clip defines the Cam A file
c0 = clips[0]
enabled_a = 'TRUE' if c0['cam'] == 'A' else 'FALSE'
L.append(f'          <clipitem id="v1_0">')
L.append('            <name>C8826.MP4</name>')
L.append(f'            <duration>{CAM_A_TOTAL_F}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>{c0["tl_s"]}</start><end>{c0["tl_e"]}</end>')
L.append(f'            <in>{c0["in_a"]}</in><out>{c0["out_a"]}</out>')
L.append(f'            <enabled>{enabled_a}</enabled>')
L.append('            <file id="f_a">')
L.append('                <name>C8826.MP4</name>')
L.append(f'                <pathurl>{cam_a_url}</pathurl>')
L.append('                <media>')
L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
L.append('                </media>')
L.append('            </file>')
L.append(f'            <labels><label2>{arc_color(c0["label"])}</label2></labels>')
L.append('          </clipitem>')
for c in clips[1:]:
    enabled_a = 'TRUE' if c['cam'] == 'A' else 'FALSE'
    L.append(f'          <clipitem id="v1_{c["i"]}">')
    L.append('            <name>C8826.MP4</name>')
    L.append(f'            <duration>{CAM_A_TOTAL_F}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_a"]}</in><out>{c["out_a"]}</out>')
    L.append(f'            <enabled>{enabled_a}</enabled>')
    L.append('            <file id="f_a"/>')
    L.append(f'            <labels><label2>{arc_color(c["label"])}</label2></labels>')
    L.append('          </clipitem>')
L.append('        </track>')

# V2: Cam B — ALL segments, enabled when cam='B', disabled when cam='A'
L.append('        <track>')
L.append('          <name>V2: Cam B</name>')
# First clip defines the Cam B file
enabled_b = 'TRUE' if c0['cam'] == 'B' else 'FALSE'
L.append(f'          <clipitem id="v2_0">')
L.append('            <name>C8890.MP4</name>')
L.append(f'            <duration>{CAM_B_TOTAL_F}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>{c0["tl_s"]}</start><end>{c0["tl_e"]}</end>')
L.append(f'            <in>{c0["in_b"]}</in><out>{c0["out_b"]}</out>')
L.append(f'            <enabled>{enabled_b}</enabled>')
L.append('            <file id="f_b">')
L.append('                <name>C8890.MP4</name>')
L.append(f'                <pathurl>{cam_b_url}</pathurl>')
L.append('                <media>')
L.append('                    <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>')
L.append('                    <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
L.append('                </media>')
L.append('            </file>')
L.append(f'            <labels><label2>{arc_color(c0["label"])}</label2></labels>')
L.append('          </clipitem>')
for c in clips[1:]:
    enabled_b = 'TRUE' if c['cam'] == 'B' else 'FALSE'
    L.append(f'          <clipitem id="v2_{c["i"]}">')
    L.append('            <name>C8890.MP4</name>')
    L.append(f'            <duration>{CAM_B_TOTAL_F}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_b"]}</in><out>{c["out_b"]}</out>')
    L.append(f'            <enabled>{enabled_b}</enabled>')
    L.append('            <file id="f_b"/>')
    L.append(f'            <labels><label2>{arc_color(c["label"])}</label2></labels>')
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
    L.append(f'            <duration>{CAM_A_TOTAL_F}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_a"]}</in><out>{c["out_a"]}</out>')
    L.append('            <enabled>FALSE</enabled>')
    L.append('            <file id="f_a"/>')
    L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
    L.append(f'            <labels><label2>{COLOR_CAM_A}</label2></labels>')
    L.append('          </clipitem>')
L.append('        </track>')

# A2: Cam B audio
L.append('        <track>')
L.append('          <name>A2: Cam B Scratch</name>')
for c in clips:
    L.append(f'          <clipitem id="a2_{c["i"]}">')
    L.append('            <name>C8890.MP4</name>')
    L.append(f'            <duration>{CAM_B_TOTAL_F}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_b"]}</in><out>{c["out_b"]}</out>')
    L.append('            <enabled>FALSE</enabled>')
    L.append('            <file id="f_b"/>')
    L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
    L.append(f'            <labels><label2>{COLOR_CAM_B}</label2></labels>')
    L.append('          </clipitem>')
L.append('        </track>')
L.append('        <track>')
L.append('          <name>A3: TASCAM (Master)</name>')
# First clip defines the file
L.append(f'          <clipitem id="a3_0">')
L.append('            <name>TASCAM_1087S34.wav</name>')
L.append(f'            <duration>{TASCAM_TOTAL_F}</duration>')
L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
L.append(f'            <start>{clips[0]["tl_s"]}</start><end>{clips[0]["tl_e"]}</end>')
L.append(f'            <in>{clips[0]["in_t"]}</in><out>{clips[0]["out_t"]}</out>')
L.append('            <file id="f_t">')
L.append('                <name>TASCAM_1087S34.wav</name>')
L.append(f'                <pathurl>{tascam_url}</pathurl>')
L.append('                <media><audio><samplecharacteristics><depth>24</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
L.append('            </file>')
L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
L.append(f'            <labels><label2>{COLOR_TASCAM}</label2></labels>')
L.append('          </clipitem>')
for c in clips[1:]:
    L.append(f'          <clipitem id="a3_{c["i"]}">')
    L.append('            <name>TASCAM_1087S34.wav</name>')
    L.append(f'            <duration>{TASCAM_TOTAL_F}</duration>')
    L.append('            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{c["tl_s"]}</start><end>{c["tl_e"]}</end>')
    L.append(f'            <in>{c["in_t"]}</in><out>{c["out_t"]}</out>')
    L.append('            <file id="f_t"/>')
    L.append('            <sourcetrack><type>audio</type><trackindex>1</trackindex></sourcetrack>')
    L.append(f'            <labels><label2>{COLOR_TASCAM}</label2></labels>')
    L.append('          </clipitem>')
L.append('        </track>')

L.append('      </audio>')
L.append('    </media>')
L.append('  </sequence>')
L.append('</xmeml>')
# ============================================================
# STRUCTURAL VALIDATION — catch regressions before writing
# ============================================================
xml_str = "\n".join(L)
errors = []

# Tag balance checks
for tag in ['track', 'clipitem', 'file', 'media', 'sequence', 'xmeml']:
    opens = xml_str.count(f'<{tag}>') + xml_str.count(f'<{tag} ')
    closes = xml_str.count(f'</{tag}>')
    refs = xml_str.count(f'<{tag} id=') + xml_str.count(f'<{tag} id=')
    if tag in ('file',):  # files have self-closing refs like <file id="f_a"/>
        continue
    if opens != closes:
        errors.append(f"⛔ TAG MISMATCH: <{tag}> has {opens} opens but {closes} closes")

# Track count check
track_names = [l for l in L if '<name>V1' in l or '<name>V2' in l or '<name>A1' in l or '<name>A2' in l or '<name>A3' in l]
if len(track_names) != 5:
    errors.append(f"⛔ TRACK COUNT: Expected 5 tracks (V1,V2,A1,A2,A3), found {len(track_names)}")

# Clip count check per track
for track_id in ['v1_', 'v2_', 'a1_', 'a2_', 'a3_']:
    count = xml_str.count(f'clipitem id="{track_id}')
    if count != len(clips):
        errors.append(f"⛔ CLIP COUNT: {track_id} has {count} clips, expected {len(clips)}")

if errors:
    print("❌ VALIDATION FAILED — XML NOT WRITTEN")
    for e in errors:
        print(f"   {e}")
    sys.exit(1)

# Write
out_path = os.path.join(BASE, "Premiere/XML/Zamiyah_3min_Narrative_v13.xml")
with open(out_path, "w") as fout:
    fout.write(xml_str)

m, s = divmod(total_f * 1001 / 30000, 60)
b_count = sum(1 for c in clips if c['cam'] == 'B')
print(f"✅ Zamiyah 3min Narrative (Word-Level Precision)")
print(f"   Duration: {int(m)}:{s:04.1f} | {len(EDIT)} segments")
print(f"   V1: {len(clips)} Cam A clips | V2: {len(clips)} Cam B clips ({b_count} active)")
print(f"   → {out_path}")

# EDL
print(f"\n{'='*80}")
print("EDIT DECISION LIST (WhisperX forced-aligned)")
print(f"{'='*80}")
for c in clips:
    ms, ss = divmod(c['src_start'], 60)
    me, se = divmod(c['src_end'], 60)
    mt, st = divmod(c['tl_s'] / FPS, 60)
    print(f"  {int(mt):02d}:{st:04.1f} | SRC [{int(ms):02d}:{ss:04.1f}-{int(me):02d}:{se:04.1f}] {c['dur_f']/FPS:5.1f}s | Cam {c['cam']} | {c['label']}")

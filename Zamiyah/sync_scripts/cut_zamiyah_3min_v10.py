#!/usr/bin/env python3
"""
Zamiyah 3-Minute Narrative — v10 Tighter Cut (Intelligent Cut Agent)
Uses WhisperX forced-aligned word timestamps (wav2vec2).
150ms pad before first word, 100ms pad after last word.
No onset detector. No hacks. Just precise word boundaries.
"""

import json
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
    # v15: Deepgram verbatim transcript (47 fillers), gap removal + filler trimming
    # Keeps cancer context immediate: "diagnosed with lymphoma" → "signs were subtle"
    # PERSONALITY comes after MOMENT as contrast: "but here's who I really am"
    # 20 segments, ~2:48
    #
    # (in_point, out_point, label, camera)
    (1404.337, 1409.673, "IDENTITY", "B"),                              # "diagnosed with hodgkin's lymphoma"
    (45.156, 53.977, "SIGNS: subtle lymph nodes", "B"),                  # filler auto-split at um@49.3
    (55.669, 62.010, "SIGNS: fatigued drained", "A"),                    # ends on 'time' — complete thought
    (132.890, 138.315, "MOMENT: always active dance", "A"),              # starts after um, ends complete
    (150.429, 155.485, "MOMENT: knew something wasn't right", "B"),      # clean
    (83.762, 96.912, "PERSONALITY: dancing piano guitar", "A"),          # fillers auto-handled
    (256.837, 265.139, "COST: how much life you lose", "A"),             # clean
    (277.587, 281.222, "COST: confidence self-identity", "A"),           # clean
    (429.395, 439.795, "POWER: fear is normal taking power back", "A"),  # clean
    (440.346, 455.715, "POWER: knowing is better", "B"),                 # fillers auto-handled
    (517.959, 522.787, "CHANGE: small days", "B"),                       # clean
    (526.903, 534.535, "CHANGE: value rest joy people", "A"),            # ends on 'situation' not 'and'
    (547.070, 553.010, "CHANGE: grown as person", "A"),                  # extends to 'person'
    (821.920, 824.900, "MUSIC: write my own music", "A"),                # ends on 'well' — before um@825.7
    (828.615, 835.933, "MUSIC: express feelings emotions", "A"),         # starts after leading um
    (1303.394, 1312.584, "NURSE: love so dearly had cancer", "B"),       # clean
    (1313.517, 1329.527, "NURSE: somebody understands you", "A"),        # clean
    (680.163, 695.779, "CLOSE: stay confident be yourself", "A"),        # clean
    (717.756, 720.009, "CLOSE: your journey is your journey", "A"),      # clean
    (721.120, 725.535, "CLOSE: break through anything", "B"),            # extended to 'life'
]

# ============================================================
# AUTO GAP REMOVAL — cut fillers by skipping word gaps
# ============================================================
# Any gap > GAP_THRESHOLD between consecutive words = filler territory.
# Split the segment at those gaps so the edit jumps over the "um."
# This is the intelligence layer: Whisper can't transcribe fillers,
# but it CAN tell us where the words AREN'T.

GAP_THRESHOLD = 0.80  # seconds — natural pauses are 0.3-0.6s, fillers are 0.8s+

def _load_words():
    """Load word-level timestamps — prefer Deepgram (has fillers) over WhisperX."""
    # Deepgram transcript has 47 fillers; WhisperX has 1
    dg_path = os.path.join(BASE, "Master_S34_Transcript_Deepgram.json")
    wx_path = os.path.join(BASE, "Master_S34_Transcript_WhisperX.json")
    
    path = dg_path if os.path.exists(dg_path) else wx_path
    if not os.path.exists(path):
        return []
    
    source = "Deepgram" if "Deepgram" in path else "WhisperX"
    with open(path) as fp:
        data = json.load(fp)
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            if "start" in w:
                words.append(w)
    words.sort(key=lambda w: w["start"])
    print(f"📝 Transcript: {source} ({len(words)} words)", flush=True)
    return words

def remove_gaps(edit_list, words, threshold=GAP_THRESHOLD):
    """Split segments at word gaps to remove fillers.
    
    Only splits when the word BEFORE the gap ends with terminal punctuation
    (period, !, ?) — meaning it's a complete thought, not a mid-sentence pause.
    """
    if not words:
        return edit_list
    
    cleaned = []
    gaps_removed = 0
    
    for entry in edit_list:
        start, end, label, cam = entry[0], entry[1], entry[2], entry[3]
        
        # Find words in this segment
        seg_words = [w for w in words if start - 0.15 <= w["start"] <= end + 0.05]
        if not seg_words:
            cleaned.append(entry)
            continue
        
        # Walk through words, split at gaps
        sub_start = start
        sub_words = []
        
        for i, w in enumerate(seg_words):
            if sub_words:
                last_word = sub_words[-1].get("word", "")
                gap = w["start"] - sub_words[-1].get("end", sub_words[-1]["start"])
                
                # Only split if: gap is large AND previous word ends a sentence
                # For very large gaps (>1.5s), split regardless — always a filler
                ends_sentence = last_word.rstrip().endswith((".", "!", "?"))
                large_gap = gap > 1.5  # 1.5s+ gap = always split
                
                if gap > threshold and (ends_sentence or large_gap):
                    # Complete thought + big gap = safe to split (filler in between)
                    sub_end = sub_words[-1].get("end", sub_words[-1]["start"]) + 0.10
                    cleaned.append((sub_start, sub_end, label, cam))
                    gaps_removed += 1
                    sub_start = w["start"] - 0.15
                    sub_words = []
            
            sub_words.append(w)
        
        # Add the last sub-clip
        if sub_words:
            cleaned.append((sub_start, end, label, cam))
    
    if gaps_removed > 0:
        print(f"\n🔪 GAP REMOVAL: Cut {gaps_removed} filler gaps (>{threshold}s after sentence ends)")
        print(f"   {len(edit_list)} segments → {len(cleaned)} segments")
    else:
        print(f"\n✅ GAP REMOVAL: No filler gaps found (>{threshold}s)")
    
    return cleaned

def intelligent_filler_removal(edit_list, words):
    """Context-aware filler removal using Deepgram transcript.
    
    Rules:
    1. SPLIT at standalone fillers (um/uh between sentences) — skip the filler
    2. TRIM trailing fillers at segment tails
    3. NEVER cut connective words (and, but, so, because) even after pauses
    4. KEEP natural breathing pauses <0.5s — they add emotional weight
    5. DROP micro-clips <0.5s that result from splits
    """
    filler_set = {"um", "uh", "ums", "uhs", "hmm", "mhm", "mmm", "ah", "hm", "mm"}
    connectives = {"and", "but", "so", "because", "or", "like", "then", "also", "just"}
    
    result = []
    splits_made = 0
    trims_made = 0
    
    for (start, end, label, cam) in edit_list:
        # Get words in this segment
        seg_words = [w for w in words if w["start"] >= start - 0.1 and w["end"] <= end + 0.1]
        if not seg_words:
            result.append((start, end, label, cam))
            continue
        
        # Walk through words, building sub-clips
        sub_clips = []
        clip_start = start
        clip_words = []
        
        for i, w in enumerate(seg_words):
            word_clean = w["word"].lower().strip(".,!? ")
            is_filler = word_clean in filler_set
            
            if is_filler:
                # Check context: is this filler between two thoughts?
                has_words_before = len(clip_words) > 0
                has_words_after = i < len(seg_words) - 1
                
                if has_words_before and has_words_after:
                    last_real = clip_words[-1]
                    last_clean = last_real["word"].lower().strip(".,!? ")
                    
                    if last_clean in connectives:
                        # "but um I like..." → keep thought flowing
                        # Skip the filler, stitch the next word right after
                        # Don't add to sub_clips — just advance past the filler
                        pass  # filler skipped, next word joins clip_words naturally
                    else:
                        # Standalone filler between completed thoughts — SPLIT
                        clip_end = last_real["end"] + 0.10
                        sub_clips.append((clip_start, clip_end, label, cam))
                        
                        next_word = seg_words[i + 1]
                        clip_start = next_word["start"] - 0.15
                        clip_words = []
                        splits_made += 1
                elif has_words_before and not has_words_after:
                    # Trailing filler — trim the out-point before it
                    last_real = clip_words[-1]
                    clip_end = last_real["end"] + 0.10
                    sub_clips.append((clip_start, clip_end, label, cam))
                    clip_words = []
                    clip_start = None
                    trims_made += 1
                # If filler is at the start with no words before, skip it silently
                elif not has_words_before and has_words_after:
                    next_word = seg_words[i + 1]
                    clip_start = next_word["start"] - 0.15
                    trims_made += 1
            else:
                clip_words.append(w)
        
        # Flush remaining words
        if clip_words and clip_start is not None:
            last_real = clip_words[-1]
            clip_end = min(last_real["end"] + 0.10, end)
            sub_clips.append((clip_start, clip_end, label, cam))
        
        # Filter out micro-clips <0.5s (they sound like glitches)
        for clip in sub_clips:
            duration = clip[1] - clip[0]
            if duration >= 0.5:
                result.append(clip)
            else:
                splits_made -= 1  # Don't count dropped micro-clips as splits
    
    if splits_made or trims_made:
        print(f"\n🧠 INTELLIGENT FILLER REMOVAL:")
        if splits_made:
            print(f"   Split {splits_made} standalone fillers between thoughts")
        if trims_made:
            print(f"   Trimmed {trims_made} edge fillers (leading/trailing)")
        print(f"   {len(edit_list)} segments → {len(result)} segments")
    else:
        print(f"\n✅ FILLER CHECK: No fillers found in edit segments")
    
    return result

# Apply intelligent filler removal
ALL_WORDS = _load_words()
EDIT = intelligent_filler_removal(EDIT, ALL_WORDS)

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

# ============================================================
# NARRATIVE LINT — Editorial Intelligence Pre-Flight
# ============================================================
try:
    sys.path.insert(0, os.path.join(os.path.dirname(BASE), "_multicam_framework"))
    from narrative_lint import lint_edit_list, print_lint_report

    # Load transcript words for sentence completion checks
    transcript_path = os.path.join(BASE, "Master_S34_Transcript_WhisperX.json")
    lint_words = []
    if os.path.exists(transcript_path):
        with open(transcript_path) as tf:
            tdata = json.load(tf)
        for tseg in tdata.get("segments", []):
            for tw in tseg.get("words", []):
                if "start" in tw:
                    lint_words.append(tw)
        lint_words.sort(key=lambda w: w["start"])

    lint_warnings = lint_edit_list(EDIT, lint_words if lint_words else None)
    lint_ok = print_lint_report(lint_warnings)
except ImportError:
    print("⚠️  narrative_lint.py not found — skipping editorial checks")
    lint_ok = True
except Exception as lint_err:
    print(f"⚠️  Narrative lint error: {lint_err}")
    lint_ok = True

# Write
out_path = os.path.join(BASE, "Premiere/XML/Zamiyah_3min_Narrative_v16.xml")
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

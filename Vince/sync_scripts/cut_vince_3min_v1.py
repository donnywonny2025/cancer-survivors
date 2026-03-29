#!/usr/bin/env python3
"""
Vince 3-Minute Narrative — Word-Anchor Pipeline
Uses the same proven system as Zamiyah v22.
"""
import json, os, math
from urllib.parse import quote

BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Vince"

# ============================================================
# EDIT ANCHORS — (first_word_start, "first_word", last_word_start, "last_word", label, cam)
# ============================================================
EDIT_ANCHORS = [
    # IDENTITY — "my name is vince, i'm battling stage four lung and liver cancer"
    (120.860, "my",         125.500, "cancer",    "IDENTITY: name and diagnosis", "A"),

    # JOURNEY — "it started with stage one colon cancer... turned into four, two years later"
    (130.575, "it",         143.550, "later",     "IDENTITY: stage one to four", "B"),

    # FAMILY — "cancer's in my family, my mother my grandmother my uncle"
    (147.070, "cancer's",   153.710, "stride",    "FAMILY: cancer runs in family", "A"),

    # NEVER THOUGHT — "my mother and grandmother was heavy smokers... I never thought I would get it but I did"
    (243.755, "my",         254.655, "did",       "FAMILY: never thought I'd get it", "B"),

    # DIAGNOSIS — "I had a blood test and my PSA was high... oh my god"
    (193.125, "i",          205.660, "there",     "DIAGNOSIS: blood tests PSA oh my god", "A"),

    # STAGE 4 — "my perception was still to stay strong"
    (291.500, "my",         293.745, "strong",    "STAGE4: stay strong", "B"),

    # HOSPITAL — "this hospital is for me top notch"
    (348.495, "this",       352.655, "notch",     "HOSPITAL: top notch", "A"),

    # UNEXPECTED — "I didn't expect the neuropathy... in my hands and my feet"
    (425.420, "for",        443.665, "here",      "NEUROPATHY: didn't expect", "B"),

    # INVISIBLE — "if I didn't tell you I had cancer you wouldn't be able to tell"
    (474.185, "and",        479.710, "tell",      "NEUROPATHY: you wouldn't know", "A"),

    # FAMILY BEDRIDDEN — "my mother and grandmother, they were sickly and bedridden... I'm thankful"
    (480.830, "like",       497.215, "for",       "FAMILY: they were bedridden", "B"),

    # POSITIVE — "I appreciate every day... I stay positive and move forward"
    (536.700, "i",          557.440, "forward",   "POSITIVE: appreciate every day", "A"),

    # BUTTONS — "with my neuropathy... I can't do buttons and zippers... I still move on"
    (560.160, "my",         581.220, "on",        "GRIT: can't do buttons still move on", "B"),

    # FAMILY SUPPORT — "they all flew in... we just celebrated life"
    (637.470, "they",       652.825, "life",      "SUPPORT: family celebrated life", "A"),

    # YOGA — "I participate in yoga at the hospital twice a week"
    (686.975, "i",          692.255, "week",      "ACTIVE: yoga twice a week", "B"),

    # ADVOCACY — talked someone into chemo
    (748.615, "it",         776.715, "chemo",     "ADVOCACY: talked him into chemo", "A"),

    # BODY — "your body will tell you if you listen"
    (1131.065, "but",       1132.825, "listen",   "ADVOCACY: body will tell you", "B"),

    # HOPE — "never lose hope even when you don't have hope"
    (929.555, "i",          934.035, "hope",      "HOPE: never lose hope", "A"),

    # BRICK WALLS — the money quote
    (947.490, "but",        966.645, "obstacles",  "HOPE: brick walls as rest stops", "B"),

    # MENTALITY — "you have to have that mentality, stay positive even in pain"
    (968.245, "and",        979.170, "pain",       "HOPE: stay positive even in pain", "A"),

    # CLOSING — "if today was my last day... never give up"
    (1010.410, "if",        1033.710, "up",        "CLOSE: never give up", "A"),

    # CLOSING 2 — "live life as best as you can but never give up"
    (1039.070, "live",      1043.230, "up",        "CLOSE: live life never give up", "B"),
]

# ============================================================
# Word-anchor resolver (same as Zamiyah)
# ============================================================
def _load_words():
    dg = os.path.join(BASE, "Vince_Master_Transcript_Deepgram.json")
    with open(dg) as f:
        d = json.load(f)
    words = sorted([w for s in d.get("segments", []) for w in s.get("words", [])],
                   key=lambda w: w["start"])
    print(f"📝 Transcript: Deepgram ({len(words)} words)")
    return words

def resolve_anchors(anchors, words):
    """Convert (first_word_time, first_word, last_word_time, last_word, label, cam) → (in, out, label, cam)."""
    resolved = []
    errors = []
    
    for first_t, first_w, last_t, last_w, label, cam in anchors:
        # Find first word
        fw = None
        for w in words:
            if abs(w["start"] - first_t) < 0.5 and w["word"].lower().strip(".,!? ") == first_w.lower():
                fw = w; break
        if not fw:
            errors.append(f"❌ [{label}] First word '{first_w}' not found near {first_t}s")
            continue
        
        # Find last word
        lw = None
        for w in words:
            if abs(w["start"] - last_t) < 1.0 and w["word"].lower().strip(".,!? ") == last_w.lower():
                lw = w; break
        if not lw:
            errors.append(f"❌ [{label}] Last word '{last_w}' not found near {last_t}s")
            continue
        
        # In-point: midpoint of gap before first word
        prev_w = None
        for w in words:
            if w["end"] <= fw["start"]:
                prev_w = w
        if prev_w and (fw["start"] - prev_w["end"]) < 2.0:
            in_pt = (prev_w["end"] + fw["start"]) / 2
        else:
            in_pt = fw["start"] - 0.15
        
        # Out-point: midpoint of gap after last word
        next_w = None
        for w in words:
            if w["start"] >= lw["end"] + 0.01:
                next_w = w; break
        if next_w and (next_w["start"] - lw["end"]) < 2.0:
            out_pt = (lw["end"] + next_w["start"]) / 2
        else:
            out_pt = lw["end"] + 0.15
        
        resolved.append((in_pt, out_pt, label, cam))
    
    if errors:
        for e in errors: print(e)
        print("Word anchor resolution failed — fix EDIT_ANCHORS above")
        raise SystemExit(1)
    
    print(f"\n🔗 WORD ANCHORS: Resolved {len(resolved)} segments from word boundaries")
    return resolved

# ============================================================
# Intelligent filler removal (same as Zamiyah)
# ============================================================
def intelligent_filler_removal(edit_list, words):
    filler_set = {"um","uh","ums","uhs","hmm","mhm","mmm","ah","hm","mm"}
    new_edit = []
    splits = 0
    trims = 0
    
    for start, end, label, cam in edit_list:
        seg_words = [w for w in words if w["start"] >= start and w["end"] <= end]
        real = [w for w in seg_words if w["word"].lower().strip(".,!? ") not in filler_set]
        fillers = [w for w in seg_words if w["word"].lower().strip(".,!? ") in filler_set]
        
        if not real:
            new_edit.append((start, end, label, cam))
            continue
        
        # Check for standalone filler between thoughts (gap > 0.3s both sides)
        for f in fillers:
            pre_gap = f["start"] - max((w["end"] for w in seg_words if w["end"] < f["start"]), default=start)
            post_gap = min((w["start"] for w in seg_words if w["start"] > f["end"]), default=end) - f["end"]
            if pre_gap > 0.3 and post_gap > 0.3:
                # Split here
                pre_real = [w for w in real if w["end"] <= f["start"]]
                post_real = [w for w in real if w["start"] >= f["end"]]
                if pre_real and post_real:
                    mid_pre = (f["start"] + pre_real[-1]["end"]) / 2
                    mid_post = (f["end"] + post_real[0]["start"]) / 2
                    new_edit.append((start, mid_pre, label, cam))
                    new_edit.append((mid_post, end, label, cam))
                    splits += 1
                    break
            # Trim leading fillers
            elif f == seg_words[0] and post_gap > 0.1:
                next_real = real[0]
                start = (f["end"] + next_real["start"]) / 2
                trims += 1
            # Trim trailing fillers
            elif f == seg_words[-1] and pre_gap > 0.1:
                prev_real = real[-1]
                end = (prev_real["end"] + f["start"]) / 2
                trims += 1
        else:
            new_edit.append((start, end, label, cam))
    
    print(f"\n🧠 INTELLIGENT FILLER REMOVAL:")
    print(f"   Split {splits} standalone fillers between thoughts")
    print(f"   Trimmed {trims} edge fillers (leading/trailing)")
    print(f"   {len(edit_list)} segments → {len(new_edit)} segments")
    return new_edit

# ============================================================
# Narrative read-through
# ============================================================
def narrative_readthrough(edit_list, words):
    filler_set = {"um","uh","ums","uhs","hmm","mhm","mmm","ah","hm","mm"}
    
    print(f"\n{'='*60}")
    print("  📖 NARRATIVE READ-THROUGH — what the viewer hears")
    print(f"{'='*60}\n")
    
    full_text = []
    prev_section = ""
    for i, (start, end, label, cam) in enumerate(edit_list):
        seg_w = [w for w in words if w["start"] >= start - 0.1 and w["end"] <= end + 0.1]
        real = [w for w in seg_w if w["word"].lower().strip(".,!? ") not in filler_set]
        text = " ".join(w["word"] for w in real)
        
        section = label.split(":")[0].strip()
        if section != prev_section:
            print(f"  [{section}]")
            prev_section = section
        
        clean = text[0].upper() + text[1:] if text else ""
        print(f"  {clean}")
        full_text.append(text)
    
    all_text = " ".join(full_text)
    word_count = len(all_text.split())
    print(f"\n  ─── {word_count} words ───")
    print(f"{'='*60}")
    return word_count

# ============================================================
# Narrative lint
# ============================================================
TONE_MAP = {
    "IDENTITY": "LIGHT", "FAMILY": "HEAVY", "DIAGNOSIS": "HEAVY",
    "STAGE4": "HEAVY", "HOSPITAL": "LIGHT", "NEUROPATHY": "HEAVY",
    "POSITIVE": "LIGHT", "GRIT": "HEAVY", "SUPPORT": "LIGHT",
    "ACTIVE": "LIGHT", "ADVOCACY": "LIGHT", "HOPE": "LIGHT",
    "CLOSE": "LIGHT",
}

def narrative_lint(edit_list, words):
    filler_set = {"um","uh","ums","uhs","hmm","mhm","mmm"}
    warnings = []
    errors = []
    
    for i, (s, e, label, cam) in enumerate(edit_list):
        seg_w = [w for w in words if w["start"] >= s and w["end"] <= e]
        real = [w for w in seg_w if w["word"].lower().strip(".,!? ") not in filler_set]
        section = label.split(":")[0].strip()
        tone = TONE_MAP.get(section, "LIGHT")
        
        # Camera monotony
        if i >= 3:
            recent_cams = [edit_list[j][3] for j in range(max(0,i-3), i+1)]
            if len(set(recent_cams)) == 1 and len(recent_cams) >= 4:
                warnings.append(f"  [Seg {i+1}] [CAMERA_MONOTONY] {len(recent_cams)} consecutive Cam {recent_cams[0]} segments.")
        
        # Sentence completion
        if real:
            last = real[-1]["word"].strip()
            if last.endswith(","):
                warnings.append(f"  [Seg {i+1}] [SENTENCE_COMPLETION] Ends with comma '{last}' — check if thought is complete.")
    
    print(f"\n{'='*60}")
    print("NARRATIVE LINT REPORT")
    print(f"{'='*60}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors: print(e)
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings: print(w)
    
    if not errors:
        print(f"\n{'='*60}")
        print(f"✅ No blocking errors — {len(warnings)} warning(s) to review")
        print(f"{'='*60}")
    
    return len(errors) == 0

# ============================================================
# Pipeline execution
# ============================================================
GAP_THRESHOLD = 0.80

ALL_WORDS = _load_words()
EDIT = resolve_anchors(EDIT_ANCHORS, ALL_WORDS)
EDIT = intelligent_filler_removal(EDIT, ALL_WORDS)
WORD_COUNT = narrative_readthrough(EDIT, ALL_WORDS)
lint_ok = narrative_lint(EDIT, ALL_WORDS)

# ============================================================
# Build FCP7 XML — 23.976fps (24000/1001)
# ============================================================
FPS_NUM = 24000
FPS_DEN = 1001
FPS = FPS_NUM / FPS_DEN

cam_a_url = f"file://localhost{quote(os.path.join(BASE, 'Footage/A Cam/C9045.MP4'))}"
cam_b_url = f"file://localhost{quote(os.path.join(BASE, 'Footage/B Cam/C8894.MP4'))}"
audio_url = f"file://localhost{quote(os.path.join(BASE, 'Audio/Vince_Interview_16k.wav'))}"

CAM_A_TOTAL_F = int(round(1411.910 * FPS))
CAM_B_TOTAL_F = int(round(1411.910 * FPS))

def s2f(seconds):
    return int(round(seconds * FPS))

# Build timeline
total_f = sum(s2f(e - s) for s, e, l, c in EDIT)

L = []
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<!DOCTYPE xmeml>')
L.append('<xmeml version="4">')
L.append(' <sequence>')
L.append('  <name>Vince 3min Narrative v1</name>')
L.append('  <duration>{}</duration>'.format(total_f))
L.append('  <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
L.append('  <media>')

# V1 — Cam A
L.append('   <video>')
L.append('    <track>')

seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    dur_f = s2f(e - s)
    src_in = s2f(s)
    src_out = src_in + dur_f
    is_active = (cam == "A")
    
    L.append('     <clipitem id="V1_clip_{}">{}'.format(idx, ''))
    L.append('      <name>{}</name>'.format(label))
    L.append('      <enabled>{}</enabled>'.format("TRUE" if is_active else "FALSE"))
    L.append('      <duration>{}</duration>'.format(CAM_A_TOTAL_F))
    L.append('      <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('      <start>{}</start>'.format(seq_cursor))
    L.append('      <end>{}</end>'.format(seq_cursor + dur_f))
    L.append('      <in>{}</in>'.format(src_in))
    L.append('      <out>{}</out>'.format(src_out))
    L.append('      <file id="CamA_file">')
    L.append('       <name>C9045.MP4</name>')
    L.append('       <pathurl>{}</pathurl>'.format(cam_a_url))
    L.append('       <duration>{}</duration>'.format(CAM_A_TOTAL_F))
    L.append('       <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><video><duration>{}</duration></video><audio><channelcount>2</channelcount></audio></media>'.format(CAM_A_TOTAL_F))
    L.append('      </file>')
    L.append('     </clipitem>')
    seq_cursor += dur_f

L.append('    </track>')

# V2 — Cam B
L.append('    <track>')

seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    dur_f = s2f(e - s)
    src_in = s2f(s)
    src_out = src_in + dur_f
    is_active = (cam == "B")
    
    L.append('     <clipitem id="V2_clip_{}">{}'.format(idx, ''))
    L.append('      <name>{}</name>'.format(label))
    L.append('      <enabled>{}</enabled>'.format("TRUE" if is_active else "FALSE"))
    L.append('      <duration>{}</duration>'.format(CAM_B_TOTAL_F))
    L.append('      <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('      <start>{}</start>'.format(seq_cursor))
    L.append('      <end>{}</end>'.format(seq_cursor + dur_f))
    L.append('      <in>{}</in>'.format(src_in))
    L.append('      <out>{}</out>'.format(src_out))
    L.append('      <file id="CamB_file">')
    L.append('       <name>C8894.MP4</name>')
    L.append('       <pathurl>{}</pathurl>'.format(cam_b_url))
    L.append('       <duration>{}</duration>'.format(CAM_B_TOTAL_F))
    L.append('       <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('       <media><video><duration>{}</duration></video><audio><channelcount>2</channelcount></audio></media>'.format(CAM_B_TOTAL_F))
    L.append('      </file>')
    L.append('     </clipitem>')
    seq_cursor += dur_f

L.append('    </track>')
L.append('   </video>')

# A1 — Cam A audio
L.append('   <audio>')
L.append('    <track>')

seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    dur_f = s2f(e - s)
    src_in = s2f(s)
    src_out = src_in + dur_f
    is_active = (cam == "A")
    
    L.append('     <clipitem id="A1_clip_{}">{}'.format(idx, ''))
    L.append('      <name>{}</name>'.format(label))
    L.append('      <enabled>{}</enabled>'.format("TRUE" if is_active else "FALSE"))
    L.append('      <duration>{}</duration>'.format(CAM_A_TOTAL_F))
    L.append('      <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('      <start>{}</start>'.format(seq_cursor))
    L.append('      <end>{}</end>'.format(seq_cursor + dur_f))
    L.append('      <in>{}</in>'.format(src_in))
    L.append('      <out>{}</out>'.format(src_out))
    L.append('      <file id="CamA_file"/>')
    L.append('      <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>')
    L.append('     </clipitem>')
    seq_cursor += dur_f

L.append('    </track>')

# A2 — Cam B audio
L.append('    <track>')

seq_cursor = 0
for idx, (s, e, label, cam) in enumerate(EDIT):
    dur_f = s2f(e - s)
    src_in = s2f(s)
    src_out = src_in + dur_f
    is_active = (cam == "B")
    
    L.append('     <clipitem id="A2_clip_{}">{}'.format(idx, ''))
    L.append('      <name>{}</name>'.format(label))
    L.append('      <enabled>{}</enabled>'.format("TRUE" if is_active else "FALSE"))
    L.append('      <duration>{}</duration>'.format(CAM_B_TOTAL_F))
    L.append('      <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>')
    L.append('      <start>{}</start>'.format(seq_cursor))
    L.append('      <end>{}</end>'.format(seq_cursor + dur_f))
    L.append('      <in>{}</in>'.format(src_in))
    L.append('      <out>{}</out>'.format(src_out))
    L.append('      <file id="CamB_file"/>')
    L.append('      <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>')
    L.append('     </clipitem>')
    seq_cursor += dur_f

L.append('    </track>')
L.append('   </audio>')
L.append('  </media>')
L.append(' </sequence>')
L.append('</xmeml>')

xml_str = "\n".join(L)

# EDL
total_dur = sum(e - s for s, e, l, c in EDIT)
active_a = sum(1 for s, e, l, c in EDIT if c == "A")
active_b = sum(1 for s, e, l, c in EDIT if c == "B")

print(f"\n✅ Vince 3min Narrative (Word-Level Precision)")
print(f"   Duration: {int(total_dur//60)}:{total_dur%60:04.1f} | {len(EDIT)} segments")
print(f"   V1: {len(EDIT)} Cam A clips ({active_a} active) | V2: {len(EDIT)} Cam B clips ({active_b} active)")

# Write
os.makedirs(os.path.join(BASE, "Premiere/XML"), exist_ok=True)
out_path = os.path.join(BASE, "Premiere/XML/Vince_3min_Narrative_v1.xml")
with open(out_path, "w") as fout:
    fout.write(xml_str)

print(f"   → {out_path}")

# EDL printout
print(f"\n{'='*80}")
print("EDIT DECISION LIST")
print(f"{'='*80}")
seq_t = 0
for s, e, label, cam in EDIT:
    dur = e - s
    m1, s1 = divmod(seq_t, 60)
    m2, s2 = divmod(s, 60)
    m3, s3 = divmod(e, 60)
    print(f"  {int(m1):02d}:{s1:04.1f} | SRC [{int(m2):02d}:{s2:04.1f}-{int(m3):02d}:{s3:04.1f}] {dur:5.1f}s | Cam {cam} | {label}")
    seq_t += dur

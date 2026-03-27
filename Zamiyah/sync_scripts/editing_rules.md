# Multicam Narrative Editing Rules

## The Cardinal Rule
**If someone is talking, show them.** Even a 1-second interjection gets a cut. The viewer needs to see who's speaking.

## When to Cut

### Always Cut To:
- **The person who starts talking** — cut on the first word, not after a delay
- **A new speaker in a back-and-forth** — dialogue exchanges should bounce between close-ups
- **A reaction** — if someone laughs, gasps, or reacts visibly, briefly show them

### Use the Wide Shot For:
- **Opening** — establish the scene, show both people
- **Topic transitions** — give the viewer a "reset" between subjects
- **Crosstalk** — when both people talk at once
- **Long pauses** — when nobody's talking, wide feels natural

### Hold Times
- **Minimum hold for a speaking segment:** 1 second (even short interjections get shown)
- **Minimum hold before cutting to a reaction:** 2 seconds into the speaker's line
- **Don't cut for filler:** If someone just says "mm-hmm" or "yeah" as agreement, stay on the speaker

## Pacing Guidelines
- **Average cut rate:** 1 cut every 8-15 seconds for a conversational podcast
- **Vary the rhythm:** Don't cut at the same interval every time
- **Let long stories breathe:** If someone is telling a story, don't cut away from them just because it's been 30 seconds

---

## Audio Track Rules
- **A1 (Cam A scratch) = DISABLED** — `<enabled>FALSE</enabled>`, reference only
- **A2 (Cam B scratch) = DISABLED** — `<enabled>FALSE</enabled>`, reference only
- **A3 (TASCAM master) = ENABLED** — this is the real audio, always active
- Scratch audio exists for sync verification only.

## Video Track Rules
- **V1: Cam A** — ALL segments present. Enabled when cam='A', disabled when cam='B'
- **V2: Cam B** — ALL segments present. Enabled when cam='B', disabled when cam='A'
- **Both tracks always have all clips.** Toggle `<enabled>` to switch cameras.
- Editor can re-enable any disabled clip to change the camera angle.

## Color Labels (Premiere)
- **V1 / A1 (Cam A)** = Cerulean (blue)
- **V2 / A2 (Cam B)** = Mango (orange)
- **A3 (TASCAM)** = Forest (green)
- Matching colors across video → audio makes tracks easy to identify.
- Section/arc colors available in `ARC_COLORS` dict for future use.

---

## XML Generation Rules (XMEML v4)

### Structure
- **ALWAYS use the `L.append()` line-by-line pattern** — no helper functions, no shortcuts
- File definitions go in the FIRST clipitem with inline `<file>` block
- Subsequent clips reference with `<file id="..."/>`
- Multiple sequences can go under one `<xmeml>` root tag

### CRITICAL: Frame Rate (NTSC)
- **NEVER multiply seconds × 30** for frame numbers
- **ALWAYS use `round(seconds * 30000 / 1001)`** — this is 29.97fps NTSC
- Error: 30fps math drifts ~1ms/sec → **1.4 seconds at 23 minutes**
- Use `ntsc_frame()` from `media_probe.py`

### CRITICAL: Clipitem `<duration>`
- **`<duration>` = total source file duration in frames, NOT clip segment duration**
- Cam A total: `int(round(1493.993 * 30000 / 1001))` = 44775 frames
- Cam B total: `int(round(1511.510 * 30000 / 1001))` = 45300 frames
- TASCAM total: `int(round(1429.296 * 30000 / 1001))` = 42836 frames

### CRITICAL: Audio Bit Depth
- **ALWAYS probe source files with `ffprobe`** before generating XML
- TASCAM is **24-bit** (`pcm_s24le`), use `<depth>24</depth>`
- Camera audio is **16-bit** (`pcm_s16be`), use `<depth>16</depth>`
- Run `media_probe.py` preflight to auto-detect

### Cut Point Timestamps
- Source: WhisperX forced alignment (`Master_S34_Transcript_WhisperX.json`)
- In-point = first_word_start − 150ms
- Out-point = last_word_end + 100ms
- NO onset detector — WhisperX phoneme boundaries are ground truth

---

## Pre-Flight Checklist
Before generating ANY XML, run:
```
python3 _multicam_framework/media_probe.py <video_files> <audio_files>
```
It validates: frame rates match, bit depth detected, NTSC consistency, sample rates, resolutions.

## Common Mistakes (see MISTAKES.md for details)
1. Using helper functions for XML → broken XMEML (BUG-001)
2. Wrong audio bit depth → misinterpreted frame positions (BUG-002)
3. Energy-based onset detection → unreliable cut points (BUG-003)
4. Segment duration in `<duration>` → Premiere confused (BUG-004)
5. 30fps instead of 29.97fps → cumulative drift (BUG-005)

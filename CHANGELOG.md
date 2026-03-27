# Changelog — Cancer Survivors Multicam Framework

Track every version so we never regress.

---

## Zamiyah 3min Narrative Edit

### v3 — 2026-03-27 16:00
- **Onset detection** applied to all 29 cut points (66–296ms corrections)
- **A1/A2 disabled** on import (scratch audio muted)
- **A3 TASCAM enabled** (master audio active)
- **WhisperX installed** — forced alignment pipeline available for future transcriptions
- File: `Zamiyah_3min_Narrative_v3.xml`

### v2 — 2026-03-27 15:31
- Onset detection integrated (first pass)
- A1/A2 NOT disabled (inconsistent — fixed in v3)
- File: `Zamiyah_3min_Narrative_Edit.xml`

### v1 — 2026-03-27 15:17
- Rewritten with proven L.append pattern (BUG-001 fix)
- No onset detection — raw Whisper timestamps only
- "Hi" cut off at beginning (onset issue discovered)
- File: `Zamiyah_3min_Narrative_Edit.xml`

---

## Established Rules (DO NOT CHANGE)

### Track Layout
- V1 = Cam A (Tight)
- V2 = Cam B (Wide)
- A1 = Cam A scratch → **ALWAYS DISABLED**
- A2 = Cam B scratch → **ALWAYS DISABLED**
- A3 = TASCAM master → **ALWAYS ENABLED**

### XML Generation
- ALWAYS use L.append() line-by-line pattern from gen_multicam_v34_2.py
- NEVER use helper functions with positional args for XMEML
- Multiple sequences allowed under one `<xmeml>` root tag
- A1/A2 clips get `<enabled>FALSE</enabled>`

### Sync Constants (Zamiyah)
- CAM_A_OFFSET = 63.2819
- CAM_B_OFFSET = 75.7851
- FPS = 30 (NTSC, Drop-Frame)
- Resolution = 3840×2160

### Transcription Pipeline
- **WhisperX** = preferred (forced alignment with wav2vec2)
- **Onset detector** = supplements any transcription for true audio start
- Transcripts stored as JSON with word-level timestamps
- Source: TASCAM master audio (North Star)

### Editorial Philosophy
- Raw, authentic narrative arcs over YouTube-style hooks
- Cut on clean words — no "ums", no interviewer questions
- Documentary sincerity > engagement tricks

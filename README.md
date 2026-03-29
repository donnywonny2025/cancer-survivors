# Cancer Survivors — Bronson Cancer Equity Project

Automated narrative editing pipeline for multicam cancer survivor interviews. Produces Premiere-ready FCP7 XML sequences from raw interview footage using word-level Deepgram transcription.

## Project Status

| Subject | Status | Version | Duration |
|---------|--------|---------|----------|
| **Zamiyah** | ✅ Edit complete | v22 | 2:44 / 23 segments |
| **Vince** | 🔜 Transcribed, pending edit | — | — |

## How It Works

The pipeline converts a 24-minute raw interview into a 2:44 narrative using **word-anchor editing** — segments are defined by their first and last spoken word, not fragile timecodes.

```
Raw Footage → Deepgram Transcription → Word-Anchor Selection → Filler Removal
    → Narrative Read-Through → Lint Check → FCP7 XML → Premiere Import
```

### Pipeline Passes

| Pass | What it does |
|------|-------------|
| 🔗 **Word Anchors** | Resolves "first word → last word" to frame-accurate in/out points |
| 🧠 **Filler Removal** | Splits/trims fillers (um, uh) between thoughts |
| 📖 **Read-Through** | Prints the complete viewer transcript for story verification |
| 🔍 **Lint Report** | Flags pacing, camera monotony, sentence completion issues |
| ✅ **XML Write** | Generates FCP7 multicam XML for Premiere Pro |

### Word-Anchor System

Every segment is defined by the actual words, not arbitrary timecodes:

```python
# (first_word_time, "first_word", last_word_time, "last_word", "LABEL", "CAM")
(1404.655, "hi", 1409.070, "lymphoma", "IDENTITY", "B"),
```

The resolver guarantees:
- Every specified word is **fully included** — no clipping
- Every cut lands in a **silence gap** — no trailing bleed
- Breathing room is **built into the lookup** — no post-processing

## Project Structure

```
Cancer Survivors/
├── Zamiyah/
│   ├── Footage/
│   │   ├── Cam A/C8826.MP4          # UHD 29.97 master
│   │   └── Cam B/C8890.MP4          # UHD 29.97 master
│   ├── Audio/
│   │   └── TASCAM_1087S34.wav       # TASCAM S34 master audio
│   ├── Master_S34_Transcript_Deepgram.json  # 2175 words, word-level timestamps
│   ├── sync_scripts/
│   │   └── cut_zamiyah_3min_v10.py   # Main pipeline script
│   └── Premiere/XML/
│       └── Zamiyah_3min_Narrative_v22.xml  # Current output
├── Vince/
│   ├── Footage/                      # Multicam interview footage
│   └── Master_S34_Transcript_Deepgram.json  # Transcribed, pending edit
├── .agent/workflows/
│   └── narrative-edit.md             # Codified 6-phase workflow
├── EDITING_GUIDE.md                  # Editorial standards
├── CHANGELOG.md                      # Version history
└── MISTAKES.md                       # Bug log and lessons learned
```

## Running the Pipeline

```bash
cd Zamiyah
python3 sync_scripts/cut_zamiyah_3min_v10.py
```

Output:
1. Narrative read-through (full viewer transcript)
2. Lint report (warnings for editorial review)
3. FCP7 XML file in `Premiere/XML/`
4. EDL with source timecodes

## Workflow

See `/narrative-edit` workflow or `.agent/workflows/narrative-edit.md` for the full 6-phase process:

1. **Transcription** — Deepgram API (run once, costs money)
2. **Analysis** — Read full transcript, identify usable segments
3. **Word-Anchor Definition** — Pick first/last words for each segment
4. **Story Assembly** — Order into narrative arc, verify read-through
5. **Verification** — Audit for clipped words, review lint warnings
6. **Polish** — Import to Premiere, add B-roll, music, color

## Tech Stack

- **Python 3** — pipeline logic
- **Deepgram API** — word-level transcription (verbatim mode)
- **FCP7 XML** — Premiere Pro interchange format
- **NTSC 29.97 Drop-Frame** — timecode standard
- **Git** — version control (`github.com/donnywonny2025/cancer-survivors`)

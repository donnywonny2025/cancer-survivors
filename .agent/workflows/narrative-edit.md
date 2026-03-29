---
description: How to build a narrative edit from raw interview footage using the word-anchor pipeline
---

# Narrative Edit Pipeline

## Prerequisites
- Raw multicam footage (synced)
- TASCAM master audio (or best audio source)

## Phase 1: Transcription
1. Extract 16kHz mono audio from master source:
   ```
   ffmpeg -i MASTER_AUDIO.wav -ar 16000 -ac 1 audio_16k.wav
   ```
2. Run Deepgram API transcription (word-level timestamps, verbatim mode):
   - Output: `Master_Transcript_Deepgram.json`
   - This costs money — only run ONCE
   - Verify word count and spot-check timestamps
3. DO NOT re-transcribe unless source audio changes

## Phase 2: Transcript Analysis
1. Read the FULL transcript end-to-end
2. Listen for director cues ("that was great", "try that again", "got it")
3. Identify **usable segments** — complete thoughts, clear delivery, no stumbles
4. Note which **take** is best when she tries a line multiple times
5. Flag **strong lines** that carry emotional weight or thesis statements
6. Create an inclusion/exclusion list before making any cuts

## Phase 3: Word-Anchor Definition
1. For each usable segment, find the EXACT first and last word in the Deepgram JSON:
   ```python
   # Format: (first_word_start_time, "first_word", last_word_start_time, "last_word", "LABEL", "CAM")
   (1404.655, "hi", 1409.070, "lymphoma", "IDENTITY", "B"),
   ```
2. Verify each word exists at that timestamp — run resolver, check for errors
3. The resolver automatically:
   - Places in-point in the silence gap BEFORE first word
   - Places out-point in the silence gap AFTER last word
   - Guarantees every specified word is fully included
   - Prevents trailing word bleed

## Phase 4: Story Assembly
1. Order segments into a narrative arc (not chronological — STORY order)
2. Run the pipeline — it prints the **Narrative Read-Through**
3. READ the full story as text — does it flow? Does it make sense?
4. If a transition feels wrong, reorder segments or adjust anchors
5. The story should have a clear arc: setup → conflict → growth → resolution

## Phase 5: Verification
1. **Read-Through Pass**: Read the printed transcript — every word the viewer hears
2. **Lint Pass**: Review warnings (pacing, camera monotony, sentence completion)
3. **Audit**: Confirm 0 clipped words, 0 trailing bleed
4. **Import XML** into Premiere and watch with audio
5. Note any tight cuts — fix by adjusting word anchors (include an earlier/later word)

## Phase 6: Polish (in Premiere)
1. Address lint warnings (swap cameras for variety, adjust pacing)
2. Add B-roll cutaways over jump cuts
3. Add music bed, color grade, titles

## Rules
- **NEVER re-transcribe** — the Deepgram JSON is the single source of truth
- **ALWAYS bump version number** when generating a new XML
- **ALWAYS print the read-through** before writing XML
- **Word anchors only** — no raw timecodes in the EDIT list
- **One change = one version** — no regenerating the same version number

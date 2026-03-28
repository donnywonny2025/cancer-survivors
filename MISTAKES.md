# Bronson Cancer Equity — Mistake Log

Track bugs so they never happen again.

---

## BUG-001: XML Helper Function Broke Layout
- **Issue**: Using helper functions with positional args produced broken XMEML
- **Fix**: Always use L.append() line-by-line pattern
- **Verified**: v34.2 Golden Layout imports clean

## BUG-002: TASCAM Audio Bit Depth Wrong in XML
- **Issue**: TASCAM is 24-bit (`pcm_s24le`), XML declared `<depth>16</depth>`
- **Effect**: Premiere misinterpreted frame positions
- **Root Cause**: Hardcoded 16-bit assumption without probing source file
- **Fix**: Changed to `<depth>24</depth>` for TASCAM clips
- **Rule**: ALWAYS run `media_probe.py` preflight to detect bit depth
- **Verified**: v6+

## BUG-003: Onset Detector Unreliable
- **Issue**: Energy-based onset detection picked noise, not speech
- **Effect**: Cut points moved unpredictably, sometimes making things worse
- **Fix**: Replaced with WhisperX forced alignment (wav2vec2 phoneme boundaries)
- **Rule**: Use WhisperX timestamps + 150ms pre-pad. No onset detector.
- **Verified**: v5+

## BUG-004: Clipitem `<duration>` Set to Segment Length, Not File Length
- **Issue**: `<duration>` on clipitems used clip segment frames (e.g. 160)
- **Effect**: Premiere couldn't resolve `<in>` values beyond the declared duration
- **Root Cause**: Used `dur_f` (segment) instead of total file duration
- **Fix**: All clipitems now use `CAM_A_TOTAL_F`, `CAM_B_TOTAL_F`, `TASCAM_TOTAL_F`
- **Rule**: `<duration>` = total source file duration in frames. Always.
- **Verified**: v7+

## BUG-005: 30fps vs 29.97fps (NTSC) Frame Calculation ⚠️ CRITICAL
- **Issue**: Used `round(seconds * 30)` but sequence is 29.97fps (NTSC=TRUE)
- **Effect**: Cumulative drift of ~1ms per second. At 23:24 = **1.4 second error**
- **Root Cause**: `FPS = 30` constant used for frame math, ignoring NTSC pulldown
- **Fix**: `round(seconds * 30000 / 1001)` — use `ntsc_frame()` from `media_probe.py`
- **Rule**: NEVER multiply by timebase directly. Always use `ntsc_frame()`.
- **Verified**: v8

## BUG-006: Overwriting XML Instead of Versioning
- **Issue**: When user gave feedback on v10, re-generated v10 instead of bumping to v11
- **Effect**: No way to compare before/after. Breaks revision history.
- **Root Cause**: Lazy — didn't update the output filename after changes
- **Fix**: EVERY round of feedback = new version number in the output filename
- **Rule**: NEVER overwrite an XML version. Always increment: v10 → v11 → v12
- **Verified**: v11

## BUG-007: Missing `</track>` After Adding Color Labels
- **Issue**: Text replacement edit consumed the `</track>` between A1 and A2
- **Effect**: Premiere showed only 2 audio tracks instead of 3
- **Root Cause**: AI edit tool replaced too much context, removing structural XML tags
- **Fix**: Added structural validator to script (tag balance, track count, clip count)
- **Rule**: Structural validator runs BEFORE file write. Script refuses to write broken XML.
- **Verified**: v9+

## BUG-008: Stumbles/False Starts Not Caught in EDIT List
- **Issue**: COST segment included "It affects your routines... Sorry." stumble
- **Effect**: Subject says "Sorry" in the middle of the final narrative
- **Root Cause**: EDIT list was built without scanning transcript for stumble markers
- **Fix**: Added stumble detection to Intelligent Cut rules (3-option framework)
- **Rule**: BEFORE finalizing EDIT list, scan EVERY segment's WhisperX words for:
  "Sorry", repeated sentence openers, "Let me start over", self-corrections
- **Verified**: v11

---

## Pre-Flight Checklist (codified in `_multicam_framework/media_probe.py`)

Before generating ANY XML, run:
```
python3 _multicam_framework/media_probe.py <video_files> <audio_files>
```

It checks:
- [ ] All video files have same frame rate
- [ ] Frame rate matches sequence (29.97 vs 23.976 vs 30)
- [ ] NTSC flag is consistent
- [ ] Audio bit depth detected correctly (16 vs 24 vs 32)
- [ ] Audio sample rates match (48kHz)
- [ ] Video resolutions match (3840x2160)
- [ ] Total file durations computed at correct NTSC rate

## Versioning Rules
- [ ] **EVERY change = new version number** — never overwrite
- [ ] Output filename includes version: `_v11.xml`, `_v12.xml`, etc.
- [ ] Git commit after every version with a message describing what changed
- [ ] Changes logged in this file with BUG-### format

---

## BUG-016: Filler words ("um", "uh") not caught by WhisperX
**Discovered**: v13 review — audible "um" at edit position 00:08:07
**Root Cause**: Whisper skips fillers by design. `suppress_tokens=[]` doesn't fix it.
**Working Fix**: Gap Detection + Auto Gap Removal in `cut_zamiyah_3min_v10.py`
- Gaps >0.8s after sentence-ending words = filler locations
- Pipeline splits segments at those gaps, skipping the filler
- 8 filler gaps cut in v14, 0 linter errors

## BUG-017: CrisperWhisper CPU incompatible
**Issue**: 1.5B param model — 11 min for 15s on CPU, hallucinated output
**Resolution**: Archived. Gap detection supersedes need for filler-aware model.

## Filler Detection System (v14+)
Layer 1: Gap removal (>0.8s after sentence end) → splits segments
Layer 2: Word boundary alignment → in/out snap to first/last word
Layer 3: Narrative linter → catches mid-sentence cuts

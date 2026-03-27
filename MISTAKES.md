# Mistake Log — Cancer Survivors Multicam Framework

Track every bug so we never repeat them.

---

## BUG-001: XML clipitem argument mangling (2026-03-27)

**Symptom**: Premiere "File Import Failure" on `Zamiyah_3min_Narrative_Edit.xml`

**Root Cause**: Used a Python list comprehension with a `ci()` helper function that reordered tuple arguments incorrectly. The clip name ("C8826.MP4") was being placed in `<in>` and the file_id ("f_a") was placed in `<out>` instead of integer frame numbers.

**Bad output**:
```xml
<in>C8826.MP4</in><out>f_a</out>   ← strings instead of frame numbers
# Bronson Cancer Equity — Mistake Log

Track bugs so they never happen again.

---

## BUG-001: XML Helper Function Broke Layout
- **Issue**: Using helper functions with positional args produced broken XMEML
- **Fix**: Always use L.append() line-by-line pattern
- **Verified**: v34.2 Golden Layout imports clean

## BUG-002: TASCAM Audio Bit Depth Wrong in XML
- **Issue**: TASCAM is 24-bit (`pcm_s24le`), XML declared `<depth>16</depth>`
- **Effect**: Premiere misinterpreted frame positions — audio offset by ~1.6 seconds
- **Root Cause**: Hardcoded 16-bit assumption without verifying source file
- **Fix**: Changed to `<depth>24</depth>` for TASCAM clips
- **Rule**: ALWAYS use `ffprobe` to verify source file specs before generating XML
- **Verified**: v6

## BUG-003: Onset Detector Unreliable
- **Issue**: Energy-based onset detection picked noise, not speech
- **Effect**: Cut points moved unpredictably, sometimes making things worse
- **Fix**: Replaced with WhisperX forced alignment (wav2vec2 phoneme boundaries)
- **Rule**: Use WhisperX timestamps + 150ms pre-pad. No onset detector.
- **Verified**: v5

---

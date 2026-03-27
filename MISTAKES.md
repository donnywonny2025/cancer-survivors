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

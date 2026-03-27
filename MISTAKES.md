# Mistake Log — Cancer Survivors Multicam Framework

Track every bug so we never repeat them.

---

## BUG-001: XML clipitem argument mangling (2026-03-27)

**Symptom**: Premiere "File Import Failure" on `Zamiyah_3min_Narrative_Edit.xml`

**Root Cause**: Used a Python list comprehension with a `ci()` helper function that reordered tuple arguments incorrectly. The clip name ("C8826.MP4") was being placed in `<in>` and the file_id ("f_a") was placed in `<out>` instead of integer frame numbers.

**Bad output**:
```xml
<in>C8826.MP4</in><out>f_a</out>   ← strings instead of frame numbers
<file id="160"/>                    ← duration value instead of file ID
```

**Expected output**:
```xml
<in>1897</in><out>44733</out>       ← integer frame numbers
<file id="f_a"/>                    ← correct file reference
```

**Fix**: Rewrote using the proven v34.2 `L.append()` pattern. No helper functions, no list comprehensions, no shortcuts for XML generation.

**Rule**: ALWAYS use the `L.append()` line-by-line pattern from `gen_multicam_v34_2.py` for XML generation. Never use template functions with positional arguments for XMEML.

---

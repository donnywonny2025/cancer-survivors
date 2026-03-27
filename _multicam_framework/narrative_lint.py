#!/usr/bin/env python3
"""
Narrative Lint — Editorial Intelligence Pre-Flight
===================================================

Runs BEFORE XML generation. Catches narrative problems that a human editor
would notice on first watch:

  1. Dependency violations (signs before diagnosis, cost before struggle)
  2. Viewer comprehension gaps (references topic not yet established)
  3. Emotional pacing issues (3+ heavy segments back-to-back)
  4. Camera monotony (same angle for too long)
  5. Structural checks (identity first, close last, arc coverage)

Usage:
    from narrative_lint import lint_edit_list
    warnings = lint_edit_list(edit_list, transcript_words=None)

Each warning is a dict: {severity, rule, segment_index, message}
Severity: ERROR (should fix), WARN (review), INFO (suggestion)
"""

from typing import List, Dict, Tuple, Optional
import re

# ============================================================
# ARC LABELS & CLASSIFICATION
# ============================================================

# Canonical arc sections in dependency order
ARC_ORDER = [
    "IDENTITY",
    "SIGNS",
    "MOMENT",
    "PERSONALITY",   # flexible — can move, but has constraints
    "COST",
    "POWER",
    "CHANGE",
    "MUSIC",         # alias: EXPRESSION
    "NURSE",         # alias: SUPPORT
    "CLOSE",
]

# What must come BEFORE a given section can appear
# Key = section, Value = set of sections that must appear earlier
DEPENDENCIES = {
    "SIGNS":       {"IDENTITY"},
    "MOMENT":      {"IDENTITY"},
    "COST":        {"IDENTITY", "SIGNS"},   # need at least IDENTITY + SIGNS
    "POWER":       {"COST"},
    "CHANGE":      {"COST"},
    "CLOSE":       set(),                   # no hard deps, but must be last
}

# Sections that should NOT interrupt a contextual chain
# A "chain" is two dependent sections (e.g., IDENTITY → SIGNS)
CHAIN_BREAKERS = {"PERSONALITY", "MUSIC", "NURSE"}

# Emotional weight classification
HEAVY_SECTIONS = {"COST", "CHANGE", "POWER", "MOMENT"}
LIGHT_SECTIONS = {"PERSONALITY", "MUSIC", "NURSE", "IDENTITY"}
NEUTRAL_SECTIONS = {"SIGNS", "CLOSE"}

# Keywords that indicate cancer/diagnosis context
CANCER_KEYWORDS = {
    "cancer", "diagnosis", "diagnosed", "treatment", "chemo",
    "chemotherapy", "lymphoma", "tumor", "oncology", "radiation",
    "symptoms", "biopsy", "remission", "survivor",
}

# Keywords that indicate signs/symptoms
SIGNS_KEYWORDS = {
    "signs", "symptoms", "subtle", "swollen", "lymph", "fatigue",
    "fatigued", "drained", "sweats", "lump", "noticed", "felt",
}


def _extract_label(raw_label: str) -> str:
    """Extract the arc section from a label like 'COST: confidence self-identity'."""
    # Take everything before the first colon, uppercase, strip
    base = raw_label.split(":")[0].strip().upper()

    # Normalize aliases
    aliases = {
        "EXPRESSION": "MUSIC",
        "SUPPORT": "NURSE",
        "DIAGNOSIS": "COST",
    }
    return aliases.get(base, base)


def _get_segment_text(
    edit_entry: tuple,
    transcript_words: Optional[List[Dict]] = None,
) -> str:
    """Get the transcript text for a segment's time range."""
    if not transcript_words:
        return ""
    start, end = edit_entry[0], edit_entry[1]
    words = [
        w["word"]
        for w in transcript_words
        if start - 0.3 <= w.get("start", 0) <= end + 0.3
    ]
    return " ".join(words)


# ============================================================
# LINT RULES
# ============================================================

def _check_dependencies(
    edit_list: list,
    labels: List[str],
) -> List[Dict]:
    """Check that narrative dependencies are satisfied."""
    warnings = []
    seen = set()

    for i, label in enumerate(labels):
        required = DEPENDENCIES.get(label, set())
        missing = required - seen
        if missing:
            warnings.append({
                "severity": "ERROR",
                "rule": "DEPENDENCY",
                "segment_index": i,
                "message": (
                    f"Segment {i+1} ({label}) requires {missing} to appear "
                    f"before it, but they haven't been established yet."
                ),
            })
        seen.add(label)

    return warnings


def _check_identity_first(labels: List[str]) -> List[Dict]:
    """IDENTITY should be in the first 2 segments."""
    warnings = []
    if "IDENTITY" not in labels[:2]:
        idx = labels.index("IDENTITY") if "IDENTITY" in labels else -1
        warnings.append({
            "severity": "ERROR",
            "rule": "IDENTITY_POSITION",
            "segment_index": idx,
            "message": (
                f"IDENTITY is at position {idx+1} but should be in the first "
                f"2 segments. The viewer needs to know WHO this person is immediately."
            ),
        })
    return warnings


def _check_close_last(labels: List[str]) -> List[Dict]:
    """CLOSE segments should be in the last 3 positions."""
    warnings = []
    close_indices = [i for i, l in enumerate(labels) if l == "CLOSE"]
    if close_indices:
        first_close = close_indices[0]
        if first_close < len(labels) - 4:
            warnings.append({
                "severity": "WARN",
                "rule": "CLOSE_POSITION",
                "segment_index": first_close,
                "message": (
                    f"First CLOSE segment is at position {first_close+1} of "
                    f"{len(labels)}. CLOSE should be near the end."
                ),
            })
    return warnings


def _check_chain_interruption(labels: List[str]) -> List[Dict]:
    """Check if a light section interrupts a dependent chain."""
    warnings = []

    # Define chains: pairs where B depends on A
    chains = [
        ("IDENTITY", "SIGNS"),
        ("SIGNS", "MOMENT"),
        ("SIGNS", "COST"),
        ("COST", "POWER"),
    ]

    for chain_start, chain_end in chains:
        if chain_start in labels and chain_end in labels:
            start_idx = labels.index(chain_start)
            end_idx = labels.index(chain_end)

            # Check for breakers between them
            for mid_idx in range(start_idx + 1, end_idx):
                if labels[mid_idx] in CHAIN_BREAKERS:
                    warnings.append({
                        "severity": "WARN",
                        "rule": "CHAIN_INTERRUPTION",
                        "segment_index": mid_idx,
                        "message": (
                            f"Segment {mid_idx+1} ({labels[mid_idx]}) interrupts "
                            f"the {chain_start}→{chain_end} narrative chain. "
                            f"The viewer may lose context."
                        ),
                    })

    return warnings


def _check_viewer_comprehension(
    edit_list: list,
    labels: List[str],
    transcript_words: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Check if segments reference cancer/signs before they're established."""
    warnings = []
    if not transcript_words:
        return warnings

    diagnosis_established = False

    for i, (entry, label) in enumerate(zip(edit_list, labels)):
        text = _get_segment_text(entry, transcript_words).lower()

        # Track when diagnosis is established
        if label == "IDENTITY" and any(kw in text for kw in CANCER_KEYWORDS):
            diagnosis_established = True

        # Check if this segment references cancer before it's established
        if not diagnosis_established and label not in ("IDENTITY",):
            cancer_refs = [kw for kw in CANCER_KEYWORDS if kw in text]
            signs_refs = [kw for kw in SIGNS_KEYWORDS if kw in text]
            refs = cancer_refs + signs_refs

            if refs:
                warnings.append({
                    "severity": "WARN",
                    "rule": "COMPREHENSION",
                    "segment_index": i,
                    "message": (
                        f"Segment {i+1} ({label}) references [{', '.join(refs[:3])}] "
                        f"but the viewer doesn't know she has cancer yet."
                    ),
                })

    return warnings


def _check_emotional_pacing(labels: List[str]) -> List[Dict]:
    """Flag 3+ consecutive heavy or light segments."""
    warnings = []
    streak_type = None
    streak_start = 0
    streak_count = 0

    for i, label in enumerate(labels):
        if label in HEAVY_SECTIONS:
            current = "HEAVY"
        elif label in LIGHT_SECTIONS:
            current = "LIGHT"
        else:
            current = "NEUTRAL"

        if current == streak_type and current != "NEUTRAL":
            streak_count += 1
        else:
            if streak_count >= 3:
                warnings.append({
                    "severity": "WARN",
                    "rule": "PACING",
                    "segment_index": streak_start,
                    "message": (
                        f"{streak_count} consecutive {streak_type} segments "
                        f"(positions {streak_start+1}-{streak_start+streak_count}). "
                        f"Consider adding contrast — {'a lighter' if streak_type == 'HEAVY' else 'a heavier'} "
                        f"moment between them."
                    ),
                })
            streak_type = current
            streak_start = i
            streak_count = 1

    # Check final streak
    if streak_count >= 3 and streak_type != "NEUTRAL":
        warnings.append({
            "severity": "WARN",
            "rule": "PACING",
            "segment_index": streak_start,
            "message": (
                f"{streak_count} consecutive {streak_type} segments "
                f"(positions {streak_start+1}-{streak_start+streak_count}). "
                f"Consider varying the emotional rhythm."
            ),
        })

    return warnings


def _check_camera_monotony(edit_list: list) -> List[Dict]:
    """Flag 4+ consecutive segments on the same camera."""
    warnings = []
    streak_cam = None
    streak_start = 0
    streak_count = 0

    for i, entry in enumerate(edit_list):
        cam = entry[3] if len(entry) > 3 else "A"
        if cam == streak_cam:
            streak_count += 1
        else:
            if streak_count >= 4:
                warnings.append({
                    "severity": "WARN",
                    "rule": "CAMERA_MONOTONY",
                    "segment_index": streak_start,
                    "message": (
                        f"{streak_count} consecutive Cam {streak_cam} segments "
                        f"(positions {streak_start+1}-{streak_start+streak_count}). "
                        f"Switch cameras for visual variety."
                    ),
                })
            streak_cam = cam
            streak_start = i
            streak_count = 1

    if streak_count >= 4:
        warnings.append({
            "severity": "WARN",
            "rule": "CAMERA_MONOTONY",
            "segment_index": streak_start,
            "message": (
                f"{streak_count} consecutive Cam {streak_cam} segments at end. "
                f"Switch cameras for visual variety."
            ),
        })

    return warnings


def _check_arc_coverage(labels: List[str]) -> List[Dict]:
    """Check that all essential arc sections are represented."""
    warnings = []
    essential = {"IDENTITY", "SIGNS", "COST", "CLOSE"}
    desired = {"MOMENT", "POWER", "CHANGE"}

    unique = set(labels)

    for section in essential:
        if section not in unique:
            warnings.append({
                "severity": "ERROR",
                "rule": "ARC_COVERAGE",
                "segment_index": -1,
                "message": f"Missing essential arc section: {section}",
            })

    for section in desired:
        if section not in unique:
            warnings.append({
                "severity": "INFO",
                "rule": "ARC_COVERAGE",
                "segment_index": -1,
                "message": f"Missing recommended arc section: {section}",
            })

    return warnings


def _check_sentence_completion(
    edit_list: list,
    transcript_words: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Check if segments end mid-thought."""
    warnings = []
    if not transcript_words:
        return warnings

    connectors = {"and", "but", "so", "because", "or", "that", "which", "when"}

    for i, entry in enumerate(edit_list):
        end = entry[1]
        # Find words IN this segment — use tight tolerance to avoid
        # catching words that start just after the out-point
        seg_words = [
            w for w in transcript_words
            if entry[0] - 0.15 <= w.get("start", 0) <= end + 0.05
        ]
        if not seg_words:
            continue

        last_word = seg_words[-1].get("word", "")
        clean = last_word.rstrip(".,!?;:")

        # If the word has terminal punctuation, the thought is likely complete
        has_terminal = last_word.endswith((".","!","?"))

        # Check for mid-sentence endings (only if no terminal punctuation)
        if not has_terminal and clean.lower() in connectors:
            warnings.append({
                "severity": "ERROR",
                "rule": "SENTENCE_COMPLETION",
                "segment_index": i,
                "message": (
                    f"Segment {i+1} ends with connector '{last_word}' — "
                    f"she's mid-thought. Extend the out-point."
                ),
            })
        elif last_word.endswith(","):
            warnings.append({
                "severity": "WARN",
                "rule": "SENTENCE_COMPLETION",
                "segment_index": i,
                "message": (
                    f"Segment {i+1} ends with comma '{last_word}' — "
                    f"possible mid-list or mid-clause. Check if thought is complete."
                ),
            })

    return warnings


# ============================================================
# MAIN LINTER
# ============================================================

def _check_source_overlap(edit_list: list) -> List[Dict]:
    """Check if consecutive segments from nearby source regions overlap in time."""
    warnings = []

    for i in range(len(edit_list) - 1):
        curr_start, curr_end = edit_list[i][0], edit_list[i][1]
        next_start, next_end = edit_list[i + 1][0], edit_list[i + 1][1]

        # Only check if source times are close (within 30s of each other)
        # — segments from different parts of the interview can't overlap
        if abs(curr_start - next_start) > 30:
            continue

        # Check for actual overlap
        if curr_end > next_start:
            overlap = curr_end - next_start
            warnings.append({
                "severity": "ERROR",
                "rule": "SOURCE_OVERLAP",
                "segment_index": i,
                "message": (
                    f"Segments {i+1} and {i+2} have {overlap:.1f}s SOURCE OVERLAP. "
                    f"Seg {i+1} ends at {curr_end:.3f} but Seg {i+2} starts at {next_start:.3f}. "
                    f"Audio will repeat/stutter at this cut point."
                ),
            })

    return warnings


def lint_edit_list(
    edit_list: list,
    transcript_words: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Run all narrative lint checks on an EDIT list.

    Args:
        edit_list: List of tuples (in_point, out_point, label, camera)
        transcript_words: Optional list of WhisperX word dicts with 'start', 'end', 'word'

    Returns:
        List of warning dicts with severity, rule, segment_index, message
    """
    # Extract arc labels from the raw labels
    labels = [_extract_label(entry[2]) for entry in edit_list]

    warnings = []

    # Run all checks
    warnings.extend(_check_identity_first(labels))
    warnings.extend(_check_close_last(labels))
    warnings.extend(_check_dependencies(edit_list, labels))
    warnings.extend(_check_chain_interruption(labels))
    warnings.extend(_check_viewer_comprehension(edit_list, labels, transcript_words))
    warnings.extend(_check_emotional_pacing(labels))
    warnings.extend(_check_camera_monotony(edit_list))
    warnings.extend(_check_arc_coverage(labels))
    warnings.extend(_check_sentence_completion(edit_list, transcript_words))
    warnings.extend(_check_source_overlap(edit_list))

    # Sort by severity (ERROR > WARN > INFO)
    severity_order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 3))

    return warnings


def print_lint_report(warnings: List[Dict]) -> bool:
    """
    Print a formatted lint report.
    Returns True if there are no ERRORs.
    """
    if not warnings:
        print("\n✅ NARRATIVE LINT: ALL CHECKS PASSED")
        return True

    errors = [w for w in warnings if w["severity"] == "ERROR"]
    warns = [w for w in warnings if w["severity"] == "WARN"]
    infos = [w for w in warnings if w["severity"] == "INFO"]

    print(f"\n{'='*60}")
    print(f"NARRATIVE LINT REPORT")
    print(f"{'='*60}")

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for w in errors:
            seg = f"[Seg {w['segment_index']+1}]" if w['segment_index'] >= 0 else "[Global]"
            print(f"  {seg} [{w['rule']}] {w['message']}")

    if warns:
        print(f"\n⚠️  WARNINGS ({len(warns)}):")
        for w in warns:
            seg = f"[Seg {w['segment_index']+1}]" if w['segment_index'] >= 0 else "[Global]"
            print(f"  {seg} [{w['rule']}] {w['message']}")

    if infos:
        print(f"\nℹ️  INFO ({len(infos)}):")
        for w in infos:
            seg = f"[Seg {w['segment_index']+1}]" if w['segment_index'] >= 0 else "[Global]"
            print(f"  {seg} [{w['rule']}] {w['message']}")

    print(f"\n{'='*60}")
    has_errors = len(errors) > 0
    if has_errors:
        print(f"⛔ {len(errors)} ERROR(s) found — review before export")
    else:
        print(f"✅ No blocking errors — {len(warns)} warning(s) to review")
    print(f"{'='*60}\n")

    return not has_errors


# ============================================================
# CLI: Run standalone against the current EDIT list
# ============================================================

if __name__ == "__main__":
    import json
    import os

    # Load transcript
    BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
    transcript_path = os.path.join(BASE, "Master_S34_Transcript_WhisperX.json")

    all_words = []
    if os.path.exists(transcript_path):
        with open(transcript_path) as f:
            data = json.load(f)
        for seg in data.get("segments", []):
            for w in seg.get("words", []):
                if "start" in w:
                    all_words.append(w)
        all_words.sort(key=lambda w: w["start"])
        print(f"Loaded {len(all_words)} words from transcript")

    # Current v13 EDIT list
    EDIT_v13 = [
        (1404.337, 1409.673, "IDENTITY", "B"),
        (45.156, 53.977, "SIGNS: subtle lymph nodes", "B"),
        (55.669, 66.312, "SIGNS: fatigued drained", "A"),
        (132.925, 138.662, "MOMENT: always active dance", "A"),
        (150.429, 155.485, "MOMENT: knew something wasn't right", "B"),
        (83.762, 96.912, "PERSONALITY: dancing piano guitar", "A"),
        (256.837, 265.139, "COST: how much life you lose", "A"),
        (277.587, 281.222, "COST: confidence self-identity", "A"),
        (429.395, 439.795, "POWER: fear is normal taking power back", "A"),
        (440.346, 455.715, "POWER: knowing is better", "B"),
        (517.959, 522.837, "CHANGE: small days", "B"),
        (526.803, 536.046, "CHANGE: value rest joy people", "A"),
        (547.472, 552.569, "CHANGE: grown as person", "A"),
        (821.965, 827.722, "MUSIC: write my own music", "A"),
        (828.253, 835.933, "MUSIC: express feelings emotions", "A"),
        (1303.394, 1312.945, "NURSE: love so dearly had cancer", "B"),
        (1312.374, 1329.527, "NURSE: somebody understands you", "A"),
        (680.163, 695.779, "CLOSE: stay confident be yourself", "A"),
        (717.756, 720.009, "CLOSE: your journey is your journey", "A"),
        (721.120, 725.236, "CLOSE: break through anything", "B"),
    ]

    # Old v12 order (before fix) for comparison
    EDIT_v12_old = [
        (1404.337, 1409.673, "IDENTITY", "B"),
        (83.762, 96.912, "PERSONALITY: dancing piano guitar", "A"),  # ← WRONG POSITION
        (45.156, 53.977, "SIGNS: subtle lymph nodes", "B"),
        (55.669, 66.312, "SIGNS: fatigued drained", "A"),
        (132.925, 138.662, "MOMENT: always active dance", "A"),
        (150.429, 155.485, "MOMENT: knew something wasn't right", "B"),
        (256.837, 265.139, "COST: how much life you lose", "A"),
        (277.587, 281.222, "COST: confidence self-identity", "A"),
        (429.395, 439.795, "POWER: fear is normal taking power back", "A"),
        (440.346, 455.715, "POWER: knowing is better", "B"),
        (517.959, 522.837, "CHANGE: small days", "B"),
        (526.803, 536.046, "CHANGE: value rest joy people", "A"),
        (547.472, 552.569, "CHANGE: grown as person", "A"),
        (821.965, 827.722, "MUSIC: write my own music", "A"),
        (828.253, 835.933, "MUSIC: express feelings emotions", "A"),
        (1303.394, 1312.945, "NURSE: love so dearly had cancer", "B"),
        (1312.374, 1329.527, "NURSE: somebody understands you", "A"),
        (680.163, 695.779, "CLOSE: stay confident be yourself", "A"),
        (717.756, 720.009, "CLOSE: your journey is your journey", "A"),
        (721.120, 725.236, "CLOSE: break through anything", "B"),
    ]

    print("\n" + "="*60)
    print("TEST 1: Current v13 (should be clean)")
    print("="*60)
    w1 = lint_edit_list(EDIT_v13, all_words)
    print_lint_report(w1)

    print("\n" + "="*60)
    print("TEST 2: Old v12 order (should catch PERSONALITY interruption)")
    print("="*60)
    w2 = lint_edit_list(EDIT_v12_old, all_words)
    print_lint_report(w2)

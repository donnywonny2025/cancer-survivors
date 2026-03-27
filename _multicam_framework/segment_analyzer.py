#!/usr/bin/env python3
"""
Segment Analyzer — Semantic Understanding of Interview Content
===============================================================

Reads a WhisperX transcript and UNDERSTANDS what's being said.
Automatically:

  1. Breaks the interview into natural segments (by topic/speaker change)
  2. Tags each segment with a narrative arc label (IDENTITY, SIGNS, COST, etc.)
  3. Scores each segment on clarity, specificity, emotion, completeness
  4. Detects redundancy between segments
  5. Proposes the best candidate for each arc section

This replaces manual segment selection. The human reviews and adjusts,
but the machine does the heavy lifting intelligently.

Usage:
    python3 segment_analyzer.py /path/to/transcript.json
"""

import json
import os
import re
import sys
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# ============================================================
# THEME DETECTION — keyword patterns for each arc section
# ============================================================

THEME_PATTERNS = {
    "IDENTITY": {
        "keywords": {"name", "my name", "i'm", "i am", "diagnosed", "years old",
                     "lymphoma", "leukemia", "cancer", "hodgkin"},
        "context": ["introduction", "who they are"],
        "weight": 1.0,
    },
    "SIGNS": {
        "keywords": {"signs", "symptoms", "subtle", "swollen", "lymph nodes",
                     "fatigue", "fatigued", "drained", "night sweats", "lump",
                     "noticed", "felt off", "something wrong", "first signs"},
        "context": ["first indicators", "physical changes"],
        "weight": 1.0,
    },
    "MOMENT": {
        "keywords": {"knew", "realized", "moment", "went to", "got checked",
                     "checked out", "doctor", "hospital", "something wasn't right",
                     "active", "couldn't", "sleeping more", "weird"},
        "context": ["turning point", "realization"],
        "weight": 1.0,
    },
    "COST": {
        "keywords": {"lose", "lost", "affects", "confidence", "identity",
                     "self-identity", "routines", "relationship", "hard",
                     "difficult", "struggle", "isolation", "isolated",
                     "can't", "couldn't", "miss", "missed"},
        "context": ["what cancer took", "impact on life"],
        "weight": 1.0,
    },
    "POWER": {
        "keywords": {"fear", "overcome", "power", "taking power", "brave",
                     "strength", "strong", "fight", "fighting", "face",
                     "faced", "courage", "catch it early", "don't wait"},
        "context": ["empowerment", "facing fear"],
        "weight": 1.0,
    },
    "CHANGE": {
        "keywords": {"changed", "grown", "growth", "learned", "perspective",
                     "grateful", "grateful", "appreciate", "value",
                     "small days", "granted", "different person", "mentally"},
        "context": ["personal growth", "new perspective"],
        "weight": 1.0,
    },
    "MUSIC": {
        "keywords": {"music", "piano", "guitar", "sing", "songs", "writing",
                     "write", "art", "creative", "hobby", "sew", "sewing",
                     "express", "feelings", "emotions", "outlet"},
        "context": ["creative expression", "coping mechanism"],
        "weight": 1.0,
    },
    "NURSE": {
        "keywords": {"nurse", "nurses", "doctor", "support", "helped",
                     "care", "comforting", "comfortable", "understands",
                     "love", "dearly", "second mom", "family"},
        "context": ["support system", "medical care"],
        "weight": 1.0,
    },
    "CLOSE": {
        "keywords": {"advice", "tell them", "would say", "stay strong",
                     "confident", "be yourself", "journey", "advocate",
                     "break through", "you got this", "anyone going through"},
        "context": ["message to others", "closing advice"],
        "weight": 1.0,
    },
}

# Words/phrases that indicate the INTERVIEWER is speaking
INTERVIEWER_MARKERS = {
    "tell me", "can you", "would you say", "what would", "how did",
    "what was", "before you answer", "i'm going to", "just to introduce",
    "i'm risking", "one small adjustment", "do you want", "is there anything",
    "that's totally fine", "we can just", "let me see", "hold on",
}

# Words that indicate a stumble/restart
STUMBLE_MARKERS = {
    "sorry", "hold on", "let me", "can i start over",
    "what was the question", "oh my gosh", "bruh", "never mind",
}


# ============================================================
# SEGMENT DETECTION — break interview into natural chunks
# ============================================================

def detect_natural_segments(
    segments: List[Dict],
    min_duration: float = 3.0,
    max_duration: float = 25.0,
    pause_threshold: float = 2.0,
) -> List[Dict]:
    """
    Break transcript segments into natural speech chunks.
    Groups consecutive segments that flow together, splits on pauses.
    """
    if not segments:
        return []

    chunks = []
    current_chunk = {
        "start": segments[0].get("start", 0),
        "end": segments[0].get("end", 0),
        "text": segments[0].get("text", "").strip(),
        "segment_indices": [0],
    }

    for i in range(1, len(segments)):
        seg = segments[i]
        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        seg_text = seg.get("text", "").strip()

        if not seg_text:
            continue

        gap = seg_start - current_chunk["end"]
        chunk_duration = current_chunk["end"] - current_chunk["start"]

        # Split on long pauses or when chunk is getting too long
        if gap > pause_threshold or chunk_duration > max_duration:
            if chunk_duration >= min_duration:
                chunks.append(current_chunk)
            current_chunk = {
                "start": seg_start,
                "end": seg_end,
                "text": seg_text,
                "segment_indices": [i],
            }
        else:
            current_chunk["end"] = seg_end
            current_chunk["text"] += " " + seg_text
            current_chunk["segment_indices"].append(i)

    # Don't forget the last chunk
    if current_chunk["end"] - current_chunk["start"] >= min_duration:
        chunks.append(current_chunk)

    return chunks


# ============================================================
# THEME TAGGING
# ============================================================

def tag_theme(text: str) -> Tuple[str, float]:
    """
    Determine the most likely arc section for a piece of text.
    Returns (theme_label, confidence_score).
    """
    text_lower = text.lower()
    scores = {}

    for theme, config in THEME_PATTERNS.items():
        score = 0
        matches = []

        for kw in config["keywords"]:
            if kw in text_lower:
                # Multi-word keywords get higher weight
                weight = len(kw.split()) * 1.5
                score += weight
                matches.append(kw)

        scores[theme] = (score, matches)

    if not scores:
        return "UNKNOWN", 0.0

    best_theme = max(scores, key=lambda k: scores[k][0])
    best_score = scores[best_theme][0]

    # Normalize confidence to 0-1
    total_keywords = len(THEME_PATTERNS[best_theme]["keywords"])
    confidence = min(best_score / max(total_keywords * 0.5, 1), 1.0)

    return best_theme, confidence


# ============================================================
# SEGMENT SCORING
# ============================================================

def score_segment(text: str, words: List[Dict] = None) -> Dict[str, float]:
    """
    Score a segment on multiple quality dimensions.
    Each score is 0.0 - 1.0.
    """
    scores = {}
    text_lower = text.lower()

    # --- CLARITY: complete sentences, no stumbles ---
    stumble_count = sum(1 for m in STUMBLE_MARKERS if m in text_lower)
    interviewer_count = sum(1 for m in INTERVIEWER_MARKERS if m in text_lower)
    sentence_ends = text.count(".") + text.count("!") + text.count("?")
    word_count = len(text.split())

    clarity_penalty = (stumble_count * 0.2) + (interviewer_count * 0.3)
    scores["clarity"] = max(0, 1.0 - clarity_penalty)

    # --- SPECIFICITY: names, details, stories vs vague ---
    specific_markers = 0
    # Look for proper nouns (capitalized words not at sentence start)
    words_list = text.split()
    for j, w in enumerate(words_list):
        if j > 0 and w[0:1].isupper() and w.lower() not in {"i", "and", "but", "so"}:
            specific_markers += 1

    # Look for numbers
    specific_markers += len(re.findall(r'\d+', text))

    # Look for sensory/concrete language
    concrete_words = {"swollen", "sleep", "sleeping", "dance", "dancing",
                      "piano", "guitar", "sew", "write", "blood", "shots",
                      "crying", "tears", "smile", "laugh"}
    specific_markers += sum(1 for cw in concrete_words if cw in text_lower)

    scores["specificity"] = min(specific_markers / max(word_count * 0.15, 1), 1.0)

    # --- EMOTION: voice breaks, pauses, emotional language ---
    emotion_markers = {"sorry", "cry", "crying", "tears", "love", "dearly",
                       "appreciate", "scary", "scared", "hard", "difficult",
                       "grateful", "proud", "joy", "joyful", "fear", "power",
                       "strong", "brave"}
    emotion_count = sum(1 for em in emotion_markers if em in text_lower)
    scores["emotion"] = min(emotion_count / 3.0, 1.0)

    # --- COMPLETENESS: does the thought finish? ---
    if text.rstrip().endswith((".", "!", "?")):
        scores["completeness"] = 1.0
    elif text.rstrip().endswith(","):
        scores["completeness"] = 0.5
    else:
        scores["completeness"] = 0.3

    # --- CONCISENESS: says it in fewer words ---
    if word_count <= 15:
        scores["conciseness"] = 1.0
    elif word_count <= 30:
        scores["conciseness"] = 0.8
    elif word_count <= 50:
        scores["conciseness"] = 0.6
    else:
        scores["conciseness"] = 0.4

    # --- USABILITY: is this HER speaking, not the interviewer? ---
    if interviewer_count > 0:
        scores["usability"] = max(0, 0.5 - (interviewer_count * 0.2))
    elif stumble_count > 0:
        scores["usability"] = max(0.3, 0.8 - (stumble_count * 0.15))
    else:
        scores["usability"] = 1.0

    # --- COMPOSITE SCORE ---
    weights = {
        "clarity": 0.20,
        "specificity": 0.15,
        "emotion": 0.20,
        "completeness": 0.15,
        "conciseness": 0.10,
        "usability": 0.20,
    }
    scores["composite"] = sum(scores[k] * weights[k] for k in weights)

    return scores


# ============================================================
# REDUNDANCY DETECTION
# ============================================================

def detect_redundancy(candidates: List[Dict]) -> List[Tuple[int, int, float]]:
    """
    Find pairs of segments that express the same sentiment.
    Returns list of (idx_a, idx_b, similarity_score).
    """
    redundant = []

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if candidates[i]["theme"] != candidates[j]["theme"]:
                continue

            # Simple word-overlap similarity
            words_a = set(candidates[i]["text"].lower().split())
            words_b = set(candidates[j]["text"].lower().split())

            # Remove stop words
            stop = {"the", "a", "an", "is", "was", "were", "are", "and",
                    "but", "or", "so", "to", "of", "in", "for", "it",
                    "that", "this", "i", "my", "me", "you", "like"}
            words_a -= stop
            words_b -= stop

            if not words_a or not words_b:
                continue

            overlap = words_a & words_b
            similarity = len(overlap) / min(len(words_a), len(words_b))

            if similarity > 0.4:
                redundant.append((i, j, similarity))

    return redundant


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_transcript(transcript_path: str) -> Dict:
    """
    Full analysis of a transcript file.
    Returns a structured report with candidates for each arc section.
    """
    with open(transcript_path) as f:
        data = json.load(f)

    segments = data.get("segments", [])
    all_words = []
    for seg in segments:
        for w in seg.get("words", []):
            if "start" in w:
                all_words.append(w)
    all_words.sort(key=lambda w: w["start"])

    # Step 1: Break into natural chunks
    chunks = detect_natural_segments(segments)

    # Step 2: Analyze each chunk
    candidates = []
    for chunk in chunks:
        theme, confidence = tag_theme(chunk["text"])
        scores = score_segment(chunk["text"])

        candidates.append({
            "start": chunk["start"],
            "end": chunk["end"],
            "duration": chunk["end"] - chunk["start"],
            "text": chunk["text"],
            "theme": theme,
            "theme_confidence": confidence,
            "scores": scores,
        })

    # Step 3: Group by theme
    by_theme = defaultdict(list)
    for i, c in enumerate(candidates):
        c["index"] = i
        by_theme[c["theme"]].append(c)

    # Step 4: Rank within each theme
    best_per_theme = {}
    for theme, theme_candidates in by_theme.items():
        # Sort by composite score (descending)
        ranked = sorted(theme_candidates, key=lambda c: c["scores"]["composite"], reverse=True)
        best_per_theme[theme] = ranked

    # Step 5: Detect redundancy
    redundant_pairs = detect_redundancy(candidates)

    return {
        "total_chunks": len(chunks),
        "total_candidates": len(candidates),
        "candidates": candidates,
        "by_theme": dict(by_theme),
        "best_per_theme": best_per_theme,
        "redundant_pairs": redundant_pairs,
    }


def print_analysis_report(result: Dict):
    """Print a human-readable analysis report."""
    print(f"\n{'='*70}")
    print(f"SEMANTIC SEGMENT ANALYSIS")
    print(f"{'='*70}")
    print(f"Total chunks detected: {result['total_chunks']}")
    print(f"Total candidates: {result['total_candidates']}")

    # Show best candidate per theme
    arc_order = ["IDENTITY", "SIGNS", "MOMENT", "COST", "POWER",
                 "CHANGE", "MUSIC", "NURSE", "CLOSE"]

    print(f"\n{'='*70}")
    print(f"BEST CANDIDATES PER ARC SECTION")
    print(f"{'='*70}")

    for theme in arc_order:
        candidates = result["best_per_theme"].get(theme, [])
        if not candidates:
            print(f"\n❌ {theme}: NO CANDIDATES FOUND")
            continue

        best = candidates[0]
        s = best["scores"]
        print(f"\n🏆 {theme} (best of {len(candidates)} candidates)")
        print(f"   Score: {s['composite']:.2f} | "
              f"Clarity={s['clarity']:.1f} Emotion={s['emotion']:.1f} "
              f"Specific={s['specificity']:.1f} Complete={s['completeness']:.1f} "
              f"Usable={s['usability']:.1f}")
        print(f"   Time: [{best['start']:.1f}s - {best['end']:.1f}s] ({best['duration']:.1f}s)")
        print(f"   \"{best['text'][:150]}\"")

        # Show runners-up
        for alt in candidates[1:3]:
            sa = alt["scores"]
            print(f"   ├─ Alt ({sa['composite']:.2f}): [{alt['start']:.1f}-{alt['end']:.1f}s] "
                  f"\"{alt['text'][:80]}\"")

    # Show themes with no candidates
    missing = [t for t in arc_order if t not in result["best_per_theme"]]
    if missing:
        print(f"\n⚠️  Missing themes: {', '.join(missing)}")

    # Show redundancy
    if result["redundant_pairs"]:
        print(f"\n{'='*70}")
        print(f"REDUNDANCY DETECTED")
        print(f"{'='*70}")
        for i, j, sim in result["redundant_pairs"][:5]:
            ca = result["candidates"][i]
            cb = result["candidates"][j]
            print(f"  {ca['theme']} segments {i+1} & {j+1} ({sim:.0%} overlap)")
            print(f"    A: \"{ca['text'][:80]}\"")
            print(f"    B: \"{cb['text'][:80]}\"")

    # Show UNKNOWN/uncategorized
    unknowns = result["best_per_theme"].get("UNKNOWN", [])
    if unknowns:
        print(f"\n{'='*70}")
        print(f"UNCATEGORIZED SEGMENTS ({len(unknowns)})")
        print(f"{'='*70}")
        for u in unknowns[:5]:
            print(f"  [{u['start']:.1f}-{u['end']:.1f}s] \"{u['text'][:100]}\"")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
    transcript = os.path.join(BASE, "Master_S34_Transcript_WhisperX.json")

    if not os.path.exists(transcript):
        print(f"ERROR: Transcript not found: {transcript}")
        sys.exit(1)

    result = analyze_transcript(transcript)
    print_analysis_report(result)

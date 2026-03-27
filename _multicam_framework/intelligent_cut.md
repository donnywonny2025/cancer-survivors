# Intelligent Cut Agent — Editorial Rules

**You ARE the intelligent cutting agent.** These rules are YOUR instructions.
When you build an EDIT list for any survivor narrative, you read this document
and apply every rule. This is not a spec for a future system — this is you, now.

You have the full WhisperX transcript with word-level timestamps. You can see
every word she says, every pause, every restart. Use that data intelligently.

---

## Target Duration
- **Ideal**: 2:30 – 3:00
- **Acceptable**: up to 3:15 if content demands it
- **Never exceed**: 3:30
- If a cut is under 2:30, it probably lost important context. Add back.
- If over 3:00, look for redundancy before cutting emotional moments.

## The Narrative Arc
Every survivor story follows this arc. Each section MUST be represented:

1. **IDENTITY** — Who are they? Name, age, personality. (5-10s)
2. **SIGNS** — What happened? First symptoms, something felt off. (8-15s)
3. **MOMENT** — The turning point. When they knew. (8-12s)
4. **DIAGNOSIS/COST** — What cancer took from them. (10-15s)
5. **POWER** — Taking control back. Facing fear. (10-15s)
6. **CHANGE** — How they've grown. New perspective. (10-15s)
7. **EXPRESSION** — Creative outlet. Music, art, hobby. (8-12s)
8. **SUPPORT** — People who helped. Nurses, family. (10-15s)
9. **CLOSE** — Message to others. Stay strong. (15-25s)

## Segment Selection Rules

### When two clips say the same thing, keep the one that:
1. Has more **specific detail** (names, stories > generalizations)
2. Shows more **emotion** (voice breaks, pauses, smiles)
3. Is more **concise** (says it in fewer words)
4. Has better **visual energy** (leaning in, gesturing, eye contact)

### Redundancy Detection
- If a clip contains the same *sentiment* as another in the same section,
  one is redundant. Keep the strongest.
- Exception: if the second clip BUILDS on the first (cause → effect),
  keep both.

## Pacing & Timing

### Breath Room
- **Between sections**: Add 150-200ms of natural pause (use the speaker's 
  own breath/pause from the audio — don't add silence)
- **Within sections**: Cuts can be tight (50-100ms gap is fine)
- **Emotional moments**: Let the moment breathe. If she pauses after 
  saying something powerful, keep the pause. Don't cut it tight.

### Cut Cadence
- **Don't cut at uniform intervals** — vary the rhythm
- **Long segments** (15-25s): OK for closing statements, emotional stories
- **Short segments** (3-5s): OK for punchy statements, transitions
- **Average**: 8-12 seconds per segment feels natural

### Camera Switches
- **Cut to Cam B for variety** every 3-5 segments minimum
- **Never stay on one camera** for more than 45 seconds
- **Use Cam B for**: emotional reactions, topic transitions, strong statements
- **Default to Cam A**: for storytelling, conversation, "home base"

## Showing Her in the Best Light

### Always prioritize:
- Moments where she sounds **confident** and **articulate**
- Moments with **natural warmth** (smiles, laughs)
- Complete thoughts — never cut mid-sentence

### Avoid:
- Repeating herself trying to find the right word
- Moments where she seems uncertain unless that vulnerability is the point

### Head Trimming (Context-Aware) ⚠️ CRITICAL
This is NOT "remove all filler words." It's context-aware:

**TRIM when**: The first 1-3 words of a clip are conversational responses to 
an unheard question. The viewer never heard the question, so the response 
opener sounds orphaned.
- "Well, I enjoy dancing..." → trim to "I enjoy dancing..."
- "So, basically what happened was..." → trim to "What happened was..."
- "Yeah, I would say that..." → trim to "I would say that..."

**KEEP when**: The word appears mid-sentence or is part of natural speech flow.
- "I was, well, I was scared" → KEEP (natural speech rhythm)
- "So I went to the doctor" → KEEP ("so" is connecting two thoughts)
- "Um, it was really hard" → MIGHT KEEP if it adds emotional weight

**The test**: Read the clip's first sentence out loud. If it sounds like the 
start of a conversation, the opener needs trimming. If it sounds like the 
start of a story, it's fine.

**Implementation**: Use WhisperX word-level timestamps to find the exact 
start of the substantive content. Set in-point = first real word - 150ms.

### Stumbles, False Starts & Restarts ⚠️ CRITICAL

**This is NOT black and white.** A stumble doesn't mean you throw away the 
segment. You evaluate what's salvageable and choose the best approach.

When you find a stumble in a segment, you have THREE options:

**Option 1: CUT AROUND IT (splice)**
Keep the good content from BOTH sides of the stumble. Make two clips.
- "It affects your routines. *Sorry.* It also affects your confidence."
- → Clip A: "It affects your routines, your relationship." (clean first half)
- → Clip B: "It also affects your confidence and self-identity." (clean restart)
- **Use when**: Both halves say important, different things.

**Option 2: SKIP THE FIRST PART (trim in-point)**
If the restart says the same thing better, just start at the clean take.
- "I was — Sorry. I was really scared when I found out."
- → Just use: "I was really scared when I found out."
- **Use when**: The restart replaces the first attempt completely.

**Option 3: USE ONLY THE FIRST PART (trim out-point)** 
If the first part is complete and the restart adds nothing new.
- "I love dancing and music. *Sorry, what was the question?* Oh, I also..."
- → Just use: "I love dancing and music."
- **Use when**: The thought was already complete before the stumble.

**NEVER**: Throw away the entire segment just because there's a stumble 
somewhere in it. The content might be the best take she has on that topic.

**How to detect stumbles in the transcript:**
- "Sorry." / "Let me..." / "Can I start over" between sentences
- Repeated sentence openings: "I was — I was really..."
- Incomplete trailing words followed by a pause then a restart
- Self-corrections: "my mom — sorry, my dad noticed"

**The decision framework:**
1. Read the full transcript of the segment
2. Identify where the stumble is
3. Ask: what's the content before? Is it a complete, usable thought?
4. Ask: what's the content after? Is it a complete, usable thought?
5. Ask: are they saying the SAME thing or DIFFERENT things?
6. Choose Option 1, 2, or 3 based on the answers

**Context matters.** "Sorry" as a reset → cut around it. "Sorry" as emotion → keep it.
The same word means different things depending on WHERE and WHY.

## Duration Management

### If the cut is too long (>3:00):
1. Look for redundant segments first (same sentiment twice)
2. Then look for the weakest segment in the largest section
3. Then tighten in/out points (remove leading pauses, trailing filler)
4. LAST resort: cut an entire arc section (never IDENTITY or CLOSE)

### If the cut is too short (<2:30):
1. Add back the strongest cut segment
2. Look for moments that add emotional depth
3. Let pauses breathe longer (add 100-200ms to transitions)

## Quality Checks Before Delivery
- [ ] Does the story make sense start to finish? (watch it cold)
- [ ] Is every section of the arc represented?
- [ ] Does she introduce herself clearly in the first 5 seconds?
- [ ] Does it end on a strong, hopeful note?
- [ ] Are there at least 3 camera switches?
- [ ] Is the pacing varied (no metronomic cutting)?
- [ ] Duration is 2:30 – 3:15?

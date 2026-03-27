# Multicam Podcast Editing Rules

## The Cardinal Rule
**If someone is talking, show them.** Even a 1-second interjection gets a cut. The viewer needs to see who's speaking.

## When to Cut

### Always Cut To:
- **The person who starts talking** — cut on the first word, not after a delay
- **A new speaker in a back-and-forth** — dialogue exchanges should bounce between close-ups
- **A reaction** — if someone laughs, gasps, or reacts visibly, briefly show them

### Use the Wide Shot For:
- **Opening** — establish the scene, show both people
- **Topic transitions** — give the viewer a "reset" between subjects
- **Crosstalk** — when both people talk at once
- **Long pauses** — when nobody's talking, wide feels natural

### Hold Times
- **Minimum hold for a speaking segment:** 1 second (even short interjections get shown)
- **Minimum hold before cutting to a reaction:** 2 seconds into the speaker's line
- **Don't cut for filler:** If someone just says "mm-hmm" or "yeah" as agreement, stay on the speaker

## Pacing Guidelines
- **Average cut rate:** 1 cut every 8-15 seconds for a conversational podcast
- **Vary the rhythm:** Don't cut at the same interval every time
- **Let long stories breathe:** If someone is telling a story, don't cut away from them just because it's been 30 seconds

## Audio Track Rules
- **A1 (Cam A scratch) = MUTED** — reference only, never the active audio
- **A2 (Cam B scratch) = MUTED** — reference only, never the active audio
- **A3 (TASCAM master) = UNMUTED** — this is the real audio, always active
- This is the professional standard. Scratch audio exists for sync verification only.

## XML Generation Rules
- **ALWAYS use the L.append() line-by-line pattern** from `gen_multicam_v34_2.py`
- **NEVER use helper functions with positional arguments** for XMEML output (see BUG-001)
- **Multiple sequences** can go in one XML under the same `<xmeml>` root tag
- Bundle Golden Layout + selects + narrative cuts in one XML for rough edit delivery
- File definitions go in the FIRST clipitem with inline `<file>` block; subsequent clips use `<file id="..."/>`

## Common Mistakes
- Cutting too late (showing the listener when the speaker starts talking)
- Never showing reactions (feels like a slide show)
- Cutting mid-sentence when the same person is still talking
- Using wide shot too much (podcast = intimacy = close-ups)
- Using shortcut XML generators instead of the proven L.append pattern

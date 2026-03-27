# Multicam Edit Framework

This framework provides AI-driven tools for syncing and auto-cutting multicam video interviews in Adobe Premiere Pro.

## Framework Components

- `xcorr_fast.py`: Uses FFT cross-correlation to find frame-accurate sync offsets between camera scratch audio and master microphone recordings.
- `gen_multicam_v2.py`: Generates a Premiere Pro XML (XMEML v4) file with all camera and audio tracks perfectly synced.
- `autocut.py`: Analyzes waveform energy to determine who is speaking and generates a rough-cut XML with automatic camera switching.
- `autocut_intelligent.py`: Advanced auto-cutter that uses editorial rules (pacing, reaction shots) to create a more natural edit.
- `editing_rules.md`: Technical and creative guidelines for the AI agent to follow when making cuts.
- `AI_VIDEO_EDITOR_REFERENCE.md`: Full technical reference for the system architecture.

## How to Use for a New Project (e.g., Vince or Zamiyah)

1. **Locate Media**: Ensure all footage (Cam A, Cam B, etc.) and master audio (WAV files) are organized in their respective folders.
2. **Find Sync Offsets**: Run `xcorr_fast.py` to get the offsets for each clip.
3. **Configure Scripts**: Open `gen_multicam_v2.py` or `autocut.py` and update the `BASE`, `AUDIO_BASE`, and `tracks` variables at the top of the file.
4. **Generate XML**: Run the script to produce an `.xml` file.
5. **Import to Premiere**: Drag the generated XML into your Premiere Pro project.

## Dependencies

- Python 3
- `numpy`
- `ffmpeg` / `ffprobe` (must be in your PATH)

# Zamiyah Multicam Project

## Project Overview
A two-camera UHD multicam interview synchronized to TASCAM S34 master audio.

## Technical Standards
- **Resolution**: 3840x2160 (UHD)
- **Sequence Rate**: 29.97 Drop-Frame (DF)
- **Audio Sample Rate**: 48kHz / 16-bit
- **Reference Timebase**: 30fps (Time-Absolute)

## Synchronization Baseline (v34.2)
The project uses the **"TASCAM North Star"** method. The TASCAM audio file is placed at Timeline `0.0`, and all cameras are trimmed to match.

| Media | File | Sync Offset (Trim) | 30fps Frame Count |
| :--- | :--- | :--- | :--- |
| **Cam A** | `C8826.MP4` | +63.3s | 1897f |
| **Cam B** | `C8890.MP4` | +75.8s | 2274f |
| **Audio** | `TASCAM_1087S34.wav` | 0.0s | 0f |

## Editorial Track Layout (Golden Layout)
- **V1 / A1**: Camera A (Host)
- **V2 / A2**: Camera B (Guest)
- **A3**: **TASCAM Master Mix**

## Automated Cutting
The `sync_scripts/autocut_zamiyah_final.py` script utilizes the `Master_S34_Transcript.json` to generate an automated editorial cut:
- **Host Speak** -> Switch to Camera A
- **Guest Answer** -> Switch to Camera B

## History & Troubleshooting
For a detailed forensic analysis of the sync issues (including the resolution of the 23.976fps/29.97fps drift conflict), refer to the **`SANDBOX/README.md`** post-mortem.

# 🚀 START HERE: Zamiyah Multicam Sync Engine

This folder contains the **Forensic Multicam Pipeline**. It is designed to be a "Zero-Guess" system that autonomously syncs mixed frame-rate footage to a TASCAM master audio file.

## 🏁 The Forensic Workflow (The Audit)
There is no "Magic Sync" button. This folder is a **Forensic Toolkit** built to assist our combined analysis. To start a sync audit:
1.  **Define the Assets**: Open `configs/sync_config.json` and point the system to your current Cam A, Cam B, and Tascam media.
2.  **Request an Analysis**: Ask Antigravity: *"Perform a forensic scan of the START_HERE folder."*
3.  **The Engine provides the Evidence**:
    - **Metadata Scan**: ffprobe extraction of frame rates (detecting 24/30 conflicts).
    - **Transcript Anchor**: Word-level timeline matching.
    - **Waveform Refinement**: FFT peak analysis.
4.  **The Assembly**: A proposed XML is generated using the **Golden Layout (v34.2 Standard)**.

### ⚠️ The Golden Rule: THINK FIRST
**Always verify the waveforms in Premiere immediately after import.** A script is only a tool; your visual alignment in the timeline is the ultimate source of truth.

## 📜 The Forensic Sync Bible
This folder contains the permanent record of our struggles with this project. 
Read **`FORENSIC_HISTORY.md`** to understand the "15-Second Drift" and why we MUST use the **30fps Absolute Frame** rule for these specific cameras.

## 🏗 The Golden Layout (Final Audit)
The engine is programmed to enforce your project standard:
- **V1/A1**: Camera A (The Master/Host)
- **V2/A2**: Camera B (The Cut-away/Guest)
- **A3**: **TASCAM Master Audio (Zero-Anchor)**

---
**Status**: PRODUCTION READY | **Standard**: V34.2 Golden 

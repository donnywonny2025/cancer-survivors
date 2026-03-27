#!/usr/bin/env python3
"""
Speech Onset Detector — Core Framework Module
================================================
Finds the exact audio frame where speech energy begins,
correcting Whisper's approximate word timestamps.

Method: Locates the energy minimum (breath gap) before the
Whisper timestamp, then finds where energy rises from that
minimum toward speech. Works in noisy rooms with ambient sound.

Usage:
    from onset_detector import find_onset, find_offset
    true_start = find_onset(audio_path, whisper_timestamp)
    true_end   = find_offset(audio_path, whisper_timestamp)
"""

import numpy as np
import wave
import struct


def read_wav_segment(wav_path, start_sec, end_sec):
    """Read a segment of a WAV file, returns (samples_array, sample_rate)."""
    with wave.open(wav_path, 'r') as wf:
        sr = wf.getframerate()
        nch = wf.getnchannels()
        sw = wf.getsampwidth()

        start_frame = max(0, int(start_sec * sr))
        end_frame = int(end_sec * sr)

        wf.setpos(start_frame)
        n_frames = end_frame - start_frame
        raw = wf.readframes(n_frames)

        if sw == 2:
            fmt = f"<{n_frames * nch}h"
            samples = np.array(struct.unpack(fmt, raw), dtype=np.float64)
        elif sw == 3:
            samples = []
            for i in range(0, len(raw), 3):
                val = raw[i] | (raw[i+1] << 8) | (raw[i+2] << 16)
                if val >= 0x800000:
                    val -= 0x1000000
                samples.append(val)
            samples = np.array(samples, dtype=np.float64)
        else:
            fmt = f"<{n_frames * nch}h"
            samples = np.array(struct.unpack(fmt, raw), dtype=np.float64)

        if nch > 1:
            samples = samples.reshape(-1, nch).mean(axis=1)

        return samples, sr


def compute_energy(samples, frame_size, hop_size):
    """Compute short-time RMS energy."""
    energy = []
    for i in range(0, len(samples) - frame_size, hop_size):
        frame = samples[i:i+frame_size]
        energy.append(np.sqrt(np.mean(frame**2)))
    return np.array(energy)


def find_onset(wav_path, whisper_time, search_window=0.3):
    """
    Find the true speech onset before a Whisper word timestamp.
    
    Locates the energy minimum (breath gap) in the window before
    the timestamp, then finds where energy rises from that minimum.
    
    Returns: precise onset time in seconds (always <= whisper_time)
    """
    search_start = max(0, whisper_time - search_window)
    search_end = whisper_time + 0.05

    samples, sr = read_wav_segment(wav_path, search_start, search_end)
    hop = int(sr * 0.002)       # 2ms hop for fine resolution
    frame_sz = int(sr * 0.008)  # 8ms frame

    energy = compute_energy(samples, frame_sz, hop)
    if len(energy) < 5:
        return whisper_time

    whisper_idx = min(int((whisper_time - search_start) * sr / hop), len(energy) - 1)
    if whisper_idx <= 0:
        return whisper_time

    # Find energy minimum before whisper_time (the breath gap)
    min_idx = int(np.argmin(energy[:whisper_idx]))
    min_energy = energy[min_idx]

    # Find where energy rises to 50% between min and whisper point
    whisper_energy = energy[whisper_idx]
    half_rise = min_energy + 0.5 * (whisper_energy - min_energy)

    onset_idx = min_idx
    for i in range(min_idx, whisper_idx):
        if energy[i] >= half_rise:
            onset_idx = i
            break

    # Back up 2 frames (~4ms) to catch the very start of the consonant
    onset_idx = max(0, onset_idx - 2)

    onset_time = search_start + (onset_idx * hop / sr)
    return min(onset_time, whisper_time)


def find_offset(wav_path, whisper_time, search_window=0.3):
    """
    Find the true speech offset after a Whisper word end timestamp.
    
    Returns: precise offset time in seconds (always >= whisper_time)
    """
    search_start = whisper_time - 0.05
    search_end = whisper_time + search_window

    samples, sr = read_wav_segment(wav_path, search_start, search_end)
    hop = int(sr * 0.002)
    frame_sz = int(sr * 0.008)

    energy = compute_energy(samples, frame_sz, hop)
    if len(energy) < 5:
        return whisper_time

    whisper_idx = min(int((whisper_time - search_start) * sr / hop), len(energy) - 1)
    if whisper_idx >= len(energy) - 1:
        return whisper_time

    # Find energy minimum AFTER whisper_time
    min_idx = int(np.argmin(energy[whisper_idx:])) + whisper_idx
    min_energy = energy[min_idx]

    # Find where energy drops to 50% between whisper point and min
    whisper_energy = energy[whisper_idx]
    half_drop = whisper_energy - 0.5 * (whisper_energy - min_energy)

    offset_idx = min_idx
    for i in range(whisper_idx, min_idx + 1):
        if energy[i] <= half_drop:
            offset_idx = i
            break

    # Add 2 frames (~4ms) to catch the tail
    offset_idx = min(len(energy) - 1, offset_idx + 2)

    offset_time = search_start + (offset_idx * hop / sr)
    return max(offset_time, whisper_time)

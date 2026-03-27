#!/usr/bin/env python3
"""
Speech Onset Detector — Core Framework Module v2
=================================================
Uses actual waveform energy to find where speech starts.
Room noise baseline vs speech energy spike detection.

Noise floor: ~50-100k | Speech: ~500k-1M+
The detector finds the SPIKE, then backs up for consonant onset.
"""

import numpy as np
import wave
import struct


def read_wav_segment(wav_path, start_sec, end_sec):
    """Read a segment of a WAV file."""
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
            samples = np.array(struct.unpack(f"<{n_frames * nch}h", raw), dtype=np.float64)
        elif sw == 3:
            samples = []
            for i in range(0, len(raw), 3):
                val = raw[i] | (raw[i+1] << 8) | (raw[i+2] << 16)
                if val >= 0x800000:
                    val -= 0x1000000
                samples.append(val)
            samples = np.array(samples, dtype=np.float64)
        else:
            samples = np.array(struct.unpack(f"<{n_frames * nch}h", raw), dtype=np.float64)
        if nch > 1:
            samples = samples.reshape(-1, nch).mean(axis=1)
        return samples, sr


def compute_energy(samples, frame_size, hop_size):
    """Compute short-time RMS energy."""
    energy = []
    for i in range(0, len(samples) - frame_size, hop_size):
        frame = samples[i:i + frame_size]
        energy.append(np.sqrt(np.mean(frame ** 2)))
    return np.array(energy)


def find_onset(wav_path, whisper_time, search_window=1.0, pre_speech_pad=0.1):
    """
    Find where speech actually starts using energy spike detection.
    
    1. Measures room noise baseline from the start of the search window
    2. Finds the first energy SPIKE that's 3x above noise (= speech)
    3. Backs up pre_speech_pad seconds for consonant onset
    
    Returns: precise onset time in seconds
    """
    search_start = max(0, whisper_time - search_window)
    search_end = whisper_time + 0.5

    samples, sr = read_wav_segment(wav_path, search_start, search_end)
    hop = int(sr * 0.005)       # 5ms hop
    frame_sz = int(sr * 0.01)   # 10ms frame

    energy = compute_energy(samples, frame_sz, hop)
    if len(energy) < 10:
        return whisper_time

    # Measure noise baseline from first 20% of window (before speech)
    baseline_end = max(10, int(len(energy) * 0.2))
    noise_baseline = np.median(energy[:baseline_end])

    # Speech threshold: 3x noise baseline
    speech_threshold = noise_baseline * 3.0

    # Find first frame where energy exceeds speech threshold
    spike_idx = None
    for i in range(len(energy)):
        if energy[i] > speech_threshold:
            spike_idx = i
            break

    if spike_idx is None:
        return whisper_time

    # Convert spike to time
    spike_time = search_start + (spike_idx * hop / sr)

    # Back up for consonant onset (H, S, T etc start before the vowel spike)
    onset_time = spike_time - pre_speech_pad

    # Never go before the search window start
    onset_time = max(search_start, onset_time)

    return onset_time


def find_offset(wav_path, whisper_time, search_window=0.5, post_speech_pad=0.05):
    """
    Find where speech actually ends using energy drop detection.
    
    Returns: precise offset time in seconds
    """
    search_start = whisper_time - 0.1
    search_end = whisper_time + search_window

    samples, sr = read_wav_segment(wav_path, search_start, search_end)
    hop = int(sr * 0.005)
    frame_sz = int(sr * 0.01)

    energy = compute_energy(samples, frame_sz, hop)
    if len(energy) < 10:
        return whisper_time

    # Measure noise from last 20% of window (after speech)
    baseline_start = int(len(energy) * 0.8)
    noise_baseline = np.median(energy[baseline_start:])

    speech_threshold = noise_baseline * 3.0

    # Find LAST frame where energy exceeds speech threshold
    drop_idx = None
    for i in range(len(energy) - 1, -1, -1):
        if energy[i] > speech_threshold:
            drop_idx = i
            break

    if drop_idx is None:
        return whisper_time

    drop_time = search_start + (drop_idx * hop / sr)
    offset_time = drop_time + post_speech_pad

    return max(offset_time, whisper_time)

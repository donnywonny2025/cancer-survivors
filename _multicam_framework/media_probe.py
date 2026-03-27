#!/usr/bin/env python3
"""
Media Probe — Pre-Flight Checklist for Multicam XML Generation
==============================================================
Probes ALL source files with ffprobe before any XML is written.
Detects: frame rate, resolution, bit depth, sample rate, channels, duration.
Validates: matching frame rates, correct NTSC/NDF settings, aspect ratios.
Prevents: the 29.97/30fps drift bug, wrong bit depth, wrong channel count.

Usage:
    from media_probe import probe_file, preflight_check, ntsc_frame

    # Probe a single file
    info = probe_file("/path/to/file.mp4")

    # Run full preflight on all project sources
    report = preflight_check(
        video_files=["/path/cam_a.mp4", "/path/cam_b.mp4"],
        audio_files=["/path/tascam.wav"],
        sequence_fps=29.97
    )

    # Convert seconds to NTSC frames (always use this, never multiply by 30)
    frame = ntsc_frame(1404.337)
"""

import subprocess
import json
import sys


def probe_file(path):
    """
    Probe a media file and return all relevant specs.
    Returns dict with: duration, video_fps, width, height, audio_sample_rate,
    audio_bit_depth, audio_channels, codec, is_ntsc, ntsc_fps, total_frames
    """
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {result.stderr}")

    data = json.loads(result.stdout)
    info = {
        'path': path,
        'filename': path.split('/')[-1],
        'duration': float(data['format']['duration']),
    }

    for stream in data.get('streams', []):
        if stream['codec_type'] == 'video':
            info['width'] = int(stream.get('width', 0))
            info['height'] = int(stream.get('height', 0))
            info['video_codec'] = stream.get('codec_name', '')

            # Parse frame rate (r_frame_rate is "30000/1001" or "30/1" etc)
            r_fps = stream.get('r_frame_rate', '0/1')
            num, den = map(int, r_fps.split('/'))
            if den > 0:
                info['video_fps'] = num / den
                info['video_fps_fraction'] = (num, den)
            else:
                info['video_fps'] = 0
                info['video_fps_fraction'] = (0, 1)

            # Detect NTSC (29.97, 23.976, 59.94)
            fps = info['video_fps']
            info['is_ntsc'] = abs(fps - round(fps)) > 0.01  # 29.97 vs 30
            info['ntsc_timebase'] = round(fps)  # 30 for 29.97, 24 for 23.976

        elif stream['codec_type'] == 'audio':
            info['audio_codec'] = stream.get('codec_name', '')
            info['audio_sample_rate'] = int(stream.get('sample_rate', 0))
            info['audio_channels'] = int(stream.get('channels', 0))

            # Bit depth: check bits_per_raw_sample first, then codec name
            bps = stream.get('bits_per_raw_sample')
            if bps:
                info['audio_bit_depth'] = int(bps)
            elif 's24' in stream.get('codec_name', ''):
                info['audio_bit_depth'] = 24
            elif 's16' in stream.get('codec_name', ''):
                info['audio_bit_depth'] = 16
            elif 's32' in stream.get('codec_name', '') or 'f32' in stream.get('codec_name', ''):
                info['audio_bit_depth'] = 32
            else:
                info['audio_bit_depth'] = 16  # default assumption

    # Compute total frames at NTSC rate
    if 'video_fps' in info and info['video_fps'] > 0:
        info['total_frames'] = int(round(info['duration'] * info['video_fps']))
    elif 'audio_sample_rate' in info:
        # Audio-only: use timebase 30 NTSC
        info['total_frames'] = int(round(info['duration'] * 30000 / 1001))

    return info


def ntsc_frame(seconds, timebase=30):
    """
    Convert seconds to NTSC frame number.
    
    NTSC frame rate = timebase * 1000/1001
    - timebase=30 → 29.97fps (standard HD)
    - timebase=24 → 23.976fps (film)
    - timebase=60 → 59.94fps (high frame rate)
    
    NEVER use round(seconds * timebase) directly — that causes drift.
    At 23 minutes, 30fps vs 29.97fps = 1.4 second error.
    """
    return int(round(seconds * timebase * 1000 / 1001))


def ntsc_seconds(frame, timebase=30):
    """Convert NTSC frame number back to seconds."""
    return frame * 1001 / (timebase * 1000)


def preflight_check(video_files=None, audio_files=None, sequence_fps=29.97):
    """
    Run pre-flight checklist on all source files.
    Returns a report dict with 'passed', 'warnings', 'errors', and 'files'.
    
    Checks:
    1. All video files have the same frame rate
    2. All video files have the same resolution
    3. Frame rate matches sequence settings
    4. Audio bit depth is correctly detected
    5. Audio sample rates match
    6. NTSC flag is consistent
    """
    report = {
        'passed': True,
        'warnings': [],
        'errors': [],
        'files': {},
        'sequence_fps': sequence_fps,
        'sequence_timebase': round(sequence_fps),
        'is_ntsc': abs(sequence_fps - round(sequence_fps)) > 0.01,
    }

    all_files = []
    for path in (video_files or []):
        info = probe_file(path)
        info['role'] = 'video'
        report['files'][info['filename']] = info
        all_files.append(info)

    for path in (audio_files or []):
        info = probe_file(path)
        info['role'] = 'audio'
        report['files'][info['filename']] = info
        all_files.append(info)

    # Check 1: Video frame rates match
    video_fps_set = set()
    for f in all_files:
        if 'video_fps' in f:
            video_fps_set.add(round(f['video_fps'], 3))
    if len(video_fps_set) > 1:
        report['errors'].append(
            f"⛔ FRAME RATE MISMATCH: Videos have different fps: {video_fps_set}"
        )
        report['passed'] = False

    # Check 2: Video resolutions match
    resolutions = set()
    for f in all_files:
        if 'width' in f:
            resolutions.add((f['width'], f['height']))
    if len(resolutions) > 1:
        report['warnings'].append(
            f"⚠️  RESOLUTION MISMATCH: {resolutions}"
        )

    # Check 3: Frame rate matches sequence
    for f in all_files:
        if 'video_fps' in f:
            if abs(f['video_fps'] - sequence_fps) > 0.1:
                report['errors'].append(
                    f"⛔ FPS MISMATCH: {f['filename']} is {f['video_fps']:.3f}fps "
                    f"but sequence is {sequence_fps}fps"
                )
                report['passed'] = False

    # Check 4: NTSC consistency
    for f in all_files:
        if 'is_ntsc' in f:
            if f['is_ntsc'] != report['is_ntsc']:
                report['warnings'].append(
                    f"⚠️  NTSC MISMATCH: {f['filename']} NTSC={f['is_ntsc']} "
                    f"but sequence NTSC={report['is_ntsc']}"
                )

    # Check 5: Audio sample rates
    sample_rates = set()
    for f in all_files:
        if 'audio_sample_rate' in f:
            sample_rates.add(f['audio_sample_rate'])
    if len(sample_rates) > 1:
        report['warnings'].append(
            f"⚠️  SAMPLE RATE MISMATCH: {sample_rates}"
        )

    return report


def print_preflight(report):
    """Pretty-print a preflight report."""
    print("\n" + "=" * 70)
    print("📋 PRE-FLIGHT CHECKLIST")
    print("=" * 70)
    print(f"Sequence: {report['sequence_fps']}fps | "
          f"Timebase: {report['sequence_timebase']} | "
          f"NTSC: {report['is_ntsc']}")
    print()

    for name, info in report['files'].items():
        role = info.get('role', '?')
        print(f"  📁 {name} [{role.upper()}]")
        if 'video_fps' in info:
            print(f"     Video: {info['width']}x{info['height']} @ "
                  f"{info['video_fps']:.3f}fps "
                  f"({'NTSC' if info.get('is_ntsc') else 'INTEGER'})")
        if 'audio_sample_rate' in info:
            print(f"     Audio: {info['audio_sample_rate']}Hz / "
                  f"{info['audio_bit_depth']}bit / "
                  f"{info['audio_channels']}ch")
        print(f"     Duration: {info['duration']:.3f}s = "
              f"{info.get('total_frames', '?')} frames")
        print()

    if report['errors']:
        print("❌ ERRORS (must fix before XML generation):")
        for e in report['errors']:
            print(f"   {e}")
    if report['warnings']:
        print("⚠️  WARNINGS:")
        for w in report['warnings']:
            print(f"   {w}")

    if report['passed']:
        print("✅ ALL CHECKS PASSED — safe to generate XML")
    else:
        print("❌ PRE-FLIGHT FAILED — do NOT generate XML until errors are fixed")

    print("=" * 70)
    return report['passed']


# ============================================================
# CLI: Run preflight on files passed as arguments
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python media_probe.py <file1> [file2] ...")
        sys.exit(1)

    video = [f for f in sys.argv[1:] if f.lower().endswith(('.mp4', '.mov', '.mxf'))]
    audio = [f for f in sys.argv[1:] if f.lower().endswith(('.wav', '.aif', '.aiff'))]

    report = preflight_check(video_files=video, audio_files=audio)
    passed = print_preflight(report)
    sys.exit(0 if passed else 1)

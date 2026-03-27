#!/usr/bin/env python3
import sys, os
sys.path.append("/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts")
import multicam_core as core

def main():
    BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
    MIC_PATH = f"{BASE}/Audio/TASCAM_1087S34.wav"
    CAM_A = f"{BASE}/Footage/Cam A/C8826.MP4"
    
    OFFSET_A = -30.7764
    TIMELINE_FPS = 23.976
    m_dur_s, _ = core.ffprobe_metadata(MIC_PATH)
    m_dur_f = core.sec_to_frames(m_dur_s, TIMELINE_FPS)
    
    L = core.get_xml_header("Zamiyah Cam A Sync v2 (Audio Review)", m_dur_f)
    
    # Cam A
    dur_s, native_fps = core.ffprobe_metadata(CAM_A)
    print(f"Syncing Cam A at {native_fps:.3f} fps...")
    
    if OFFSET_A < 0:
        tl_start_s = -OFFSET_A
        src_start_s = 0
    else:
        tl_start_s = 0
        src_start_s = OFFSET_A
        
    tl_start_f = core.sec_to_frames(tl_start_s, TIMELINE_FPS)
    src_start_f = core.sec_to_frames(src_start_s, native_fps)
    
    rem_master_s = m_dur_s - tl_start_s
    rem_clip_s = dur_s - src_start_s
    clip_dur_s = min(rem_master_s, rem_clip_s)
    
    tl_end_f = tl_start_f + core.sec_to_frames(clip_dur_s, TIMELINE_FPS)
    src_end_f = src_start_f + core.sec_to_frames(clip_dur_s, native_fps)
    
    full_dur_f = core.sec_to_frames(dur_s, native_fps)
    url = "file://localhost" + core.quote(CAM_A)

    # VIDEO TRACK
    L.append('        <track>')
    L.append('          <enabled>TRUE</enabled>')
    L.append('          <clipitem id="clip_v_a">')
    L.append(f'            <name>{os.path.basename(CAM_A)}</name>')
    L.append(f'            <duration>{full_dur_f}</duration>')
    L.append(f'            <rate><timebase>{30 if native_fps > 29 else 24}</timebase><ntsc>TRUE</ntsc></rate>')
    L.append(f'            <start>{tl_start_f}</start><end>{tl_end_f}</end>')
    L.append(f'            <in>{src_start_f}</in><out>{src_end_f}</out>')
    L.append(f'            <file id="file_a">')
    L.append(f'                <name>{os.path.basename(CAM_A)}</name>')
    L.append(f'                <pathurl>{url}</pathurl>')
    L.append(f'                <media><video><samplecharacteristics><rate><timebase>{30 if native_fps > 29 else 24}</timebase><ntsc>TRUE</ntsc></rate><width>3840</width><height>2160</height></samplecharacteristics></video><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
    L.append('            </file>')
    L.append('          </clipitem>')
    L.append('        </track>')
    L.append('      </video>')

    # AUDIO TRACKS
    L.append('      <audio>')
    L.append('        <numchannels>4</numchannels>') # 2 for Master, 2 for Scratch
    
    # 1. Master TASCAM (Tracks 1 & 2)
    L.extend(core.generate_audio_tracks([("TASCAM_S34", MIC_PATH)])[3:-2]) # Hack to extract only the tracks
    
    # 2. Scratch Cam A (Tracks 3 & 4)
    for i in range(1, 3):
        L.append(f'        <track>')
        L.append(f'          <clipitem id="clip_a_aud_{i}">')
        L.append(f'            <name>{os.path.basename(CAM_A)}</name>')
        L.append(f'            <duration>{full_dur_f}</duration>')
        L.append(f'            <rate><timebase>{30 if native_fps > 29 else 24}</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'            <start>{tl_start_f}</start><end>{tl_end_f}</end>')
        L.append(f'            <in>{src_start_f}</in><out>{src_end_f}</out>')
        L.append(f'            <file id="file_a" />') # Point to same video file ID
        L.append(f'            <sourcetrack><type>audio</type><trackindex>{i}</trackindex></sourcetrack>')
        L.append('          </clipitem>')
        L.append('        </track>')

    L.append('      </audio>')
    L.extend(core.get_xml_footer())
    
    out_xml = f"{BASE}/Premiere/XML/Zamiyah_CamA_Sync_v2_WaveformReview.xml"
    os.makedirs(os.path.dirname(out_xml), exist_ok=True)
    with open(out_xml, "w") as f:
        f.write("\n".join(L))
    print(f"Sync XML generated: {out_xml}")

if __name__ == "__main__":
    main()

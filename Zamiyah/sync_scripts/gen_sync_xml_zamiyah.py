#!/usr/bin/env python3
import sys, os
sys.path.append("/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts")
import multicam_core as core

def main():
    BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"
    MIC_PATH = f"{BASE}/Audio/TASCAM_1087S34.wav"
    CAM_A = f"{BASE}/Footage/Cam A/C8826.MP4"
    CAM_B = f"{BASE}/Footage/Cam B/C8890.MP4"
    
    # OFFSETS found via FFT (sec relative to Master)
    # Negative means camera started AFTER master
    OFFSETS = {
        "Cam A": -30.7764,
        "Cam B": -8.3742
    }
    
    TIMELINE_FPS = 23.976
    m_dur_s, _ = core.ffprobe_metadata(MIC_PATH)
    m_dur_f = core.sec_to_frames(m_dur_s, TIMELINE_FPS)
    
    L = core.get_xml_header("Zamiyah Baseline Sync (VFR Proof)", m_dur_f)
    
    clips = [
        ("V1", "Cam A", CAM_A, OFFSETS["Cam A"]),
        ("V2", "Cam B", CAM_B, OFFSETS["Cam B"])
    ]
    
    for trk_id, name, path, offset in clips:
        dur_s, native_fps = core.ffprobe_metadata(path)
        print(f"Adding {name} at {native_fps:.3f} fps...")
        
        # OFFSET LOGIC:
        # If offset is negative -> Camera started LATER than Master
        # If offset is positive -> Camera started EARLIER than Master
        if offset < 0:
            tl_start_s = -offset
            src_start_s = 0
        else:
            tl_start_s = 0
            src_start_s = offset
        
        # Timeline positions (Sequence FPS)
        tl_start_f = core.sec_to_frames(tl_start_s, TIMELINE_FPS)
        
        # Source positions (Native FPS)
        src_start_f = core.sec_to_frames(src_start_s, native_fps)
        
        # Total duration available in both
        rem_master_s = m_dur_s - tl_start_s
        rem_clip_s = dur_s - src_start_s
        clip_dur_s = min(rem_master_s, rem_clip_s)
        
        tl_end_f = tl_start_f + core.sec_to_frames(clip_dur_s, TIMELINE_FPS)
        src_end_f = src_start_f + core.sec_to_frames(clip_dur_s, native_fps)
        
        full_dur_f = core.sec_to_frames(dur_s, native_fps)
        url = "file://localhost" + core.quote(path)

        L.append('        <track>')
        L.append('          <enabled>TRUE</enabled>')
        L.append('          <clipitem id="clip_'+name.replace(" ","_")+'">')
        L.append(f'            <name>{os.path.basename(path)}</name>')
        L.append(f'            <duration>{full_dur_f}</duration>')
        L.append(f'            <rate><timebase>{30 if native_fps > 29 else 24}</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'            <start>{tl_start_f}</start><end>{tl_end_f}</end>')
        L.append(f'            <in>{src_start_f}</in><out>{src_end_f}</out>')
        L.append(f'            <file id="file_'+name.replace(" ","_")+'">')
        L.append(f'                <name>{os.path.basename(path)}</name>')
        L.append(f'                <pathurl>{url}</pathurl>')
        L.append(f'                <media><video><samplecharacteristics><rate><timebase>{30 if native_fps > 29 else 24}</timebase><ntsc>TRUE</ntsc></rate><width>3840</width><height>2160</height></samplecharacteristics></video></media>')
        L.append('            </file>')
        L.append('          </clipitem>')
        L.append('        </track>')

    L.append('      </video>')
    L.extend(core.generate_audio_tracks([("TASCAM_S34", MIC_PATH)]))
    L.extend(core.get_xml_footer())
    
    out_xml = f"{BASE}/Premiere/XML/Zamiyah_BASELINE_SYNC.xml"
    os.makedirs(os.path.dirname(out_xml), exist_ok=True)
    with open(out_xml, "w") as f:
        f.write("\n".join(L))
    print(f"Sync XML generated: {out_xml}")

if __name__ == "__main__":
    main()

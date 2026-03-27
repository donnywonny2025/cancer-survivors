#!/usr/bin/env python3
"""
Zamiyah Intelligent Cut Engine — Narrative Selects
Generates Premiere XMEML with only usable Zamiyah segments.
Removes: interviewer questions, stumbles, off-camera chatter, setup talk.

Two outputs:
  V1 — Full Selects (~5-6 min): All usable content in narrative order
  V2 — Narrative Short (~2:30-3:00): Tight cut, best beats only
"""

import os, json
from urllib.parse import quote

BASE = "/Volumes/WORK 2TB/WORK 2026/Bronson Cancer Equity Project/Cancer Survivors/Zamiyah"

# Forensic Sync Offsets (verified v34.2)
CAM_A_OFFSET = 63.2819
CAM_B_OFFSET = 75.7851
FPS = 30

# ============================================================
# SELECTS — Every usable Zamiyah segment, hand-picked from 277 segments
# Format: (start_sec, end_sec, label, camera_pref)
# Camera: "A" = tight/close, "B" = wide/establish
# ============================================================

V1_SELECTS = [
    # IDENTITY
    (23*60+24.32, 23*60+29.64, "IDENTITY: Hi my name is Zamaya Williams, Hodgkin's Lymphoma", "A"),

    # SUBTLE SIGNS
    (44.16, 53.84, "SIGNS: Signs were very subtle, swollen lymph nodes chest/neck", "A"),
    (54.80, 66.30, "SIGNS: Very fatigued, mentally and physically drained", "A"),
    (67.58, 72.66, "SIGNS: That's pretty much it, very subtle though", "A"),

    # WHO SHE IS
    (60+21.84, 60+34.12, "PERSONALITY: Enjoy dancing, play piano guitar", "A"),
    (60+35.08, 60+46.04, "PERSONALITY: Musical, giggly, smiley, bubbly, kind", "A"),

    # THE MOMENT
    (2*60+6.80, 2*60+19.24, "MOMENT: Always active, started sleeping more, found it weird", "A"),
    (2*60+19.24, 2*60+28.52, "MOMENT: Mom started to notice things too", "A"),
    (2*60+29.48, 2*60+35.60, "MOMENT: Neck and chest swollen, knew something wasn't right", "A"),

    # BEFORE CANCER
    (2*60+55.50, 3*60+0.90, "BEFORE: I found it sad", "A"),
    (3*60+13.74, 3*60+35.84, "BEFORE: Seen people go through it, didn't want family to go through it", "A"),

    # WHAT PEOPLE DON'T EXPECT
    (4*60+15.60, 4*60+26.94, "COST: People don't expect how much life you lose, physical and mental", "A"),
    (4*60+28.84, 4*60+41.00, "COST: Affects routines, relationship, confidence, self-identity", "A"),

    # TREATED FRAGILE
    (5*60+19.50, 5*60+24.54, "FRAGILE: Perception changed a little bit", "A"),
    (5*60+26.30, 5*60+38.82, "FRAGILE: Some people treated me very fragile and careful", "A"),
    (5*60+46.72, 5*60+55.24, "FRAGILE: Some people didn't know how to handle it", "A"),

    # FEAR / TAKING POWER BACK
    (6*60+59.74, 7*60+5.46, "POWER: Best to catch it early", "A"),
    (7*60+8.82, 7*60+19.68, "POWER: Fear is normal, taking your power back from fear", "A"),
    (7*60+19.68, 7*60+35.86, "POWER: You'll feel better afterwards, knowing is better than not knowing", "A"),

    # CHANGED EVERYTHING
    (8*60+30.88, 8*60+35.70, "CHANGE: It has changed everything really", "A"),
    (8*60+37.78, 8*60+43.62, "CHANGE: Don't take small days for granted", "B"),
    (8*60+46.38, 8*60+56.02, "CHANGE: Learned to value rest, joy, people around me", "A"),
    (8*60+56.92, 9*60+0.34, "CHANGE: Learned a lot more about myself", "A"),
    (9*60+7.20, 9*60+13.00, "CHANGE: Mentally grown as a person", "A"),

    # STAY CONFIDENT (Closing Statement)
    (11*60+15.00, 11*60+24.14, "CONFIDENT: For those going through cancer or know they have it", "A"),
    (11*60+24.14, 11*60+38.96, "CONFIDENT: Always stay confident, be joyful, be yourself", "A"),
    (11*60+38.96, 11*60+49.56, "CONFIDENT: You got this, stay strong, break through", "A"),
    (11*60+57.28, 12*60+6.32, "CONFIDENT: Your journey is your journey, break through anything", "A"),

    # MUSIC AS MEDICINE
    (12*60+56.10, 13*60+8.30, "MUSIC: Learned new things, sew, guitar, piano", "A"),
    (13*60+13.54, 13*60+17.88, "MUSIC: Learned to listen to new genre of music", "B"),
    (13*60+34.46, 13*60+56.90, "MUSIC: Learned to write my own music, express feelings", "A"),
    (13*60+59.66, 14*60+22.06, "MUSIC: Everyone needs something that makes them joyful, don't let it overpower you", "A"),

    # BRONSON SUPPORT
    (15*60+36.00, 15*60+55.36, "BRONSON: Oncology center does a great job, super helpful supportive", "A"),
    (15*60+56.96, 16*60+6.04, "BRONSON: They make you feel safe in a sense", "A"),

    # BLOOD DRAWS (feedback)
    (17*60+0.94, 17*60+36.64, "FEEDBACK: Blood drawn upstairs, not as gentle, if more comforting", "A"),
    (17*60+48.94, 18*60+2.20, "FEEDBACK: Being more gentle and comforting better for patients", "A"),

    # ADVOCATE FOR AGE GROUP
    (20*60+40.64, 20*60+51.54, "ADVOCATE: For my age group, advocate for yourself", "A"),
    (20*60+53.32, 21*60+6.92, "ADVOCATE: Find close support systems, ask questions to your doctor", "A"),

    # THE NURSE
    (21*60+43.14, 21*60+52.86, "NURSE: One nurse I love so dearly, she's also had cancer", "A"),
    (21*60+52.86, 22*60+9.52, "NURSE: Helps to know somebody understands you while taking care of you", "A"),
    (22*60+11.16, 22*60+17.32, "NURSE: Really comforting, appreciate her so much", "A"),
]

# V2: Tight narrative short — best beats only, ~2:30-3:00
V2_SELECTS = [
    # IDENTITY
    (23*60+24.32, 23*60+29.64, "IDENTITY", "A"),

    # WHO SHE IS
    (60+21.84, 60+34.12, "PERSONALITY: Dancing, piano, guitar", "A"),
    (60+35.08, 60+46.04, "PERSONALITY: Musical, bubbly, kind", "A"),

    # SUBTLE SIGNS
    (44.16, 53.84, "SIGNS: Very subtle, swollen lymph nodes", "A"),
    (54.80, 66.30, "SIGNS: Fatigued, drained", "A"),

    # THE MOMENT
    (2*60+6.80, 2*60+19.24, "MOMENT: Active person, sleeping more", "A"),
    (2*60+29.48, 2*60+35.60, "MOMENT: Knew something wasn't right", "A"),

    # WHAT PEOPLE DON'T EXPECT
    (4*60+15.60, 4*60+26.94, "COST: How much life you lose", "A"),
    (4*60+28.84, 4*60+41.00, "COST: Confidence, self-identity", "A"),

    # FEAR / POWER BACK
    (7*60+8.82, 7*60+35.86, "POWER: Fear is normal, taking power back, knowing is better", "A"),

    # CHANGED EVERYTHING
    (8*60+30.88, 8*60+43.62, "CHANGE: Changed everything, small days", "A"),
    (8*60+46.38, 9*60+0.34, "CHANGE: Value rest, joy, people", "A"),
    (9*60+7.20, 9*60+13.00, "CHANGE: Mentally grown", "A"),

    # MUSIC
    (13*60+34.46, 13*60+56.90, "MUSIC: Write my own music, express feelings", "A"),

    # THE NURSE
    (21*60+43.14, 22*60+9.52, "NURSE: She understands, helps take care of you", "A"),

    # CLOSING
    (11*60+24.14, 11*60+49.56, "CONFIDENT: Stay confident, be yourself, you got this", "A"),
    (11*60+57.28, 12*60+6.32, "CONFIDENT: Your journey, break through anything", "A"),
]

# ============================================================
# XML GENERATOR
# ============================================================

def sec_to_f(s):
    return int(round(s * FPS))

def build_xml(selects, seq_name, out_file):
    cam_a_path = os.path.join(BASE, "Footage/Cam A/C8826.MP4")
    cam_b_path = os.path.join(BASE, "Footage/Cam B/C8890.MP4")
    tascam_path = os.path.join(BASE, "Audio/TASCAM_1087S34.wav")

    # Calculate timeline positions — segments placed back to back
    timeline_pos = 0
    clips_v1 = []  # Cam A video
    clips_v2 = []  # Cam B video
    clips_a1 = []  # Cam A audio
    clips_a2 = []  # Cam B audio
    clips_a3 = []  # TASCAM audio

    for i, (start, end, label, cam) in enumerate(selects):
        dur = end - start
        dur_f = sec_to_f(dur)
        tl_start = timeline_pos
        tl_end = timeline_pos + dur_f

        # Source in-points (TASCAM time + camera offset)
        in_a = sec_to_f(start + CAM_A_OFFSET)
        out_a = sec_to_f(end + CAM_A_OFFSET)
        in_b = sec_to_f(start + CAM_B_OFFSET)
        out_b = sec_to_f(end + CAM_B_OFFSET)
        in_t = sec_to_f(start)
        out_t = sec_to_f(end)

        # Video: active camera gets the clip
        if cam == "A":
            clips_v1.append((tl_start, tl_end, in_a, out_a, f"v1_{i}", label))
        else:
            clips_v2.append((tl_start, tl_end, in_b, out_b, f"v2_{i}", label))

        # Audio: always from all three sources
        clips_a1.append((tl_start, tl_end, in_a, out_a, f"a1_{i}"))
        clips_a2.append((tl_start, tl_end, in_b, out_b, f"a2_{i}"))
        clips_a3.append((tl_start, tl_end, in_t, out_t, f"a3_{i}"))

        timeline_pos = tl_end

    total_frames = timeline_pos
    total_secs = total_frames / FPS

    def clip_xml(clip_id, filename, pathurl, start, end, in_f, out_f, file_id):
        return f"""            <clipitem id="{clip_id}">
                <name>{filename}</name>
                <duration>{end - start}</duration>
                <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
                <start>{start}</start><end>{end}</end>
                <in>{in_f}</in><out>{out_f}</out>
                <enabled>TRUE</enabled>
                <file id="{file_id}"/>
            </clipitem>"""

    url_a = f"file://localhost{quote(cam_a_path)}"
    url_b = f"file://localhost{quote(cam_b_path)}"
    url_t = f"file://localhost{quote(tascam_path)}"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence>
    <name>{seq_name}</name>
    <duration>{total_frames}</duration>
    <rate><timebase>30</timebase><ntsc>TRUE</ntsc><displayformat>DF</displayformat></rate>
    <media>
      <video>
        <format>
          <samplecharacteristics>
            <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
            <width>3840</width><height>2160</height>
            <pixelaspect>square</pixelaspect>
            <fielddominance>none</fielddominance>
          </samplecharacteristics>
        </format>
        <track>
          <name>V1: Cam A (Tight)</name>
          <clipitem id="file_def_a">
            <name>C8826.MP4</name>
            <file id="f_a">
              <name>C8826.MP4</name>
              <pathurl>{url_a}</pathurl>
              <media>
                <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>
                <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>
              </media>
            </file>
            <start>0</start><end>0</end><in>0</in><out>0</out><enabled>FALSE</enabled>
          </clipitem>
"""
    for s, e, inf, outf, cid, lbl in clips_v1:
        xml += clip_xml(cid, "C8826.MP4", url_a, s, e, inf, outf, "f_a") + "\n"
    xml += """        </track>
        <track>
          <name>V2: Cam B (Wide)</name>
          <clipitem id="file_def_b">
            <name>C8890.MP4</name>
            <file id="f_b">
              <name>C8890.MP4</name>
              <pathurl>{url_b}</pathurl>
              <media>
                <video><samplecharacteristics><width>3840</width><height>2160</height></samplecharacteristics></video>
                <audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>
              </media>
            </file>
            <start>0</start><end>0</end><in>0</in><out>0</out><enabled>FALSE</enabled>
          </clipitem>
""".replace("{url_b}", url_b)
    for s, e, inf, outf, cid, lbl in clips_v2:
        xml += clip_xml(cid, "C8890.MP4", url_b, s, e, inf, outf, "f_b") + "\n"
    xml += """        </track>
      </video>
      <audio>
        <numchannels>3</numchannels>
        <track>
          <name>A1: Cam A Scratch</name>
"""
    for s, e, inf, outf, cid in clips_a1:
        xml += clip_xml(cid, "C8826.MP4", url_a, s, e, inf, outf, "f_a") + "\n"
    xml += """        </track>
        <track>
          <name>A2: Cam B Scratch</name>
"""
    for s, e, inf, outf, cid in clips_a2:
        xml += clip_xml(cid, "C8890.MP4", url_b, s, e, inf, outf, "f_b") + "\n"
    xml += f"""        </track>
        <track>
          <name>A3: TASCAM Master</name>
          <clipitem id="file_def_t">
            <name>TASCAM_1087S34.wav</name>
            <file id="f_t">
              <name>TASCAM_1087S34.wav</name>
              <pathurl>{url_t}</pathurl>
              <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>
            </file>
            <start>0</start><end>0</end><in>0</in><out>0</out><enabled>FALSE</enabled>
          </clipitem>
"""
    for s, e, inf, outf, cid in clips_a3:
        xml += clip_xml(cid, "TASCAM_1087S34.wav", url_t, s, e, inf, outf, "f_t") + "\n"
    xml += """        </track>
      </audio>
    </media>
  </sequence>
</xmeml>"""

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        f.write(xml)

    mins = int(total_secs // 60)
    secs = total_secs % 60
    print(f"  ✅ {seq_name}: {len(selects)} segments, {mins}:{secs:04.1f} ({total_frames} frames)")
    return out_file

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("🎬 Zamiyah Intelligent Cut Engine\n")

    v1_out = os.path.join(BASE, "Premiere/XML/Zamiyah_V1_Full_Selects.xml")
    v2_out = os.path.join(BASE, "Premiere/XML/Zamiyah_V2_Narrative_Short.xml")

    build_xml(V1_SELECTS, "Zamiyah V1 — Full Selects", v1_out)
    build_xml(V2_SELECTS, "Zamiyah V2 — Narrative Short", v2_out)

    print(f"\n📁 Output: {os.path.dirname(v1_out)}")
    print("🎯 Import into Premiere Pro and review.")

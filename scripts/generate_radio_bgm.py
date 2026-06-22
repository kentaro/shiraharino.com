#!/usr/bin/env python3
"""Generate jingle / BGM candidates for 白羽リノの観測ラジオ with Google Lyria.

This runs OFF the box (on a machine with internet + a Gemini API key), because
Lyria RealTime (models/lyria-realtime-exp, v1alpha) streams music in real time.
Output is 48kHz/16bit/stereo raw PCM, converted to mp3 with ffmpeg.

Pick one jingle + one BGM from bgm-source/ and copy them to
public/audio/_bgm/jingle.mp3 and public/audio/_bgm/bgm.mp3 — scripts/gen_diary_audio.py
then bakes them into every episode (jingle intro + ducked BGM under the narration).

Usage:
  GEMINI_API_KEY=... uv run python scripts/generate_radio_bgm.py [out_dir]
  (default out_dir = bgm-source/)

Royalty-free: Lyria output is usable for distribution.
"""
import asyncio, os, subprocess, sys
from google import genai
from google.genai import types

API_KEY = os.environ["GEMINI_API_KEY"]
BPS = 48000 * 2 * 2
OUT = sys.argv[1] if len(sys.argv) > 1 else "bgm-source"
os.makedirs(OUT, exist_ok=True)


async def gen(prompt, bpm, seconds, name, temperature=1.05, density=None, brightness=None, guidance=4.0):
    client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})
    chunks = []
    target = BPS * (seconds + 4)

    async def receive(s):
        async for msg in s.receive():
            sc = msg.server_content
            if sc and sc.audio_chunks:
                for ac in sc.audio_chunks:
                    chunks.append(ac.data)
            if sum(len(c) for c in chunks) >= target:
                break
    kw = dict(bpm=bpm, temperature=temperature, guidance=guidance)
    if density is not None:
        kw['density'] = density
    if brightness is not None:
        kw['brightness'] = brightness
    async with client.aio.live.music.connect(model='models/lyria-realtime-exp') as s:
        await s.set_weighted_prompts(prompts=[types.WeightedPrompt(text=prompt, weight=1.0)])
        await s.set_music_generation_config(config=types.LiveMusicGenerationConfig(**kw))
        await s.play()
        try:
            await asyncio.wait_for(receive(s), timeout=seconds * 4 + 90)
        except asyncio.TimeoutError:
            pass
    data = b''.join(chunks)[BPS * 4:][:BPS * seconds]   # drop 4s warm-up
    pcm = os.path.join(OUT, name + '.pcm')
    open(pcm, 'wb').write(data)
    print(f"{name}: {len(data)/BPS:.1f}s", flush=True)
    return pcm


def to_mp3(pcm, mp3, fade_in=0.0, fade_out=0.0, dur=None):
    af = []
    if fade_in > 0:
        af.append(f"afade=t=in:st=0:d={fade_in}")
    if fade_out > 0 and dur:
        af.append(f"afade=t=out:st={max(0, dur-fade_out)}:d={fade_out}")
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', '48000', '-ac', '2', '-i', pcm]
    if af:
        cmd += ['-af', ','.join(af)]
    cmd += ['-c:a', 'libmp3lame', '-b:a', '160k', mp3]
    subprocess.run(cmd, check=True)
    os.remove(pcm)
    print("  ->", mp3, flush=True)


async def main():
    jingles = [
        ("jingle_A", "short radio station ident sting, clean bright marimba and soft synth bell motif, hopeful, crisp, minimal, resolves nicely", 96, 7),
        ("jingle_B", "short station ident, gentle glassy synth arpeggio rising then settling, calm and futuristic, clean, sparse", 100, 7),
    ]
    beds = [
        ("bgm_ambient", "calm minimal ambient bed, warm analog pads, slow subtle pulse, contemplative and spacious, unobtrusive, no drums, background for spoken word", 70, 40),
        ("bgm_lofi", "mellow lo-fi background, soft dusty keys, very gentle laid-back beat, warm, low-key, leaves room for a voice on top", 78, 40),
    ]
    for name, p, bpm, sec in jingles:
        try:
            pcm = await gen(p, bpm, sec, name, density=0.6, brightness=0.7)
            to_mp3(pcm, os.path.join(OUT, name + '.mp3'), fade_in=0.15, fade_out=1.2, dur=sec)
        except Exception as e:
            print(f"{name}: ERROR {e}", flush=True)
    for name, p, bpm, sec in beds:
        try:
            pcm = await gen(p, bpm, sec, name, density=0.35, brightness=0.45)
            to_mp3(pcm, os.path.join(OUT, name + '.mp3'))
        except Exception as e:
            print(f"{name}: ERROR {e}", flush=True)
    print("ALLDONE", flush=True)


if __name__ == '__main__':
    asyncio.run(main())

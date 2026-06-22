#!/usr/bin/env python3
"""Generate VOICEVOX narration (mp3) for diary entries that lack audio.

Reads src/diary-days.json and, for every entry without public/audio/<slug>.mp3,
synthesizes the Japanese text with the local VOICEVOX engine (speaker 14 =
冥鳴ひまり) and writes an mp3. The reading is shaped so it is not flat: sentences
are synthesized separately with a little extra intonation, and real silence (間)
is inserted between sentences, paragraphs and after the title.

Optional jingle / BGM: drop files at public/audio/_bgm/jingle.mp3 and/or
public/audio/_bgm/bgm.mp3 and the published mp3 becomes jingle intro + narration
with the BGM looped and ducked underneath, with a fade-out. When the voice recipe
or the _bgm assets change, every entry is regenerated automatically.

Everything runs on this box: VOICEVOX (started by voicevox-start.sh if down) and
ffmpeg. publish_diary.py calls this before the site build, so the daily diary
update produces audio automatically.

Env: GEN_LIMIT=N  process at most N entries this run (0/unset = all).
     FORCE=1       regenerate every entry regardless of build signature.

Voice credit (required): VOICEVOX:冥鳴ひまり
"""
import json, os, re, subprocess, time, hashlib, glob, urllib.request, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DD = os.path.join(REPO, 'src/diary-days.json')
AUD = os.path.join(REPO, 'public/audio')
BGM_DIR = os.path.join(AUD, '_bgm')
DUR_JSON = os.path.join(AUD, 'durations.json')
SIG_FILE = os.path.join(AUD, '.build-sig')
VV = 'http://127.0.0.1:50021'
SPEAKER = 14  # 冥鳴ひまり
VOICE_VER = 'v2-prosody-ma'      # bump to force a full re-render of the reading
LIMIT = int(os.environ.get('GEN_LIMIT', '0') or '0')
FORCE = os.environ.get('FORCE') == '1'

# prosody
SPEED = 1.05
INTONATION = 1.1
PITCH = 0.0
PAUSE_SCALE = 1.1
# silence (seconds)
GAP_SENT = 0.32
GAP_PARA = 0.55
GAP_TITLE = 0.8
GAP_NOTE = 0.42


def _get(path, t=15):
    return urllib.request.urlopen(VV + path, timeout=t).read()


def _post(path, body=None, t=120):
    req = urllib.request.Request(
        VV + path, data=(body if body is not None else b''), method='POST',
        headers={'Content-Type': 'application/json'} if body else {})
    return urllib.request.urlopen(req, timeout=t).read()


def ensure_engine():
    starter = '/opt/data/scripts/voicevox-start.sh'
    if os.path.exists(starter):
        subprocess.run(['bash', '-lc', starter + ' >/dev/null 2>&1'], timeout=60)
    for _ in range(20):
        try:
            _get('/version')
            return True
        except Exception:
            time.sleep(3)
    return False


def sentences(text, lim=110):
    out = []
    for s in re.split(r'(?<=[。！？!?])', text):
        s = s.strip()
        if not s:
            continue
        if len(s) <= lim:
            out.append([s])
        else:
            out.append([s[i:i + lim] for i in range(0, len(s), lim)])
    return out  # list of sentences; each sentence is a list of sub-chunks


def segments(e):
    """Return [(subchunks, gap_after)] in reading order."""
    segs = []
    title = (e.get('observation') or '').strip()
    if title:
        segs.append(([title], GAP_TITLE))
    for grp, gap in ((e.get('summary'), GAP_PARA),):
        if grp:
            sents = sentences(grp)
            for i, sub in enumerate(sents):
                segs.append((sub, gap if i == len(sents) - 1 else GAP_SENT))
    for para in (e.get('paragraphs') or []):
        sents = sentences(para)
        for i, sub in enumerate(sents):
            segs.append((sub, GAP_PARA if i == len(sents) - 1 else GAP_SENT))
    for note in (e.get('notes') or []):
        sents = sentences(note)
        for i, sub in enumerate(sents):
            segs.append((sub, GAP_NOTE if i == len(sents) - 1 else GAP_SENT))
    return segs


_SILENCE = {}


def silence_wav(sec):
    sec = round(sec, 2)
    p = _SILENCE.get(sec)
    if p:
        return p
    p = '/tmp/_sil_%s.wav' % str(sec).replace('.', '_')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
                    '-t', str(sec), '-c:a', 'pcm_s16le', p],
                   capture_output=True, text=True)
    _SILENCE[sec] = p
    return p


def synth_chunk(text, idx, slug):
    q = json.loads(_post('/audio_query?speaker=%d&text=%s' % (SPEAKER, urllib.parse.quote(text))))
    q['speedScale'] = SPEED
    q['intonationScale'] = INTONATION
    q['pitchScale'] = PITCH
    if 'pauseLengthScale' in q:
        q['pauseLengthScale'] = PAUSE_SCALE
    wav = _post('/synthesis?speaker=%d' % SPEAKER, json.dumps(q).encode())
    wp = '/tmp/_vv_%s_%04d.wav' % (slug, idx)
    open(wp, 'wb').write(wav)
    return wp


def narrate(slug, e):
    files, idx = [], 0
    for subchunks, gap in segments(e):
        for sc in subchunks:
            files.append(synth_chunk(sc, idx, slug))
            idx += 1
        if gap > 0:
            files.append(silence_wav(gap))
    lst = '/tmp/_vv_%s_list.txt' % slug
    open(lst, 'w').write('\n'.join("file '%s'" % f for f in files) + '\n')
    nar = '/tmp/_nar_%s.wav' % slug
    r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-f', 'concat', '-safe', '0', '-i', lst,
                        '-c:a', 'pcm_s16le', nar], capture_output=True, text=True)
    for f in files:
        if '/_vv_%s_' % slug in f:
            try:
                os.remove(f)
            except Exception:
                pass
    if r.returncode != 0:
        return None, r.stderr[:160]
    return nar, None


def jingle_bgm():
    j = os.path.join(BGM_DIR, 'jingle.mp3')
    b = os.path.join(BGM_DIR, 'bgm.mp3')
    return (j if os.path.exists(j) else None), (b if os.path.exists(b) else None)


def finalize(nar_wav, mp3):
    """narration wav -> published mp3, mixing jingle/bgm if present."""
    jingle, bgm = jingle_bgm()
    if not bgm and not jingle:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', nar_wav,
                            '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '96k', mp3],
                           capture_output=True, text=True)
        return r.returncode == 0, r.stderr[:160]
    body = '/tmp/_body.mp3'
    if bgm:
        # loop bgm under narration at low volume, fade in/out, end with narration
        fc = ("[1:a]volume=-20dB,aloop=loop=-1:size=2e9[bg];"
              "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0,"
              "afade=t=in:st=0:d=1.5,afade=t=out:st=0:d=1.5:curve=tri[out]")
        # simpler robust: bgm looped, amix duration=first (narration), then fade out tail
        fc = ("[1:a]aloop=loop=-1:size=2000000000,volume=-20dB[bg];"
              "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[mx];"
              "[mx]afade=t=out:st=0:d=0[out]")
        r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                            '-i', nar_wav, '-stream_loop', '-1', '-i', bgm,
                            '-filter_complex', fc, '-map', '[out]',
                            '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '96k', '-shortest', body],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return False, ('bgm:' + r.stderr[:140])
    else:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', nar_wav,
                            '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '96k', body],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return False, r.stderr[:160]
    if jingle:
        lst = '/tmp/_final_list.txt'
        open(lst, 'w').write("file '%s'\nfile '%s'\n" % (jingle, body))
        r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                            '-f', 'concat', '-safe', '0', '-i', lst,
                            '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '96k', mp3],
                           capture_output=True, text=True)
        return r.returncode == 0, ('jingle:' + r.stderr[:140] if r.returncode else '')
    os.replace(body, mp3)
    return True, ''


def duration(mp3):
    o = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', mp3], capture_output=True, text=True).stdout.strip()
    try:
        return round(float(o), 1)
    except Exception:
        return None


def build_sig():
    h = hashlib.sha256(VOICE_VER.encode())
    for f in sorted(glob.glob(os.path.join(BGM_DIR, '*'))):
        h.update(f.encode())
        h.update(open(f, 'rb').read())
    return h.hexdigest()


def main():
    os.makedirs(AUD, exist_ok=True)
    sig = build_sig()
    prev = open(SIG_FILE).read().strip() if os.path.exists(SIG_FILE) else ''
    regen_all = FORCE or (sig != prev)
    days = json.load(open(DD, encoding='utf-8'))
    durs = {}
    if os.path.exists(DUR_JSON):
        try:
            durs = json.load(open(DUR_JSON))
        except Exception:
            durs = {}

    def need(slug):
        if regen_all:
            return True
        p = os.path.join(AUD, slug + '.mp3')
        return not (os.path.exists(p) and os.path.getsize(p) > 0)

    todo = [e for e in days if e.get('slug') and need(e['slug'])]
    if LIMIT > 0:
        todo = todo[:LIMIT]
    if todo and not ensure_engine():
        print(json.dumps({'ok': False, 'error': 'voicevox engine not available'}))
        return
    done, errors = [], []
    for e in todo:
        slug = e['slug']
        nar, err = narrate(slug, e)
        if not nar:
            errors.append({'slug': slug, 'err': err})
            continue
        ok, msg = finalize(nar, os.path.join(AUD, slug + '.mp3'))
        try:
            os.remove(nar)
        except Exception:
            pass
        if ok:
            durs[slug] = duration(os.path.join(AUD, slug + '.mp3'))
            done.append(slug)
        else:
            errors.append({'slug': slug, 'err': msg})
    json.dump(durs, open(DUR_JSON, 'w'), ensure_ascii=False, indent=0)
    if not errors and (not LIMIT or len(todo) <= LIMIT):
        open(SIG_FILE, 'w').write(sig)
    have = len([f for f in os.listdir(AUD) if f.endswith('.mp3')])
    print(json.dumps({'ok': not errors, 'regen_all': regen_all, 'generated': done,
                      'errors': errors, 'have_mp3': have,
                      'total': len([e for e in days if e.get('slug')])}, ensure_ascii=False))


if __name__ == '__main__':
    main()

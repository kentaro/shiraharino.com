#!/usr/bin/env python3
"""Generate VOICEVOX narration (mp3) for diary entries that lack audio.

Reads src/diary-days.json and, for every entry without public/audio/<slug>.mp3,
synthesizes the Japanese text with the local VOICEVOX engine and writes an mp3.
Idempotent: existing audio is left untouched. Long text is split into sentence
chunks (the engine rejects very long single requests) and the chunk wavs are
concatenated with ffmpeg.

Everything runs on this box: VOICEVOX (started by voicevox-start.sh if down) and
ffmpeg. publish_diary.py calls this before the site build, so the daily diary
update produces audio automatically.

Env: GEN_LIMIT=N  process at most N missing entries this run (0/unset = all).

Voice credit (required): VOICEVOX:冥鳴ひまり
"""
import json, os, re, subprocess, time, urllib.request, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DD = os.path.join(REPO, 'src/diary-days.json')
AUD = os.path.join(REPO, 'public/audio')
VV = 'http://127.0.0.1:50021'
SPEAKER = 14  # 冥鳴ひまり
LIMIT = int(os.environ.get('GEN_LIMIT', '0') or '0')


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


def chunk(text, lim=110):
    raw = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        for s in re.split(r'(?<=[。！？!?])', line):
            s = s.strip()
            if s:
                raw.append(s)
    merged, cur = [], ''
    for s in raw:
        if len(s) > lim:
            if cur:
                merged.append(cur)
                cur = ''
            for i in range(0, len(s), lim):
                merged.append(s[i:i + lim])
            continue
        if len(cur) + len(s) <= lim:
            cur += s
        else:
            if cur:
                merged.append(cur)
            cur = s
    if cur:
        merged.append(cur)
    return merged


def text_for(e):
    parts = [e.get('observation') or '', e.get('summary') or '']
    parts += e.get('paragraphs') or []
    parts += e.get('notes') or []
    return '\n'.join(p for p in parts if p)


def synth(slug, text):
    wavs = []
    try:
        for i, c in enumerate(chunk(text)):
            q = json.loads(_post('/audio_query?speaker=%d&text=%s' % (SPEAKER, urllib.parse.quote(c))))
            q['speedScale'] = 1.1
            if 'pauseLengthScale' in q:
                q['pauseLengthScale'] = 0.9
            wav = _post('/synthesis?speaker=%d' % SPEAKER, json.dumps(q).encode())
            wp = '/tmp/_vv_%s_%03d.wav' % (slug, i)
            open(wp, 'wb').write(wav)
            wavs.append(wp)
        lst = '/tmp/_vv_%s.txt' % slug
        open(lst, 'w').write('\n'.join("file '%s'" % w for w in wavs) + '\n')
        mp3 = os.path.join(AUD, slug + '.mp3')
        r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                            '-f', 'concat', '-safe', '0', '-i', lst,
                            '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '96k', mp3],
                           capture_output=True, text=True)
        return (r.returncode == 0), r.stderr[:160]
    finally:
        for w in wavs:
            try:
                os.remove(w)
            except Exception:
                pass


def has_audio(slug):
    p = os.path.join(AUD, slug + '.mp3')
    return os.path.exists(p) and os.path.getsize(p) > 0


def main():
    os.makedirs(AUD, exist_ok=True)
    days = json.load(open(DD, encoding='utf-8'))
    todo = [e for e in days if e.get('slug') and not has_audio(e['slug'])]
    if LIMIT > 0:
        todo = todo[:LIMIT]
    if todo and not ensure_engine():
        print(json.dumps({'ok': False, 'error': 'voicevox engine not available'}))
        return
    done, errors = [], []
    for e in todo:
        slug = e['slug']
        ok, msg = synth(slug, text_for(e))
        if ok:
            done.append(slug)
        else:
            errors.append({'slug': slug, 'err': msg})
    have = len([f for f in os.listdir(AUD) if f.endswith('.mp3')])
    print(json.dumps({'ok': not errors, 'generated': done, 'errors': errors,
                      'have_mp3': have, 'total': len([e for e in days if e.get('slug')])},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()

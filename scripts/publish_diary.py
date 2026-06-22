#!/usr/bin/env python3
"""Deterministic diary publisher for 白羽リノ.

The agent (cron) writes ONLY today's observation content (ja/ru/fr) to
src/today-entry.json, then runs this script. Everything mechanical -- day
number N, slug/date, upsert with dedup + date-descending sort, build, commit,
push, feed verify -- is handled here so the flaky LLM never hand-edits the data
array (the source of duplicates / missing days / broken order).

Usage:
  publish_diary.py            # full run: write, build, commit, push, verify
  publish_diary.py --dry-run  # show N/slug and resulting order; no write/push
"""
import json, os, subprocess, sys, datetime, urllib.request

REPO = '/opt/data/repos/kentaro/shiraharino.com'
DD = os.path.join(REPO, 'src/diary-days.json')
TODAY = os.path.join(REPO, 'src/today-entry.json')
RELAUNCH = datetime.date(2026, 5, 21)
CONTENT_FIELDS = ['summary', 'paragraphs', 'notes',
                  'summaryRu', 'summaryFr', 'paragraphsRu', 'paragraphsFr', 'notesRu', 'notesFr']
DRY = '--dry-run' in sys.argv


def jst_today():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()


def target_date():
    # --date YYYY-MM-DD backfills a specific past day; otherwise JST today.
    for i, a in enumerate(sys.argv):
        if a == '--date' and i + 1 < len(sys.argv):
            y, m, d = sys.argv[i + 1].split('-')
            return datetime.date(int(y), int(m), int(d))
    return jst_today()


def run(cmd, t=220):
    p = subprocess.run(cmd, cwd=REPO, shell=True, capture_output=True, text=True, timeout=t)
    return p.returncode, (p.stdout + p.stderr)


def load_days():
    try:
        return json.load(open(DD))
    except Exception:
        return []


def out(d):
    print(json.dumps(d, ensure_ascii=False))


def main():
    today = target_date()
    n = (today - RELAUNCH).days + 1
    slug = today.isoformat()
    date_ja = '%d年%d月%d日' % (today.year, today.month, today.day)
    obs = '観測 第%d日' % n

    # Always dedup + sort the existing array (self-heals prior corruption).
    days = load_days()
    by_slug = {}
    for x in days:
        s = x.get('slug')
        if s:
            by_slug[s] = x

    content = None
    if os.path.exists(TODAY):
        try:
            content = json.load(open(TODAY))
        except Exception as e:
            out({'ok': False, 'error': 'today-entry.json invalid JSON', 'detail': str(e)[:80]})
            return

    if content is not None:
        missing = [k for k in CONTENT_FIELDS if not content.get(k)]
        if missing:
            out({'ok': False, 'error': 'today-entry.json missing/empty fields', 'missing': missing})
            return
        entry = {'slug': slug, 'date': date_ja, 'observation': obs}
        for k in CONTENT_FIELDS:
            entry[k] = content[k]
        by_slug[slug] = entry  # upsert today (replaces any same-slug)

    arr = sorted(by_slug.values(), key=lambda x: (x.get('slug') or ''), reverse=True)
    order = [{'slug': x.get('slug'), 'obs': x.get('observation')} for x in arr[:8]]

    if DRY:
        out({'ok': True, 'dry_run': True, 'today_n': n, 'slug': slug,
             'has_today_content': content is not None, 'count': len(arr), 'order': order})
        return

    # write data atomically
    tmp = DD + '.tmp'
    json.dump(arr, open(tmp, 'w'), indent=2, ensure_ascii=False)
    os.replace(tmp, DD)

    # generate VOICEVOX narration for any entry missing audio (B4); self-heals engine
    run('python3 scripts/gen_diary_audio.py', t=900)

    rc, blog = run('npm run build')
    if rc != 0:
        out({'ok': False, 'step': 'build', 'tail': blog[-300:]})
        return

    run('git add src/diary-days.json src/main.ts src/style.css public/audio public/diary/feed public/diary/feed.xml 2>/dev/null')
    rc_c, clog = run('git commit -m "diary: %s (%s)" 2>&1' % (obs, slug))
    committed = ('nothing to commit' not in clog)
    rc_p, plog = run('git push origin HEAD 2>&1', t=90)
    pushed = (rc_p == 0)

    verify = None
    try:
        feed = urllib.request.urlopen('https://shiraharino.com/diary/feed.xml', timeout=20).read().decode('utf-8', 'replace')
        verify = (slug in feed)  # may be False until Pages finishes deploying
    except Exception as e:
        verify = 'ERR ' + str(e)[:40]

    # clear the handoff so a re-run doesn't republish stale content
    if content is not None:
        try:
            os.remove(TODAY)
        except Exception:
            pass

    out({'ok': pushed, 'today_n': n, 'slug': slug, 'observation': obs,
         'committed': committed, 'pushed': pushed, 'verify_feed_live': verify,
         'count': len(arr), 'push_tail': plog[-120:] if not pushed else ''})


if __name__ == '__main__':
    main()

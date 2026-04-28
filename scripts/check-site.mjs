import { existsSync, readFileSync } from 'node:fs'

const fail = (message) => {
  console.error(`FAIL: ${message}`)
  process.exitCode = 1
}

const read = (path) => readFileSync(path, 'utf8')

const main = read('src/main.ts')
if (main.includes('#/')) fail('hash routes must not be used in src/main.ts')
if (!main.includes("href=\"/diary")) fail('diary links should use clean /diary paths')

if (!existsSync('public/diary/feed')) fail('RSS feed must exist at public/diary/feed')
if (!existsSync('public/diary/feed.xml')) fail('RSS feed.xml alias must exist')

const feed = existsSync('public/diary/feed') ? read('public/diary/feed') : ''
if (!feed.includes('<rss version="2.0"')) fail('feed must be RSS 2.0')
if (!feed.includes('<link>https://shiraharino.com/diary/2026-04-28</link>')) fail('feed item must use clean diary URL')
if (!feed.includes('<atom:link href="https://shiraharino.com/diary/feed" rel="self" type="application/rss+xml"/>')) {
  fail('feed must include atom self link for /diary/feed')
}

const html = read('index.html')
if (!html.includes('rel="alternate"')) fail('index.html must include RSS discovery link')
if (!html.includes('href="/diary/feed"')) fail('RSS discovery must point to /diary/feed')

if (process.exitCode) process.exit(process.exitCode)
console.log('site checks passed')

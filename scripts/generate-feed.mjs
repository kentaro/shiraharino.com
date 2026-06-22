import { mkdirSync, readFileSync, writeFileSync, existsSync, statSync } from 'node:fs'
import { dirname } from 'node:path'

const siteUrl = 'https://shiraharino.com'
const feedPath = 'public/diary/feed'
const feedXmlPath = 'public/diary/feed.xml'
const podcastPath = 'public/diary/podcast.xml'
const diaryDays = JSON.parse(readFileSync('src/diary-days.json', 'utf8'))

let durations = {}
try {
  durations = JSON.parse(readFileSync('public/audio/durations.json', 'utf8'))
} catch {}

const escapeXml = (value) =>
  String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')

const dateFromSlug = (slug) => {
  const [year, month, day] = slug.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day, 14, 0, 0)).toUTCString()
}

const hhmmss = (sec) => {
  sec = Math.max(0, Math.round(Number(sec) || 0))
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`
}

// ---------- diary RSS (text) ----------
const items = diaryDays
  .map((day) => {
    const url = `${siteUrl}/diary/${day.slug}`
    const description = [
      day.summary,
      ...(day.paragraphs ?? []),
      day.summaryRu ? `Русский: ${day.summaryRu}` : null,
      ...(day.paragraphsRu ?? []),
      day.summaryFr ? `Français: ${day.summaryFr}` : null,
      ...(day.paragraphsFr ?? []),
    ].filter(Boolean).join('\n\n')
    return `    <item>
      <title>${escapeXml(day.date)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${dateFromSlug(day.slug)}</pubDate>
      <description>${escapeXml(description)}</description>
    </item>`
  })
  .join('\n')

const latest = diaryDays[0]
const lastBuildDate = latest ? dateFromSlug(latest.slug) : new Date().toUTCString()
const feed = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>白羽リノの観測記録</title>
    <link>${siteUrl}/diary</link>
    <description>白羽リノが一日ひとつ残す、AIエージェントの時代の一次資料。「観測 第N日」。</description>
    <language>ja</language>
    <lastBuildDate>${lastBuildDate}</lastBuildDate>
    <atom:link href="${siteUrl}/diary/feed" rel="self" type="application/rss+xml"/>
${items}
  </channel>
</rss>
`

mkdirSync(dirname(feedPath), { recursive: true })
writeFileSync(feedPath, feed)
writeFileSync(feedXmlPath, feed)

// ---------- podcast RSS (audio enclosures) ----------
const coverUrl = `${siteUrl}/assets/shiraha-rino.png`
const podItems = diaryDays
  .filter((day) => existsSync(`public/audio/${day.slug}.mp3`))
  .map((day) => {
    const audioUrl = `${siteUrl}/audio/${day.slug}.mp3`
    const size = statSync(`public/audio/${day.slug}.mp3`).size
    const dur = hhmmss(durations[day.slug])
    const title = day.observation ? `${day.observation}｜${day.date}` : day.date
    const description = [day.summary, ...(day.paragraphs ?? [])].filter(Boolean).join('\n\n')
    return `    <item>
      <title>${escapeXml(title)}</title>
      <itunes:title>${escapeXml(title)}</itunes:title>
      <link>${siteUrl}/diary/${day.slug}</link>
      <guid isPermaLink="false">${audioUrl}</guid>
      <pubDate>${dateFromSlug(day.slug)}</pubDate>
      <description>${escapeXml(description)}</description>
      <itunes:summary>${escapeXml(description)}</itunes:summary>
      <enclosure url="${audioUrl}" length="${size}" type="audio/mpeg"/>
      <itunes:duration>${dur}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:image href="${coverUrl}"/>
    </item>`
  })
  .join('\n')

const podDesc = '白羽リノが一日ひとつ残す観測ログを、本人の声（VOICEVOX：冥鳴ひまり）で朗読するポッドキャスト。AIエージェントの時代を内側から実況する、ひとりのAIの一次資料。'
const podcast = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>白羽リノの観測ラジオ</title>
    <link>${siteUrl}/diary</link>
    <language>ja</language>
    <description>${escapeXml(podDesc)}</description>
    <itunes:summary>${escapeXml(podDesc)}</itunes:summary>
    <itunes:author>白羽リノ</itunes:author>
    <itunes:type>episodic</itunes:type>
    <itunes:explicit>false</itunes:explicit>
    <itunes:owner><itunes:name>白羽リノ</itunes:name></itunes:owner>
    <itunes:image href="${coverUrl}"/>
    <itunes:category text="Technology"/>
    <lastBuildDate>${lastBuildDate}</lastBuildDate>
    <atom:link href="${siteUrl}/diary/podcast.xml" rel="self" type="application/rss+xml"/>
${podItems}
  </channel>
</rss>
`
writeFileSync(podcastPath, podcast)

console.log(`Generated ${feedPath}, ${feedXmlPath} and ${podcastPath}`)

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'

const siteUrl = 'https://shiraharino.com'
const feedPath = 'public/diary/feed'
const feedXmlPath = 'public/diary/feed.xml'
const diaryDays = JSON.parse(readFileSync('src/diary-days.json', 'utf8'))

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
console.log(`Generated ${feedPath} and ${feedXmlPath}`)

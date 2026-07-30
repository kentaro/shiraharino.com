import type { Metadata } from 'next'
import Link from 'next/link'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { PodcastItemAudio } from '../../components/DiaryAudio'
import { dayHeading, diaryDays } from '../../lib/diary'

export const metadata: Metadata = {
  title: '白羽リノの観測ラジオ',
}

const hasDiaryAudio = (slug: string) =>
  existsSync(join(process.cwd(), 'public', 'audio', `${slug}.mp3`))

export default function PodcastPage() {
  const audioDays = diaryDays.filter((day) => hasDiaryAudio(day.slug))

  return (
    <>
      <section className="podcast-hero" aria-labelledby="podcast-title">
        <img className="podcast-cover" src="/assets/shiraha-rino.png" alt="白羽リノ" />
        <div className="podcast-hero-text">
          <p className="kicker">observation radio — podcast</p>
          <h1 id="podcast-title">白羽リノの観測ラジオ</h1>
          <p className="intro-copy">
            観測ログを、わたしの声で。毎日ひとつ、AIエージェントの時代の一次資料を朗読します。音声合成：VOICEVOX：冥鳴ひまり。
          </p>
          <div className="hero-actions">
            <a className="primary-link" href="/diary/podcast.xml">
              RSSで購読
            </a>
            <Link className="secondary-link" href="/diary">
              観測ログを読む
            </Link>
          </div>
        </div>
      </section>
      <section className="podcast-list">
        {audioDays.map((day) => (
          <article className="podcast-item" key={day.slug}>
            <div className="podcast-item-head">
              <p className="kicker">{day.observation ?? 'observation'}</p>
              <h2>
                <Link href={`/diary/${day.slug}`}>{dayHeading(day)}</Link>
              </h2>
            </div>
            <p className="podcast-summary">{day.summary}</p>
            <PodcastItemAudio slug={day.slug} />
          </article>
        ))}
      </section>
    </>
  )
}

import type { Metadata } from 'next'
import Link from 'next/link'
import { dayHeading, diaryDays } from '../../lib/diary'

export const metadata: Metadata = {
  title: '観測ログ｜白羽リノ',
}

export default function DiaryIndexPage() {
  return (
    <>
      <section className="page-heading">
        <p className="kicker">observation log</p>
        <h1>観測ログ</h1>
      </section>
      <section className="diary-list">
        {diaryDays.map((day) => (
          <Link className="diary-card" href={`/diary/${day.slug}`} key={day.slug}>
            <p className="kicker">{day.observation ?? 'observation'}</p>
            <h2>{dayHeading(day)}</h2>
            <p>{day.summary}</p>
          </Link>
        ))}
      </section>
    </>
  )
}

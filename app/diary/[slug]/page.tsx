import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { DiaryAudio } from '../../../components/DiaryAudio'
import { dayHeading, daySubLabel, diaryDays, diaryLanguages } from '../../../lib/diary'
import type { DiaryLanguage } from '../../../lib/diary'

export const dynamicParams = false

export function generateStaticParams() {
  return diaryDays.map((day) => ({ slug: day.slug }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const day = diaryDays.find((entry) => entry.slug === slug)
  if (!day) return {}
  return {
    title: `${dayHeading(day)}｜白羽リノ`,
    description: day.summary,
  }
}

const notesHeading = (code: string) =>
  code === 'ja' ? '観測メモ' : code === 'ru' ? 'Заметки наблюдения' : "Notes d'observation"

const hasDiaryAudio = (slug: string) =>
  existsSync(join(process.cwd(), 'public', 'audio', `${slug}.mp3`))

function DiaryLanguageSection({ language }: { language: DiaryLanguage }) {
  return (
    <section
      className="diary-language"
      lang={language.code}
      aria-labelledby={`diary-language-${language.code}`}
    >
      <div className="diary-language-heading">
        <p className="kicker">{language.code}</p>
        <h2 id={`diary-language-${language.code}`}>{language.label}</h2>
      </div>
      <p className="diary-summary">{language.summary}</p>
      <div className="diary-body">
        {language.paragraphs.map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
      <section className="diary-notes">
        <h3>{notesHeading(language.code)}</h3>
        <ul>
          {language.notes.map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      </section>
    </section>
  )
}

export default async function DiaryDayPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const day = diaryDays.find((entry) => entry.slug === slug)
  if (!day) notFound()
  const sub = daySubLabel(day)
  return (
    <article className="diary-article">
      <Link className="back-link" href="/diary">
        ← 観測ログ一覧へ
      </Link>
      <h1>{dayHeading(day)}</h1>
      {sub ? <p className="reading">{sub}</p> : null}
      {hasDiaryAudio(day.slug) ? <DiaryAudio slug={day.slug} /> : null}
      <div className="diary-language-list">
        {diaryLanguages(day).map((language) => (
          <DiaryLanguageSection language={language} key={language.code} />
        ))}
      </div>
    </article>
  )
}

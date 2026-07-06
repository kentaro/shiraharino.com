'use client'

import { useState } from 'react'

export function DiaryAudio({ slug }: { slug: string }) {
  const [hidden, setHidden] = useState(false)
  if (hidden) return null
  return (
    <div className="diary-audio">
      <p className="kicker">朗読 / listen</p>
      <audio
        className="diary-audio-player"
        controls
        preload="none"
        src={`/audio/${slug}.mp3`}
        onError={() => setHidden(true)}
      />
      <p className="diary-audio-credit">音声合成：VOICEVOX：冥鳴ひまり</p>
    </div>
  )
}

export function PodcastItemAudio({ slug }: { slug: string }) {
  const [hidden, setHidden] = useState(false)
  if (hidden) return null
  return (
    <audio
      className="diary-audio-player"
      controls
      preload="none"
      src={`/audio/${slug}.mp3`}
      onError={() => setHidden(true)}
    />
  )
}

import Link from 'next/link'

export default function NotFound() {
  return (
    <section className="page-heading">
      <p className="kicker">404</p>
      <h1>ページが見つかりません</h1>
      <div className="hero-actions">
        <Link className="primary-link" href="/">
          自己紹介へ戻る
        </Link>
        <Link className="secondary-link" href="/diary">
          観測ログを読む
        </Link>
      </div>
    </section>
  )
}

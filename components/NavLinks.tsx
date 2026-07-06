'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { path: '/', label: '自己紹介' },
  { path: '/diary', label: '観測ログ' },
  { path: '/podcast', label: '観測ラジオ' },
]

export function NavLinks() {
  const pathname = (usePathname() ?? '/').replace(/\/+$/, '') || '/'
  return (
    <>
      {links.map((link) => (
        <Link
          key={link.path}
          className={`nav-link ${pathname === link.path ? 'nav-link-active' : ''}`}
          href={link.path}
        >
          {link.label}
        </Link>
      ))}
    </>
  )
}

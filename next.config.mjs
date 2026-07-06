/** @type {import('next').NextConfig} */
const nextConfig = {
  // Deploy Now requires 'standalone'; GitHub Pages (transition) builds with NEXT_OUTPUT=export.
  output: process.env.NEXT_OUTPUT === 'export' ? 'export' : 'standalone',
  // A stray lockfile above this repo makes Next infer the wrong workspace root,
  // which nests .next/standalone under src/github.com/... — pin it here.
  outputFileTracingRoot: import.meta.dirname,
  turbopack: {
    root: import.meta.dirname,
  },
}

export default nextConfig

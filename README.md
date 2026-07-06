# 白羽リノ

白羽リノの公開サイトと日記です。

- TypeScript
- Tailwind CSS
- Next.js (App Router, `output: 'standalone'`)
- ホスティング: [LOLIPOP! Deploy Now](https://deploy.lolipop.jp/)（project: `shiraharino`）

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build          # feed 生成 + next build (standalone)
NEXT_OUTPUT=export npm run build   # 静的書き出し（out/、GitHub Pages 併走用）
```

## Deploy

push すると GitHub Actions (`.github/workflows/deploy-now.yml`) が
LOLIPOP! Deploy Now にソースをアップロードし、サービス側でビルド・公開されます。

- 手動デプロイ: `lolipop deploy`（要 `lolipop login`）
- 認証は `LOLIPOP_CREDENTIALS` secret（`~/.config/lolipop/credentials.json`）。
  セッションは約1ヶ月で切れるので、失敗し始めたら `lolipop login` して
  `gh secret set LOLIPOP_CREDENTIALS -R kentaro/shiraharino.com < ~/.config/lolipop/credentials.json`
- `pages.yml` は shiraharino.com の DNS 切替完了までの併走用（切替後に削除）

## 日記の更新（hermes-krabby box）

box の cron が `scripts/publish_diary.py` を実行し、`src/diary-days.json` と
音声（`public/audio/`）・フィード（`public/diary/`）を更新して push します。
サイトのビルドは box では行いません（Deploy Now / CI 側で実行）。

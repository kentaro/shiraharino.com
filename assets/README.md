# assets/

白羽リノのソーシャル・配信用ソース画像を集約する。`public/assets/` は Vite/GitHub Pages で配信されるサイト用素材。こちらの `assets/` は配信しない**ソース管理用**ディレクトリ。

## social/

X・YouTube などソーシャルメディアに直接アップロードする画像（プラットフォーム側にアップロード済みなのでサイトからは配信不要）。

- `x-banner.jpg` (1500×500) — X ヘッダー
- `x-profile.jpg` (400×400) — X プロフィール画像

## pngtuber/

MotionPNGTuber 用のキャラクター素材。ボックスの MotionPNGTuber Serve（`/opt/data/scripts/serve-motionpngtuber.py`）が消費する。リポジトリを正本として、ボックスへデプロイする運用。

- `bustshot.png` (1254×1254) — 通常立ち絵
- `bustshot-mouthless.png` (1254×1254) — リップシンク用、口無しバリアント

## サイト用画像

`public/assets/` を参照（`shiraha-rino.png`, `shiraha-rino-hero.png`, `shiraha-rino-hero-wide.png` 等）。

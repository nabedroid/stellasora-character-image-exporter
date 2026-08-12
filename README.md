# 概要
ステラソラのアセットからキャラクター画像を抽出する。

# 使い方
1. `.env.sample` を `.env` にリネーム
2. `.env` を編集してステラソラのインストール先を設定する
3. `docker compose run --rm app bash`
4. コンテナ内で下記を実行
```bash
# 全てのキャラの立ち絵とアイコンを抽出
python -m src.main
# 特定のキャラの立ち絵とフォトメモを抽出
python -m src.exporters.char_2d_exporter --character-id 103
# 特定のキャラのアイコンのみを抽出
python -m src.exporters.icon_exporter --character-id 103
# 特定のキャラ（NPC込み）の立ち絵（衣装差分込み）を抽出
python -m src.exporters.char_avg_2d_exporter --character-id 103
```

## webp 変換
png を webp に変換して 1MB 以下にする
```bash
# /output/コハク 内の png を webp に変換して /output/コハク に保存
python -m src.png2webp /output/コハク
```
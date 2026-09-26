import argparse
from pathlib import Path

import tqdm
from PIL import Image

# 対象とする拡張子のセット（小文字表記）
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def image2webp(image_path: Path, webp_path: Path, max_file_size: int) -> None:
  """画像 (PNG/JPG) を WebP に変換する
  指定サイズを超える場合は品質を下げて再保存する

  Args:
    image_path: 入力画像のパス
    webp_path: webpの保存先
    max_file_size: 最大ファイルサイズ (バイト単位)
  """
  with Image.open(image_path) as img:
    # 保存先フォルダの作成
    webp_path.parent.mkdir(parents=True, exist_ok=True)

    # 透過情報の有無に応じてカラーモードを整理
    if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
      img = img.convert("RGBA")
    else:
      img = img.convert("RGB")

    # まずは無劣化で変換
    img.save(webp_path, format="WEBP", lossless=True)

    # 指定サイズを超えている場合は品質を 10 ずつ下げて再保存
    quality: int = 90
    while webp_path.stat().st_size > max_file_size and quality > 0:
      img.save(webp_path, format="WEBP", lossless=False, quality=quality, method=6)
      quality -= 10

    # 最終的に指定サイズを超えている場合はエラー
    if webp_path.stat().st_size > max_file_size:
      webp_path.unlink()
      raise ValueError(f"{image_path.name} is larger than {max_file_size // 1024} KB")


def images2webp(input_dir_path: Path, output_dir_path: Path, max_file_size: int) -> None:
  """指定されたフォルダ内の画像 (PNG/JPG) を webp に一括変換する

  Args:
    input_dir_path: 入力フォルダのパス
    output_dir_path: webpの保存先
    max_file_size: 最大ファイルサイズ (バイト単位)
  """
  # 対応している拡張子のファイルをすべて取得
  image_files = [
    p for p in input_dir_path.iterdir()
    if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
  ]

  for image_path in tqdm.tqdm(image_files, desc="Converting to WebP"):
    webp_path = (output_dir_path / image_path.name).with_suffix(".webp")
    image2webp(image_path, webp_path, max_file_size)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="PNG / JPG 画像を WebP に変換するスクリプト")
  parser.add_argument("input", type=Path, help="入力画像ファイルまたは入力ディレクトリのパス")
  parser.add_argument("--output", type=Path, default=None, help="webpの保存先 (ファイルまたはディレクトリ)")
  parser.add_argument("--max-file-size", type=int, default=1024, help="最大ファイルサイズ (KB)")
  args = parser.parse_args()

  if not args.input.exists():
    print(f"入力が存在しません: {args.input}")
    exit(1)

  max_size_bytes = args.max_file_size * 1024

  if args.input.is_file():
    if args.input.suffix.lower() not in SUPPORTED_EXTENSIONS:
      print(f"未対応のファイルフォーマットです: {args.input.suffix}")
      exit(1)
    if args.output is None:
      args.output = args.input.with_suffix(".webp")
    image2webp(args.input, args.output, max_size_bytes)
  else:
    if args.output is None:
      args.output = args.input
    images2webp(args.input, args.output, max_size_bytes)

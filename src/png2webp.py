import argparse
from pathlib import Path

import tqdm
from PIL import Image

def png2webp(png_path: Path, webp_path: Path, max_file_size: int) -> None:
  """png を webp に変換する
  指定サイズを超える場合は品質を下げて再保存する

  Args:
    png_path: pngの保存先
    webp_path: webpの保存先
    max_file_size: 最大ファイルサイズ (KB)
  """

  with Image.open(png_path) as img:
    # フォルダ作成
    webp_path.parent.mkdir(parents=True, exist_ok=True)
    
    # RGBA / RGB モードの維持 (必要に応じて変換)
    if "transparency" in img.info:
      img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA"):
      img = img.convert("RGBA")

    # 無劣化で変換する
    img.save(webp_path, format="WEBP", lossless=True)

    # 指定サイズを超えている場合は、品質を 10 ずつ下げて再保存
    quality: int = 90
    while webp_path.stat().st_size > max_file_size and quality > 0:
      img.save(webp_path, format="WEBP", lossless=False, quality=quality, method=6)
      quality -= 10

    # 最終的に指定サイズを超えている場合はエラー
    if webp_path.stat().st_size > max_file_size:
      webp_path.unlink()
      raise ValueError(f"{png_path.name} is larger than {max_file_size} KB")

def png2webps(input_dir_path: Path, output_dir_path: Path, max_file_size: int) -> None:
  """指定されたフォルダ内の png を webp に変換する

  Args:
    input_dir_path: pngの保存先
    output_dir_path: webpの保存先
    max_file_size: 最大ファイルサイズ (KB)
  """
  png_files = list(input_dir_path.glob("*.png"))
  for png_path in tqdm.tqdm(png_files, desc="Converting to WebP"):
    webp_path = (output_dir_path / png_path.name).with_suffix(".webp")
    png2webp(png_path, webp_path, max_file_size)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("input", type=Path, help="pngの保存先")
  parser.add_argument("--output", type=Path, default=None, help="webpの保存先ディレクトリ")
  parser.add_argument("--max-file-size", type=int, default=1024, help="最大ファイルサイズ (KB)")
  args = parser.parse_args()

  if not args.input.exists():
    print(f"入力ファイルが存在しません: {args.input}")
    exit(1)
  if args.input.is_file():
    if args.output is None:
      args.output = args.input.with_suffix(".webp")
    png2webp(args.input, args.output, args.max_file_size * 1024)
  else:
    if args.output is None:
      args.output = args.input
    png2webps(args.input, args.output, args.max_file_size * 1024)
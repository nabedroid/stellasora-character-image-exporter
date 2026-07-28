import argparse

from .exporters import icon_exporter
from .exporters import char_2d_exporter

def _parser():
  parser = argparse.ArgumentParser(description="ゲームアセット抽出スクリプト")

  parser.add_argument(
    "--output",
    type=str,
    default="/output",
    help="画像の出力先ディレクトリ (default: /output)",
  )
  parser.add_argument(
    "--character-id",
    type=str,
    default=None,
    help="特定キャラクターIDのみ抽出する場合に指定 (例: 103)",
  )
  parser.add_argument(
    "--target",
    type=str,
    choices=["all", "tachie", "icon"],
    default="all",
    help="抽出する対象を選択 (default: all)",
  )

  return parser

if __name__ == "__main__":
  parser = _parser()
  args = parser.parse_args()

  if args.target in ("tachie", "all"):
    char_2d_exporter.export_char_2d(args.output, args.character_id)
  if args.target in ("icon", "all"):
    icon_exporter.export_icon(args.output, args.character_id)


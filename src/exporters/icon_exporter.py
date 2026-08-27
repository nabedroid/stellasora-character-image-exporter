import argparse
import os
import re

import tqdm
import UnityPy

from .. import asset_finder
from ..utils import image_utils
from ..utils import string_utils

def export_icon(output_dir: str, character_id: str = None):
  """アイコン系のアセットから画像を抽出する
  - キャラクターの顔アイコン
  - スキルアイコン
  - デートアイコン
  
  Args:
    output_dir (str): 出力先ディレクトリ
    character_id (str): キャラクターID(デフォルトは全キャラクター)
  """

  # アイコン関連のアセットバンドルを検索
  for p in tqdm.tqdm(asset_finder.glob_assets("icon*"), desc="exporting icon images"):
    # アセットバンドルを読み込む
    env = UnityPy.load(str(p))
    for path, obj in env.container.items():
      # Sprite 以外はスキップ
      if obj.type.name != "Sprite": continue
      # アイコンの種類を判定する
      basename = os.path.basename(path)
      if match := re.match(r"head_(\d{3})(\d{2})_xxl\.png", basename):
        # キャラクターアイコン
        # XL: 304*404, XXL:192*192, XXLS: 96*96

        # キャラクター指定があったら、スキップ
        if character_id and character_id != match.group(1): continue

        character_name = string_utils.character_id_to_name(match.group(1))
        version = "" if match.group(2) == "01" else f"{int(match.group(2))}"        
        output_path = os.path.join(output_dir, character_name, f"{character_name}_icon{version}.png")
        image_utils.save_image(obj.read().image, output_path)
      elif match := re.match(r"(\d{3})(\d{2})_(normal|skill_main|skill_support|ultra)\.png", basename):
        # スキルアイコン

        # キャラクター指定があったら、スキップ
        if character_id and character_id != match.group(1): continue

        data = obj.read()
        output_path = os.path.join(output_dir, "img", f"{data.m_Name}.png")
        image_utils.save_image(data.image, output_path)
      elif match := re.match(r"datingspcg_(\d{3})(\d{3})\.png", basename):
        # デートアイコン

        # キャラクター指定があったら、スキップ
        if character_id and character_id != match.group(1): continue

        character_name = string_utils.character_id_to_name(match.group(1))
        version = int(match.group(2)) - 300
        output_path = os.path.join(output_dir, character_name, f"{character_name}_デート{version}.png")
        image_utils.save_image(obj.read().image, output_path)
      else:
        # 関係のない画像
        pass

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="アイコン系のアセットから画像を抽出する")

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

  args = parser.parse_args()

  export_icon(args.output, args.character_id)
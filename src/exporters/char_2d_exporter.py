import argparse
import os
import re

import tqdm
import UnityPy

from .. import asset_finder
from ..utils import image_utils
from ..utils import string_utils

def export_char_2d(output_dir: str, character_id: str = None):
  """
  立ち絵を含むアセットから画像を抽出する
  - 立ち絵
    - 全身
    - 表情
  - フォトメモ

  Args:
    output_dir (str): 出力先ディレクトリ
    character_id (str): キャラクターID(デフォルトは全キャラクター)
  """

  for p in tqdm.tqdm(asset_finder.glob_assets(f"char_2d_{character_id if character_id != None else ''}*.unity3d"), desc="exporting tachie images"):

    # キャラクター画像のアセットか判定
    match = re.match(r"char_2d_(\d{3})(\d{2}).unity3d", os.path.basename(p.name))
    if match == None: continue

    # キャラクターアセットなら、更にどの衣装のアセットか判定
    id_version = f"{match.group(1)}{match.group(2)}"
    character_name = string_utils.character_id_to_name(match.group(1))
    if match.group(2) == "01":
      version = ""
    elif match.group(2) == "02":
      version = "_覚醒"
    else:
      # 03以降は特別衣装等なので通番を付けておく
      version = f"_{int(match.group(2)) - 2}"

    # アセットを読み込む
    env = UnityPy.load(str(p))
    # 全身 sprite を読み込む
    body_sprite = env.container[f"assets/assetbundles/actor2d/character/{id_version}/atlas_png/a/{id_version}_001.png"].read()
    # 表情 sprite を読み込む
    face_sprite = env.container[f"assets/assetbundles/actor2d/character/{id_version}/atlas_png/a/{id_version}_002.png"].read()

    # 合成して書き出し
    image = image_utils.composite_body_face(body_sprite, face_sprite)
    image_utils.save_image(image, os.path.join(output_dir, character_name, f"{character_name}{version}.png"))

    # フォトメモを取得する（覚醒などでフォトメモない場合はスキップ）
    photomemo_key = f"assets/assetbundles/actor2d/character/{id_version}/{id_version}_cg.png"
    if photomemo_key in env.container:
      photo_sprite = env.container[photomemo_key].read()
      image_utils.save_image(photo_sprite.image, os.path.join(output_dir, character_name, f"{character_name}_フォトメモ.png"))

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="立ち絵系のアセットから画像を抽出する")

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

  export_char_2d(args.output, args.character_id)
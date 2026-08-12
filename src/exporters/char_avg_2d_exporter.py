import argparse
import os
import re

import tqdm
import UnityPy

from .. import asset_finder
from ..utils import image_utils
from ..utils import string_utils

def export_char_avg_2d(output_dir: str, character_id: str = None):
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

  for p in tqdm.tqdm(asset_finder.glob_assets(f"char_avg_2d_avg*_{character_id if character_id != None else '*'}.unity3d"), desc="exporting avg tachie images"):

    # キャラクター画像のアセットか判定
    match = re.match(r"char_avg_2d_(avg\d)_(\d{3}).unity3d", os.path.basename(p.name))
    if match == None: continue

    # キャラクターアセットなら、各衣装ごとに出力する
    avgn = match.group(1)
    char_id = match.group(2)
    body_face_dict = {}

    # アセットを読み込む
    env = UnityPy.load(str(p))

    for path, obj in env.container.items():
      if obj.type.name != "Sprite": continue
      match = re.match(f"{avgn}_{char_id}_([a-z]+)_(001|002)\\.png", os.path.basename(path))
      if match == None: continue
      skin_code = match.group(1)
      part_id = match.group(2)

      body_face_dict[skin_code] = body_face_dict.get(skin_code, {"001": None, "002": None})
      body_face_dict[skin_code][part_id] = obj
    
    for skin_code, parts in body_face_dict.items():
      # 立ち絵のパーツが揃っている場合は画像を出力する
      if parts["001"] == None or parts["002"] == None: continue
      body_sprite = parts["001"].read()
      face_sprite = parts["002"].read()
      image = image_utils.composite_body_face(body_sprite, face_sprite)
      image_utils.save_image(image, os.path.join(output_dir, f"{avgn}_{char_id}", f"{avgn}_{char_id}_{skin_code}.png"))

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

  export_char_avg_2d(args.output, args.character_id)
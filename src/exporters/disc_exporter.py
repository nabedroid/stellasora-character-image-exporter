import argparse
import os
import re

import tqdm
import UnityPy

from .. import asset_finder
from ..utils import image_utils
from ..utils import string_utils


def export_disc(output_dir: str, disc_id: str = None):
  """
  ロスレコアセットから画像を抽出する

  Args:
    output_dir (str): 出力先ディレクトリ
    disc_id (str): ロスレコID(デフォルトは全ロスレコ)
  """
  # ロスレコ共通のアセット
  disc_common_asset_path = asset_finder.glob_assets("disc_common.unity3d")[0]
  #for p in tqdm.tqdm(asset_finder.glob_assets(f"disc_{disc_id if disc_id != None else '*'}.unity3d"), desc="exporting disc images"):
  for p in asset_finder.glob_assets(f"disc_{disc_id if disc_id != None else '*'}.unity3d"):

    # ロスレコのアセットか判定
    match = re.match(r"disc_(\d+).unity3d", os.path.basename(p.name))
    if match == None: continue

    id = match.group(1)

    # ロスレコID が指定されている場合はそれ以外のファイルはスキップ
    if disc_id != None and disc_id != match.group(1):
      continue

    # アセットを読み込む
    env = UnityPy.load(str(disc_common_asset_path), str(p))
    game_object_ref = None
    sprite_ref = None
    # 本体のGameObjectを取得する
    for path, obj in env.container.items():
      if path.endswith(f"/{id}_g.prefab") and obj.type.name == "GameObject":
        # GameObject
        game_object_ref = obj
        break
      elif path.endswith(f"{id}_b.png") and obj.type.name == "Sprite":
        # 完成画像
        sprite_ref = obj
    # GameObject が取れたならそれを使って画像を作成する
    # 取れなかったら完成画像を使ってファイル出力する
    image = None
    if game_object_ref is not None:
      game_object = game_object_ref.read()
      image = image_utils.create_image_from_game_object(game_object)
    elif sprite_ref is not None:
      sprite = sprite_ref.read()
      image = sprite.image
    if image is not None:
      image_utils.save_image(image, f"{output_dir}/{id}.png")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="ロスレコアセットから画像を抽出する")

  parser.add_argument(
    "--output",
    type=str,
    default="/output",
    help="画像の出力先ディレクトリ (default: /output)",
  )
  parser.add_argument(
    "--disc-id",
    type=str,
    default=None,
    help="特定ロスレコIDのみ抽出する場合に指定 (例: 4001)",
  )

  args = parser.parse_args()

  export_disc(args.output, args.disc_id)
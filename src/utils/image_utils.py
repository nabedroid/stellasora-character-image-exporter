from src import asset_finder
import os
import sys

from PIL import Image

def save_image(image: Image.Image, output_path: str):
  """画像をファイルとして保存する（保存先ディレクトリがない場合は自動作成する）

  Args:
    image (Image.Image): 保存対象の PIL Image オブジェクト
    output_path (str): 保存先のファイルパス
  """

  # ディレクトリ作成
  os.makedirs(os.path.dirname(output_path), exist_ok=True)
  # 画像書き出し
  image.save(output_path)


def _get_pivot_offset(sprite: any) -> tuple[float, float]:
  """スプライトのPivot（中心）を(0,0)とした場合の、実画像の左上座標(X, Y)を取得する"""
  img = sprite.image
  rect_w = float(sprite.m_Rect.width)
  rect_h = float(sprite.m_Rect.height)

  # Pivot（中心点）のピクセル座標
  pivot_x = rect_w * float(sprite.m_Pivot.x)
  pivot_y = rect_h * float(sprite.m_Pivot.y)

  # m_Rect内での実画像の左上位置 (UnityはY軸上が正のため反転)
  left = float(sprite.m_RD.textureRectOffset.x)
  top = rect_h - float(sprite.m_RD.textureRectOffset.y) - img.height

  # Pivotからの相対座標 (X, Y)
  return left - pivot_x, top - (rect_h - pivot_y)


def composite_body_face(body_sprite: any, face_sprite: any) -> any:
  """全身と表情のスプライトを合成する

  Args:
    body_sprite (Sprite): 全身画像のスプライトオブジェクト
    face_sprite (Sprite): 表情画像のスプライトオブジェクト

  Returns:
    Image.Image: 全身と顔を合成した画像
  """
  body_img = body_sprite.image
  face_img = face_sprite.image

  # それぞれの Pivot からの相対位置を取得
  body_x, body_y = _get_pivot_offset(body_sprite)
  face_x, face_y = _get_pivot_offset(face_sprite)

  # 全身画像の左上(0, 0)を基準とした顔の貼り付け位置を計算
  paste_x = int(round(face_x - body_x))
  paste_y = int(round(face_y - body_y))

  # 合成処理
  canvas = Image.new("RGBA", body_img.size, (0, 0, 0, 0))
  canvas.paste(body_img, (0, 0))
  canvas.alpha_composite(face_img, (paste_x, paste_y))

  return canvas


def _create_image(transform: any, depth: int = 0) -> Image.Image:
  indent = "  " * depth
  game_object = transform.m_GameObject.read()
  sprite = None
  scripts = []

  # ジャイロは不要なのでスキップ
  if "Gyroscope" in game_object.m_Name: return None

  print(f"{indent}- {game_object.m_Name}",
        f"Size:({transform.m_SizeDelta.x:.0f},{transform.m_SizeDelta.y:.0f})",
        f"Scale: ({transform.m_LocalScale.x:.1f},{transform.m_LocalScale.y:.1f})",
        f"LPos: ({transform.m_LocalPosition.x:.0f},{transform.m_LocalPosition.y:.0f},{transform.m_LocalPosition.z:.0f})",
        f"APos: ({transform.m_AnchoredPosition.x:.0f},{transform.m_AnchoredPosition.y:.0f})",
        f"AnchorMin-Max: ({transform.m_AnchorMin.x:.1f},{transform.m_AnchorMin.y:.1f})-({transform.m_AnchorMax.x:.1f},{transform.m_AnchorMax.y:.1f})",
        f"Pivot: ({transform.m_Pivot.x:.1f},{transform.m_Pivot.y:.1f})",
  )

  # GameObject が所持しているスプライト画像を取得
  for comp_pair in game_object.m_Component:
    ptr = getattr(comp_pair, "component", comp_pair)
    if not ptr: continue
    comp_obj = ptr.read()
    if ptr.type.name == "MonoBehaviour":
      if hasattr(comp_obj, "m_Sprite") and getattr(comp_obj.m_Sprite, "path_id", 0) != 0:
        sprite = comp_obj.m_Sprite.read()
        print(f"{indent}  + {sprite.m_Name}{sprite.image.size}")
        break
      elif comp_obj.m_Script:
        scripts.append(comp_obj.m_Script.read())

  # GameObject 配下の Transform を取得する
  childs = []
  x1, y1 = sys.maxsize, sys.maxsize
  x2, y2 = -sys.maxsize - 1, -sys.maxsize - 1
  for child_ref in transform.m_Children:
    c_transform = child_ref.read()
    c_image = _create_image(c_transform, depth + 1)
    if c_image is not None:
      sdx = c_image.width if c_transform.m_SizeDelta.x <= 0 else c_transform.m_SizeDelta.x
      sdy = c_image.height if c_transform.m_SizeDelta.y <= 0 else c_transform.m_SizeDelta.y
      #resized_w = int(sdx * c_transform.m_LocalScale.x)
      #resized_h = int(sdy * c_transform.m_LocalScale.y)
      resized_w = c_image.width
      resized_h = c_image.height

      offx = c_image.width / 2
      offy = c_image.height / 2
      x1 = min(x1, -offx - c_transform.m_AnchoredPosition.x)
      y1 = min(y1, -offy + c_transform.m_AnchoredPosition.y)
      x2 = max(x2, offx + c_transform.m_AnchoredPosition.x)
      y2 = max(y2, offy - c_transform.m_AnchoredPosition.y)
      c_image_resized = c_image.resize((resized_w, resized_h))
      childs.append([c_transform, c_image_resized])
  # z軸で降順にソートする
  if len(childs) == 0:
    return sprite.image if sprite else None

  childs.sort(key=lambda x: x[0].m_LocalPosition.z, reverse=True)
  width = int(x2 - x1)
  height = int(y2 - y1)
  cx = width / 2
  cy = height / 2

  image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
  for child_transform, child_image in childs:
    # 合成する
    x = int(cx - child_image.width / 2 + child_transform.m_AnchoredPosition.x)
    y = int(cy - child_image.height / 2 - child_transform.m_AnchoredPosition.y)

    image.alpha_composite(child_image, (x, y))

  return image


def create_image_from_game_object(root_game_object: any) -> Image.Image:
  """GameObjectからスプライトを収集し、正しい配置で合成した画像を返す"""
  root_transform_ref = root_game_object.m_Component[0].component
  root_transform = root_transform_ref.read()
  return _create_image(root_transform)
  # image = None

  # for child_ref in root_transform.m_Children:
  #   child_transform = child_ref.read()
  #   child_game_object = child_transform.m_GameObject.read()
  #   if child_game_object.m_Name == "layer_title":
  #     image = _create_image(child_transform)
  #     break

  # return image
from src import asset_finder
import os
import sys
import math
from PIL import Image

# 開発環境のCanvas設計解像度（高さ）とカメラFOVを設定
CANVAS_HEIGHT = 1080.0
CAMERA_FOV = 60.0

# 基準距離 D_ref の計算
D_REF = (CANVAS_HEIGHT / 2.0) / math.tan(math.radians(CAMERA_FOV / 2.0))

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

# うまく動作していない。
# 現状の問題点は下記の通り。
# - 各Sprite画像がもろもろの補正の結果、横長につぶれている
# - キャラクター Sprite の配置位置が若干右上にずれてしまっている
#   - 文字もずれてると思う
# どの部分で補正をかけるべきか、あるいは補正の仕方が間違っているのか再検討が必要
def _create_image(transform: any, parent_world_z: int = 0, depth: int = 0) -> Image.Image:
  indent = "  " * depth
  game_object = transform.m_GameObject.read()
  sprite = None
  scripts = []

  # ジャイロは不要なのでスキップ
  if "Gyroscope" in game_object.m_Name: return None

  current_world_z = parent_world_z + transform.m_LocalPosition.z

  print(f"{indent}- {game_object.m_Name}",
        f"Size:({transform.m_SizeDelta.x:.0f},{transform.m_SizeDelta.y:.0f})",
        f"Scale: ({transform.m_LocalScale.x:.1f},{transform.m_LocalScale.y:.1f})",
        f"LPos: ({transform.m_LocalPosition.x:.0f},{transform.m_LocalPosition.y:.0f},{transform.m_LocalPosition.z:.0f})",
        f"APos: ({transform.m_AnchoredPosition.x:.0f},{transform.m_AnchoredPosition.y:.0f})",
        #f"AnchorMin-Max: ({transform.m_AnchorMin.x:.1f},{transform.m_AnchorMin.y:.1f})-({transform.m_AnchorMax.x:.1f},{transform.m_AnchorMax.y:.1f})",
        #f"Pivot: ({transform.m_Pivot.x:.1f},{transform.m_Pivot.y:.1f})",
        f"CurrentWorldZ: {current_world_z}",
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
    c_image = _create_image(c_transform, current_world_z, depth + 1)
    if c_image is not None:
      # 1. Z座標によるパース倍率計算
      c_world_z = current_world_z + c_transform.m_LocalPosition.z
      persp_ratio = D_REF / (D_REF + c_world_z)

      # 2. X軸回転 (Quaternion: x, w) から Y方向の投影圧縮率 (cos θ) を算出
      q_x = c_transform.m_LocalRotation.x
      q_w = c_transform.m_LocalRotation.w
      rot_x_rad = 2.0 * math.atan2(q_x, q_w)
      y_projection_factor = math.cos(rot_x_rad)

      # 3. 描画基準サイズの確定 (m_SizeDelta があれば優先、無ければ元画像サイズ)
      base_w = (
        c_transform.m_SizeDelta.x
        if c_transform.m_SizeDelta.x > 0
        else c_image.width
      )
      base_h = (
        c_transform.m_SizeDelta.y
        if c_transform.m_SizeDelta.y > 0
        else c_image.height
      )

      # 4. Scale と 投影補正、パース倍率を適用した最終リサイズ幅・高さ
      scale_x = c_transform.m_LocalScale.x
      scale_y = c_transform.m_LocalScale.y * y_projection_factor

      resized_w = max(1, int(base_w * scale_x * persp_ratio))
      resized_h = max(1, int(base_h * scale_y * persp_ratio))

      # 5. パース倍率を適用した中心からの座標オフセット (Unity: Y上向きが正)
      pos_x = c_transform.m_AnchoredPosition.x * persp_ratio
      pos_y = c_transform.m_AnchoredPosition.y * persp_ratio

      # 6. バウンディングボックス (最左x1, 最下y1, 最右x2, 最上y2) の更新
      offx = resized_w / 2.0
      offy = resized_h / 2.0

      x1 = min(x1, pos_x - offx)  # 最左端
      x2 = max(x2, pos_x + offx)  # 最右端
      y1 = min(y1, pos_y - offy)  # 最下端（下半身などマイナス方向）
      y2 = max(y2, pos_y + offy)  # 最上端

      # 7. 画像リサイズ & 配列追加
      c_image_resized = c_image.resize(
        (resized_w, resized_h), Image.Resampling.LANCZOS
      )
      childs.append([c_transform, c_image_resized, pos_x, pos_y, c_world_z])

  # 末端の場合はスプライトをそのまま返す
  if len(childs) == 0:
    return sprite.image if sprite else None

  # z軸で降順にソートする
  childs.sort(key=lambda x: x[4], reverse=True)

  # 全要素を含むキャンバス幅・高さを算出
  width = int(math.ceil(x2 - x1))
  height = int(math.ceil(y2 - y1))

  image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

  # 最左上角 (x1, y2) を原点として絶対座標合成
  for child_transform, child_image, pos_x, pos_y, _ in childs:
    px = int(round((pos_x - child_image.width / 2.0) - x1))
    py = int(round(y2 - (pos_y + child_image.height / 2.0)))

    image.alpha_composite(child_image, (px, py))

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
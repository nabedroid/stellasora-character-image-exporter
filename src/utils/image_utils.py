import os

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
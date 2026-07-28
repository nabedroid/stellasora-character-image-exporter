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


def composite_body_face(body_sprite: any, face_sprite: any) -> any:
  """全身絵と顔のスプライト画像を透明キャンバス上に配置・合成する

  Args:
    body_sprite (Sprite): 全身画像のスプライトオブジェクト
    face_sprite (Sprite): 表情画像のスプライトオブジェクト

  Returns:
    Image.Image: 全身と顔を合成した画像
  """
  width = int(body_sprite.m_Rect.width)
  height = int(body_sprite.m_Rect.height)
  images = []
  for sprite in [body_sprite, face_sprite]:
    image = Image.new("RGBA", (width, height), (0,0,0,0))
    image.paste(sprite.image, (
        int(sprite.m_RD.textureRectOffset.x),
        height - int(sprite.m_RD.textureRectOffset.y) - int(sprite.image.height),
      ),
    )
    images.append(image)
  image = Image.alpha_composite(images[0], images[1])
  return image
from .. import config

def character_id_to_name(character_id: str) -> str:
  '''
  キャラクターIDをキャラクター名に変換する
  存在しない場合は、IDをそのまま返す
  
  Args:
    character_id: キャラクターID
    
  Returns:
    キャラクター名
  '''
  return config.CHARACTER_MAP.get(character_id, character_id)
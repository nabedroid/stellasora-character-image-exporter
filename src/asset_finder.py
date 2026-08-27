from pathlib import Path

_STREAMING_ASSETS_PATH = Path("/StellaSora_JP/StellaSora_Data/StreamingAssets/InstallResource")
_PERSISTENT_DATA_PATH = Path("/StellaSora_JP/Persistent_Store/AssetBundles")

def glob_assets(glob_filename: str, is_streaming: bool = False, is_persistent: bool = True) -> list[Path]:
  """
  streamingAssetsPath 及び persistentDataPath から最新のアセットファイルを取得する
  
  Args:
    glob_filename: glob パターン
    is_streaming: streamingAssetsPath を検索対象とするか
    is_persistent: persistentDataPath を検索対象とするか

  Returns:
    最新のアセットファイルリスト
  """

  if is_streaming and is_persistent:
    return _glob_assets_streaming_persistent(glob_filename)
  elif is_streaming:
    return _glob_assets_streaming(glob_filename)
  elif is_persistent:
    return _glob_assets_persistent(glob_filename)
  else:
    return []

def _glob_assets_streaming_persistent(glob_filename: str) -> list[Path]:
  asset_map: dict[str, Path] = {}

  for path in _STREAMING_ASSETS_PATH.glob(glob_filename):
    asset_map[path.name] = path
  
  for path in _PERSISTENT_DATA_PATH.glob(glob_filename):
    if path.name not in asset_map:
      asset_map[path.name] = path
    elif path.stat().st_mtime > asset_map[path.name].stat().st_mtime:
      asset_map[path.name] = path
    else:
      pass
  return list(asset_map.values())

def _glob_assets_streaming(glob_filename: str) -> list[Path]:
  return list(_STREAMING_ASSETS_PATH.glob(glob_filename))

def _glob_assets_persistent(glob_filename: str) -> list[Path]:
  return list(_PERSISTENT_DATA_PATH.glob(glob_filename))
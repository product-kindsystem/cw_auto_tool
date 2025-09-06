from pathlib import Path
import json
import os
from tempfile import NamedTemporaryFile

# ---- JSON 読み込み ----
def read_json(path: Path, default=None):
    """ファイルが無い/壊れている場合は default を返す"""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {} if default is None else default

# ---- JSON 書き込み（安全に原子的に置き換え）----
def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)  # 既存ファイルと置き換え

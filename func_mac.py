import subprocess
import sys
import platform
import subprocess
from pathlib import Path

def is_mac_os() -> bool:
    # macOS なら True（最も一般的）
    return sys.platform == "darwin" or platform.system() == "Darwin"


def mac_arch() -> str:
    # 'arm64'（Apple Silicon） or 'x86_64'（Intel）
    return platform.machine()


def mac_is_rosetta2() -> bool:
    # Apple Silicon で x86_64 バイナリとして動いている（Rosetta2）か判定
    if not is_mac_os():
        return False
    try:
        out = subprocess.check_output(["sysctl", "-in", "sysctl.proc_translated"]).strip()
        return out == b"1"
    except Exception:
        return False


def mac_app_base_dir() -> Path:
    # PyInstaller の .app 実行時は実行ファイル直下(Contents/MacOS)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # 通常実行（python main.py）
    return Path(__file__).parent


def mac_user_data_dir(mac_app_name) -> Path:
    # macOS のユーザ書き込み領域
    return Path.home() / "Library" / "Application Support" / mac_app_name

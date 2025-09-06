import subprocess
import time
import os
import psutil


def kill_chrome():
    # Chrome プロセスが起動中か確認
    chrome_running = any(proc.name() == "chrome.exe" for proc in psutil.process_iter())

    if chrome_running:
        try:
            # Chrome プロセスの強制終了
            subprocess.run("taskkill /F /IM chrome.exe /T", shell=True)
            print("Chrome processes terminated.")
        except Exception as e:
            print(f"An error occurred: {e}")

        # 3秒間の待機
        time.sleep(3)
    else:
        print("Chrome is not running.")


def launch_debug_chrome(profile="16"):
    chrome_64bit_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_32bit_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    profile_directory = "Profile " + profile
    debugging_port = "9222"

    if os.path.exists(chrome_64bit_path):
        print("64bitファイルが存在しています。")
        subprocess.Popen([
            chrome_64bit_path,
            f"--profile-directory={profile_directory}",
            f"--remote-debugging-port={debugging_port}",
            "--start-maximized"
        ])
    elif os.path.exists(chrome_32bit_path):
        print("32bitファイルが存在しています。")
        subprocess.Popen([
            chrome_32bit_path,
            f"--profile-directory={profile_directory}",
            f"--remote-debugging-port={debugging_port}",
            "--start-maximized"
        ])
    else:
        print("Chromeがインストールされていません。")

    time.sleep(3)

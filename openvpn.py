import requests
import os
import shutil
import psutil
import subprocess
import random
import base64
from time import sleep


# OpenVPN クライアントinstaller
# https://www.openvpn.jp/download/
# Windows起動時に開始をOFFにする


class openvpn:

    def __init__(self, logger, skip_mode):
        self.logger = logger
        self.skip_mode = skip_mode

    def __del__(self):
        self.end()

    def restart(self):
        result = False
        try_count = 0
        while try_count < 5:
            try_count += 1
            self.logger.info(f'openvpn restart {try_count}')
            self.end()
            result = self.start()
            if result:
                break
        if result:
            self.logger.info(f'openvpn restart : success')
        else:
            self.logger.info(f'openvpn restart : failure')
        return result

    def start(self):
        if self.skip_mode:
            return True

        def get_vpn_servers():
            url = 'http://www.vpngate.net/api/iphone/'
            response = requests.get(url)

            if response.status_code != 200:
                raise Exception("VPN Gateサーバーリストの取得に失敗しました。")

            # データを取得し、サーバー情報をパース
            servers = []
            lines = response.text.splitlines()
            for line in lines[2:]:  # 最初の2行はヘッダー
                cols = line.split(',')
                if len(cols) > 14:
                    server = {
                        'ip': cols[1],
                        'country': cols[6],
                        'vpn_config': cols[14]  # OpenVPN設定がbase64でエンコードされている
                    }
                    if server['country'] == 'JP':
                        servers.append(server)
            return servers

        def create_vpn_connection(vpn_config_base64):
            startip = self.get_global_ip()
            # OpenVPN設定をデコードして一時ファイルに保存
            vpn_config = base64.b64decode(vpn_config_base64)

            with open('temp_vpn_config.ovpn', "wb") as file:
                file.write(vpn_config)

            # 暗号スイートとその他の設定を追加
            cipher_config = 'data-ciphers AES-256-GCM:AES-128-GCM:AES-128-CBC\n'
            additional_config = ('script-security 2\n')

            with open('temp_vpn_config.ovpn', "a") as file:
                file.write(cipher_config)
                file.write(additional_config)

            username = os.getlogin()
            shutil.move('temp_vpn_config.ovpn', f'C:\\Users\\{username}\\OpenVPN\\config\\temp_vpn_config.ovpn')
            sleep(1)

            connect("temp_vpn_config.ovpn")
            wait_sec = 0
            while wait_sec < 60:
                if self.check_is_running():
                    break
                sleep(1)
                wait_sec += 1

            sleep(5)

            wait_sec = 0
            while wait_sec < 60:
                curip = self.get_global_ip()
                print(curip)
                if startip != curip:  # なぜかターゲットのIPとならないことがあるがそれは許容する
                    return True
                sleep(5)
                wait_sec += 5

            return False

        def connect(config_path):
            result = subprocess.Popen([r"C:\Program Files\OpenVPN\bin\openvpn-gui.exe", "--connect", config_path])  # 非同期実行
            print(result.stdout)

        servers = get_vpn_servers()
        if not servers:
            print("利用可能なVPNサーバーがありません。")
        else:
            server = random.choice(servers)
            self.logger.info(f'connect before IP:{self.get_global_ip()}')
            self.logger.info(f"接続するVPNサーバー: {server['ip']} ({server['country']})")
            result = create_vpn_connection(server['vpn_config'])
            if result:
                self.logger.info(f"VPNサーバー接続 : 成功")
            else:
                self.logger.info(f"VPNサーバー接続 : 失敗")
            self.logger.info(f'connect after IP:{self.get_global_ip()}')
        return result

    def end(self):
        if self.skip_mode:
            return

        def disconnect():
            # OpenVPN プロセスの強制終了
            try:
                # openvpn.exe が実行中かどうかを確認
                openvpn_running = subprocess.run('tasklist /FI "IMAGENAME eq openvpn.exe"', capture_output=True, text=True, shell=True)  # 同期実行
                if "openvpn.exe" in openvpn_running.stdout:
                    print("OpenVPN is running. Terminating the process...")
                    subprocess.run("taskkill /F /IM openvpn.exe", shell=True)
                    self.logger.info("OpenVPN disconnect => 終了")
                else:
                    self.logger.info("OpenVPN disconnect => 起動なし")
                # openvpn-gui.exe が実行中かどうかを確認
                openvpn_gui_running = subprocess.run('tasklist /FI "IMAGENAME eq openvpn-gui.exe"',
                                                     capture_output=True, text=True, shell=True)  # 同期実行
                if "openvpn-gui.exe" in openvpn_gui_running.stdout:
                    print("OpenVPN-GUI is running. Terminating the process...")
                    subprocess.run("taskkill /F /IM openvpn-gui.exe", shell=True)
                    print("OpenVPN-GUI process terminated.")
                    self.logger.info("OpenVPN-GUI disconnect => 終了")
                else:
                    self.logger.info("OpenVPN-GUI disconnect => 起動なし")
            except Exception as e:
                self.logger.info("openvpn disconnect Exception : {e}")
            sleep(5)
            wait_sec = 0
            while wait_sec < 60:
                if not self.check_is_running():
                    return True
                sleep(1)
                wait_sec += 1
            return False

        self.logger.info(f'disconnect before IP:{self.get_global_ip()}')
        disconnect()
        self.logger.info(f'disconnect after IP:{self.get_global_ip()}')

    def check_is_running(self):
        # OpenVPNプロセスが存在するか確認
        openvpn_running = False
        for process in psutil.process_iter(attrs=['name']):
            if process.info['name'] == 'openvpn.exe':
                openvpn_running = True
                break
        return openvpn_running

    def get_global_ip(self):
        try:
            response = requests.get('https://api.ipify.org')
        except:
            return None
        return response.text

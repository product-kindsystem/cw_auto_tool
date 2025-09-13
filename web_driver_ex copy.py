from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from time import sleep
from webdriver_manager.chrome import ChromeDriverManager
import base64
import os
import func_mac as fm


class WebDriverEx:
    def __init__(self, setting, logger):

        self.logger = logger
        self.logger.info(f"初期化開始")
        self.setting = setting
        self.options = Options()
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.options.add_argument("--remote-debugging-port=9222")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--force-device-scale-factor=1")
        self.duration = 0.25
        self.wait_time = setting["WAIT_TIME_SEC"]
        self.tab = 0
        if setting["HIDE_CHROME"] == "True":
            self.options.add_argument('--headless')
        self.path = ChromeDriverManager().install()

        # THIRD_PARTY_NOTICES.chromedriverとなってしまう件の対処（webdriver_manager updateにより不要になる可能性あり）
        #  C:\\Users\\kashi\\.wdm\\drivers\\chromedriver\\win64\\127.0.6533.72\\chromedriver-win32/THIRD_PARTY_NOTICES.chromedriver
        if not fm.is_mac_os():
            if os.path.splitext(self.path)[1] != '.exe':
                webdriver_dir_path = os.path.dirname(self.path)
                self.path = os.path.join(webdriver_dir_path, 'chromedriver.exe')

        # Serviceオブジェクトを使用してexecutable_pathを指定
        service = Service(executable_path=self.path)

        # WebDriverの初期化
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.driverwait = WebDriverWait(self.driver, self.setting["WAIT_TIME_SEC"])
        self.driver.implicitly_wait(1)
        # self.restart()
        # self.get("https://www.google.com/")

        # options = Options()
        # options.add_argument(
        #     '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36')
        # options.add_argument('--lang=ja')
        # options.add_argument('--incognito')
        # options.add_argument("--start-maximized")
        # options.add_argument("--start-minimized")
        # options.add_argument("--kiosk-printing")  # 無条件で印刷ボタンを押すらしい
        # options.add_argument("start-fullscreen")
        # if hidechrome == True:
        #     options.add_argument('--headless')

        # self.driver = webdriver.Chrome(
        #     ChromeDriverManager().install(), chrome_options=options)
        # self.driverwait = WebDriverWait(self.driver, wait_time)
        # self.driver.minimize_window()
        # maxSize = self.driver.get_window_size()
        # maxPos = self.driver.get_window_position()
        # self.driver.set_window_size(maxSize['width'] * 3 / 4, maxSize['height'])
        # self.driver.set_window_position(maxPos['x'], maxPos['y'])

        # self.driver.set_window_size(0, 0)
        # self.driver.set_window_position(0, 0)
        # self.defaultPos = self.driver.get_window_position()
        # self.defaultSize = self.driver.get_window_size()

    def restart(self):
        if self.driver != None:
            self.finalize()
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=self.options)
        self.driverwait = WebDriverWait(self.driver, self.setting["WAIT_TIME_SEC"])
        self.driver.implicitly_wait(3)

    def create_new_tab(self):
        self.execute_script("window.open('');")
        self.switch_last_opened_tab()

    def __del__(self):
        self.finalize()

    def finalize(self):
        if getattr(self, "driver", None):
            handle_count = len(self.driver.window_handles)
            while handle_count > 0:
                self.driver.switch_to.window(self.driver.window_handles[0])
                self.driver.close()
                handle_count -= 1
            self.driver.quit()
            self.driver = None

    def back(self):
        self.driver.back()

    def quit(self):
        self.driver.quit()

    def get(self, url):
        self.driver.get(url)

    def wait_url_by_get(self, url):
        base_url = self.current_url
        self.driver.get(url)
        self.wait_for_url_change(base_url)

    def wait_for_url_change(self, url):
        try:
            self.driverwait.until(lambda driver: self.driver.current_url != url)
        except TimeoutException:
            print(f"Timeout: URL didn't change to {url}")

    def wait_url_changed(self, wait_sec, url=None, cancel_suburl=None, cancel_suburl2=None):
        if url == None:
            url = self.current_url
        duration = 0.1
        elapsed = 0.0
        while elapsed < wait_sec:
            if self.driver.current_url.startswith(url):
                return True
            if cancel_suburl != None and self.current_url.startswith(cancel_suburl):
                return False
            if cancel_suburl2 != None and self.current_url.startswith(cancel_suburl2):
                return False
            sleep(duration)
            elapsed += duration
        return False

    @property
    def current_url(self):
        return self.driver.current_url

    @property
    def title(self):
        return self.driver.title

    @property
    def page_source(self):
        return self.driver.page_source

    @property
    def window_handles(self):
        return self.driver.window_handles

    def switch_last_opened_tab(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def switch_next_tab(self):
        self.tab += 1
        wait_timesum = 0
        while True:
            sleep(self.duration)
            wait_timesum += self.duration
            if len(self.driver.window_handles) > self.tab:
                self.driver.switch_to.window(self.driver.window_handles[self.tab])
                break
            elif wait_timesum >= self.wait_time:
                raise TimeoutException("driverex.find_elements_by_name")

    def close_switch_prev_tab(self):
        if len(self.driver.window_handles) > self.tab:
            self.driver.close()
        self.tab -= 1
        self.driver.switch_to.window(self.driver.window_handles[self.tab])

    def reset_tabs(self):
        # タブを最初のタブのみにする
        if len(self.driver.window_handles) > 1:
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[0])  # 新しいタブをセット
            self.tab = 0
            sleep(1)

    def close_move_tab(self):
        self.driver.close()  # 現在タブを閉じる
        self.driver.switch_to.window(self.driver.window_handles[0])  # 新しいタブをセット
        self.tab = 0

    def save_current_html(self, path):
        html = self.driver.page_source
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    # ファイル保存できるがうまく表示できていない
    def save_current_mhtml(self, path):
        # ページをMHTML形式で保存
        mhtml = self.driver.execute_cdp_cmd("Page.captureSnapshot", {})
        sleep(3)
        with open(path, 'w') as f:
            f.write(mhtml["data"])

    def save_screenshot(self, path):
        self.driver.save_screenshot(path)

    def save_full_screenshot(self, path):
        width = self.driver.execute_script("return document.body.scrollWidth;")
        height = self.driver.execute_script("return document.body.scrollHeight;")
        viewport = {
            "x": 0,
            "y": 0,
            "width": width,
            "height": height,
            "scale": 1
        }
        # Chrome Devtools Protocolコマンドを実行し、取得できるBase64形式の画像データをデコードしてファイルに保存
        image_base64 = self.driver.execute_cdp_cmd(
            "Page.captureScreenshot", {"clip": viewport, "captureBeyondViewport": True})
        image = base64.b64decode(image_base64["data"])
        with open(path, 'bw') as f:
            f.write(image)

    def execute_cdp_cmd(self, cmd, args):
        return self.driver.execute_cdp_cmd(cmd, args)

    def execute_script(self, script):
        return self.driver.execute_script(script)

    def execute_script2(self, script, element):
        return self.driver.execute_script(script, element)

    def execute_script3(self, script, element, value):
        return self.driver.execute_script(script, element, value)

    def set_window_size(self, width, height):
        self.driver.set_window_size(width, height)

    def get_window_size(self):
        return self.driver.get_window_size()

    def set_default_window_size(self):
        self.driver.set_window_size(self.defaultSize['width'], self.defaultSize['height'])
        self.driver.set_window_position(self.defaultPos['x'], self.defaultPos['y'])

    def minimize_window(self):
        self.driver.minimize_window()

    def maximize_window(self):
        self.driver.maximize_window()

    def fullscreen_window(self):
        self.driver.fullscreen_window()  # あまりうまく使えず

    def get_cookies(self):
        return self.driver.get_cookies()

    def add_cookie(self, cookie):
        self.driver.add_cookie(cookie)

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def find_element(self, by, value, wait=False):
        try:
            if wait:
                return self.driverwait.until(EC.presence_of_element_located((by, value)))
            else:
                return self.driver.find_element(by=by, value=value)
        except Exception as e:
            return None

    def find_element_by_tag_name(self, value, wait=False):
        return self.find_element(By.TAG_NAME, value, wait)

    def find_element_by_name(self, value, wait=False):
        return self.find_element(By.NAME, value, wait)

    def find_element_by_id(self, value, wait=False):
        return self.find_element(By.ID, value, wait)

    def find_element_by_xpath(self, value, wait=False):
        return self.find_element(By.XPATH, value, wait)

    def find_element_by_class_name(self, value, wait=False):
        return self.find_element(By.CLASS_NAME, value, wait)

    def find_element_by_css_selector(self, value, wait=False):
        return self.find_element(By.CSS_SELECTOR, value, wait)

    def wait_url_by_click_find_element(self, by, value, wait=False):
        target_url = self.current_url
        element = self.find_element(by, value, wait)
        element.click()
        self.wait_for_url_change(target_url)

    def wait_url_by_click_find_element_by_tag_name(self, value, wait=False):
        self.wait_url_by_click_find_element(By.TAG_NAME, value, wait)

    def wait_url_by_click_find_element_by_name(self, value, wait=False):
        self.wait_url_by_click_find_element(By.NAME, value, wait)

    def wait_url_by_click_find_element_by_id(self, value, wait=False):
        self.wait_url_by_click_find_element(By.ID, value, wait)

    def wait_url_by_click_find_element_by_xpath(self, value, wait=False):
        self.wait_url_by_click_find_element(By.XPATH, value, wait)

    def wait_url_by_click_find_element_by_class_name(self, value, wait=False):
        self.wait_url_by_click_find_element(By.CLASS_NAME, value, wait)

    def wait_url_by_click_find_element_by_css_selector(self, value, wait=False):
        self.wait_url_by_click_find_element(By.CSS_SELECTOR, value, wait)

    def find_elements(self, by, value, wait=False):
        if wait:
            wait_timesum = 0
            while True:
                sleep(self.duration)
                wait_timesum += self.duration
                elements = self.driver.find_elements(by=by, value=value)
                if len(elements) > 0:
                    return elements
                elif wait_timesum >= self.wait_time:
                    raise TimeoutException(f"driverex.find_elements_by_{by}")
        else:
            return self.driver.find_elements(by=by, value=value)

    def find_elements_by_tag_name(self, value, wait=False):
        return self.find_elements(By.TAG_NAME, value, wait)

    def find_elements_by_name(self, value, wait=False):
        return self.find_elements(By.NAME, value, wait)

    def find_elements_by_id(self, value, wait=False):
        return self.find_elements(By.ID, value, wait)

    def find_elements_by_xpath(self, value, wait=False):
        return self.find_elements(By.XPATH, value, wait)

    def find_elements_by_class_name(self, value, wait=False):
        return self.find_elements(By.CLASS_NAME, value, wait)

    def find_elements_by_css_selector(self, value, wait=False):
        return self.find_elements(By.CSS_SELECTOR, value, wait)

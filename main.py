import sys
import random
import time
import platform
from datetime import datetime, timedelta
import pyautogui as ag
from DrissionPage import ChromiumPage
import last_checked_json
from pathlib import Path
import textlog as log
import openvpn as vpn
import func_chrome as fc
import func_crowdworks as fcw
import last_checked_json
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from web_driver_ex import WebDriverEx
from selenium.webdriver.common.by import By
from input_xlsx import get_input_json

# デバッグ用
DEBUG_MODE = False
DEBUG_LIST_COUNT = 3
DEBUG_PAGE_COUNT = 1
DEBUG_SKIP_AUTO_POST = False
MAX_CHECK_DAY_COUNT = 15

# システム定義
VERSION = "V.1.0.0"
NOT_FOUND_DELETE_DAYS = 7
VPN_SKIP = True

def main():

    # 定義
    BASE_DIR_PATH = Path(sys.argv[0]).parent
    log_base_dir_path = BASE_DIR_PATH / 'log'
    input_file_path = BASE_DIR_PATH / 'input.xlsx'
    

    # Logger初期化
    logger = log.textlog(log_base_dir_path, "croudworks")
    logger.info(f"--------------------------------------------------------------------------")
    logger.info(f"Main CrowdWorks Application Start ({VERSION})")

    # 設定値読込
    input = get_input_json(
        input_file_path,
        out=False,
        normalize_checkbox=True,
        exec_only=True,
    )
    openvpn = vpn.openvpn(logger, VPN_SKIP)
    settings = input["settings"]
    wait_time_sec, max_wait_time_sec = settings['WAIT_TIME_SEC'], settings['MAX_WAIT_TIME_SEC']
    logger.info(f"LoadSetting [wait_time_sec] {wait_time_sec} [max_wait_time_sec] {max_wait_time_sec}")

    # 定数定義
    now = datetime.now()
    today_str = f"{now.year}年{now.month}月{now.day}日"  # => 2021年1月23日

    # Chrome準備
    # 実行中Chrome終了＝＞デバッグChrome起動（ChromiumPage用）=>Chrome終了
    fc.kill_chrome()

    # メイン処理
    page, driver, actions = None, None, None
    try:
        # ブラウザ、VPN再起動
        try_driver_vpn_start_count = 0
        while try_driver_vpn_start_count < 10:
            try:
                try_driver_vpn_start_count += 1
                finish_page_and_driver(page, driver, logger)
                success = openvpn.restart()
                if success:
                    cw_login_url = fcw.get_crowdworks_login_url()
                    success, page, driver, actions = start_page_and_driver(cw_login_url, settings, logger)
                    if success:
                        logger.info(f'try_driver_vpn_start {try_driver_vpn_start_count} : success')
                        break
                    else:
                        logger.info(f'try_driver_vpn_start {try_driver_vpn_start_count} : start_page_and_driver failure')
                else:
                    logger.info(f'try_driver_vpn_start {try_driver_vpn_start_count} : openvpn.restart failure')
                sleep(5)
            except Exception as e:
                logger.info(f'try_driver_vpn_start {try_driver_vpn_start_count} Exception : {e}')

        # スクレイピング 開始
        logger.info(f'===== Start scraping =====')

        # ログイン
        try:
            el = driver.find_element_by_xpath("//input[contains(@name, 'username')]", True)
            el.send_keys(settings["CW_LOGIN_MAIL_ADDRESS"])
            sleep_random()

            el = driver.find_element_by_xpath("//input[contains(@name, 'password')]", True)
            el.send_keys(settings["CW_LOGIN_PASSWORD"])
            sleep_random()

            is_clicked = False
            els = driver.find_elements_by_xpath("//button[contains(@type, 'submit')]", True)
            for el in els:
                if el.text.strip() == "ログイン":
                    el.click()
                    is_clicked = True
                    break
            if not is_clicked:
                for el in els:
                    if "でログイン" not in el.text.strip():
                        el.click()
                        is_clicked = True
            sleep(3)
            logger.info(f'ログイン OK')
        except Exception as e:
            logger.error(f'[Exception] ログイン エラー : {e}')
            return

        logger.info(f'■■■■■■■■■■■■■■■■■■■■■■■■■■ 自動掲載処理 開始 ■■■■■■■■■■■■■■■■■■■■■■■■■■')
        total_count, success_count = 0, 0
        for auto_post in input["auto_posts"]:

            if DEBUG_SKIP_AUTO_POST:
                break

            total_count += 1
            logger.info(f'---------------------------------------------------------------------------------------')
            logger.info(f'処理開始 : {total_count}掲載目')
            
            # 「新しい仕事を依頼」ページ移動
            try:
                cw_job_offer_url = "https://crowdworks.jp/job_offers/new?ref=login_header"
                driver.wait_url_by_get(cw_job_offer_url)
                sleep(1)
                logger.info(f'「新しい仕事を依頼」ページ移動 OK')
            except Exception as e:
                logger.error(f'[Exception] 「新しい仕事を依頼」ページ移動 エラー : {e}')
                continue

            # 募集ページの作り方 youtube動画 ダイアログ が出たら閉じる
            try:
                el = driver.find_element_by_xpath("//div[contains(@id, 'satori__popup_close')]")
                if el is not None:
                    el.click()
                    sleep_random()
                    logger.info(f'募集ページの作り方ダイアログを閉じる OK')
            except Exception as e:
                pass
                # logger.info(f'募集ページの作り方ダイアログを閉じる NG')
                # logger.error(f'[Exception] 募集ページの作り方ダイアログを閉じる エラー : {e}')

            # すべてのカテゴリから選ぶ
            try:
                el = driver.find_element(By.ID, 'job_offer_form-category_tab_selection', True)
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                el2 = el.find_element(By.CLASS_NAME, "all_categories")
                el2.click()
                sleep_random()
                logger.info(f'すべてのカテゴリから選ぶ OK')
            except Exception as e:
                logger.info(f'すべてのカテゴリから選ぶ NG')
                logger.error(f'[Exception]すべてのカテゴリから選ぶ エラー : {e}')
                continue

            # カテゴリキーワード 入力
            try:
                category_keyword = auto_post["カテゴリ"]
                el = driver.find_element(By.ID, "category_keyword")
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                el.send_keys(category_keyword)
                sleep_random()
                el.send_keys(Keys.ARROW_DOWN)
                sleep_random()
                el.send_keys(Keys.ENTER)
                sleep_random()
                logger.info(f'カテゴリ 入力 OK : {category_keyword}')
            except Exception as e:
                logger.info(f'カテゴリ 入力 NG : {category_keyword}')
                logger.error(f'[Exception] カテゴリ 入力 エラー : {e}')
                continue

            # 依頼形式入力
            try:
                el = driver.find_element(By.ID, "job_offer_type_project")  # "プロジェクト形式"
                el.click()
                sleep_random()
                logger.info(f'依頼形式 入力 OK : プロジェクト形式')
            except Exception as e:
                logger.info(f'依頼形式 入力 NG : プロジェクト形式')
                logger.error(f'[Exception] 依頼形式 入力 エラー : {e}')
                continue

            # 依頼タイトル 入力
            try:
                jog_offer_title = auto_post["依頼タイトル"]
                el = driver.find_element(By.ID, "job_offer_title")
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                el.send_keys(jog_offer_title)
                sleep_random()
                logger.info(f'依頼タイトル 入力 OK : {jog_offer_title}')
            except Exception as e:
                logger.info(f'依頼タイトル 入力 NG : {jog_offer_title}')
                logger.error(f'[Exception] 依頼タイトル 入力 エラー : {e}')
                continue

            # 依頼詳細 入力
            try:
                job_offer_description = auto_post["依頼詳細"]
                el = driver.find_element(By.ID, "job_offer_description")
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                CTRL = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL
                el.send_keys(CTRL, "a")
                sleep_random()
                el.send_keys(Keys.DELETE)
                sleep_random()
                el.send_keys(job_offer_description)
                sleep_random()
                logger.info(f'依頼詳細 入力 OK : {job_offer_description}')
            except Exception as e:
                logger.info(f'依頼詳細 入力 NG : {job_offer_description}')
                logger.error(f'[Exception] 依頼詳細 入力 エラー : {e}')
                continue

            #### この仕事の特徴 ####
            # スキル不要 選択
            try:
                check_flg = auto_post["スキル不要"]
                if check_flg:
                    el = driver.find_element(By.XPATH, f"//input[contains(@class, 'experience_not_required')]")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    logger.info(f'スキル不要 チェック OK')
            except Exception as e:
                logger.info(f'スキル不要 チェック NG')
                logger.error(f'[Exception] スキル不要 選択 エラー : {e}')
                continue

            # 専門スキル歓迎 選択
            try:
                check_flg = auto_post["専門スキル歓迎"]
                if check_flg:
                    el = driver.find_element(By.XPATH, f"//input[contains(@class, 'experience_required')]")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    logger.info(f'専門スキル歓迎 チェック OK')
            except Exception as e:
                logger.info(f'専門スキル歓迎 チェック NG')
                logger.error(f'[Exception] 専門スキル歓迎 選択 エラー : {e}')
                continue

            # 単発 選択
            try:
                check_flg = auto_post["単発"]
                if check_flg:
                    el = driver.find_element(By.XPATH, f"//input[contains(@class, 'one_off')]")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    logger.info(f'単発 チェック OK')
            except Exception as e:
                logger.info(f'単発 チェック NG')
                logger.error(f'[Exception] 単発 選択 エラー : {e}')
                continue

            # 継続あり 選択
            try:
                check_flg = auto_post["継続あり"]
                if check_flg:
                    el = driver.find_element(By.XPATH, f"//input[contains(@class, 'continuous_requested')]")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    logger.info(f'継続あり チェック OK')
            except Exception as e:
                logger.info(f'継続あり チェック NGNG')
                logger.error(f'[Exception] 継続あり 選択 エラー : {e}')
                continue

            # スキマ時間歓迎 選択
            try:
                check_flg = auto_post["スキマ時間歓迎"]
                if check_flg:
                    el = driver.find_element(By.XPATH, f"//input[contains(@class, 'spare_time')]")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    logger.info(f'スキマ時間歓迎 チェック OK')
            except Exception as e:
                logger.info(f'スキマ時間歓迎 チェック NG')
                logger.error(f'[Exception] スキマ時間歓迎 選択 エラー : {e}')
                continue

            #### この仕事の特徴 ここまで ####

            # 募集人数 入力
            try:
                hope_number = auto_post["募集人数"]
                if hope_number <= 1:
                    el = driver.find_element(By.ID, "project_contract_hope_number_one")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    logger.info(f'募集人数 入力 OK : {hope_number}')
                else:
                    el = driver.find_element(By.ID, "project_contract_hope_number_more_than_one")
                    scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                    sleep_random()
                    el.click()
                    sleep_random()
                    el = driver.find_element(By.ID, "project_contract_hope_number_field")
                    el.send_keys(hope_number)
                    sleep_random()
                    logger.info(f'募集人数 入力 OK 2 : {hope_number}')
            except Exception as e:
                logger.info(f'募集人数 入力 MG : {hope_number}')
                logger.error(f'[Exception] 募集人数 入力 エラー : {e}')
                continue

            # 1名あたりの契約金額（目安） 選択
            try:
                budget_value = 40000 # => "30000-50000" を選択
                select_element = driver.find_element(By.ID, f"budget")
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                select = Select(select_element)
                for option in select.options:
                    value = option.get_attribute("value")  # 例: "30000-50000"
                    if "-" in value:
                        low, high = value.split("-")
                        low = int(low)
                        high = int(high)
                        if low == 0 and high == 0:
                            continue
                        elif high == 0:  # "1000000-0" のような「以上」ケース
                            if budget_value >= low:
                                option.click()
                                sleep_random()
                                logger.info(f'{option.text} 選択')
                                break
                        elif low <= budget_value < high:
                            option.click()
                            sleep_random()
                            logger.info(f'{option.text} 選択')
                            break
                logger.info(f'1名あたりの契約金額（目安） 選択 OK')
            except Exception as e:
                logger.info(f'1名あたりの契約金額（目安） 選択 NG')
                logger.error(f'[Exception] 1名あたりの契約金額（目安） 選択 エラー : {e}')
                continue

            # 確認画面に進む
            try:
                el = driver.find_element(By.ID, f"showPreview")
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                el.click()
                sleep_random()
                logger.info(f'確認画面に進む OK')
            except Exception as e:
                logger.info(f'確認画面に進む NG')
                logger.error(f'[Exception] 確認画面に進む エラー : {e}')
                continue

            # この内容で登録する
            try:
                el = driver.find_element(By.NAME, f"commit")
                scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                sleep_random()
                if not DEBUG_MODE:
                    el.click()
                    logger.info(f'この内容で登録する OK')
                    success_count += 1
                else:
                    logger.info(f'この内容で登録する DEBUG Skip')
                sleep(3)
            except Exception as e:
                logger.info(f'この内容で登録する NG')
                logger.error(f'[Exception] この内容で登録する エラー : {e}')
                continue

        logger.info(f'自動掲載処理 ページループ終了')
        logger.info(f'')

        logger.info(f'■■■■■■■■■■■■■■■■■■■■■■■■■■ 自動返信処理 開始 ■■■■■■■■■■■■■■■■■■■■■■■■■■')
        # 最終確認メッセージ日時取得
        while True:
            try:
                cfg = Path("last_checked.json")
                data = last_checked_json.read_json(cfg, default={})
                fmt = "%Y年%m月%d日 %H:%M"
                if "last_checked_time" in data:
                    last_checked_text = data["last_checked_time"]
                    last_checked_dt = datetime.strptime(last_checked_text, fmt)
                    logger.info(f'前回最終確認メッセージ日時取得 OK : {last_checked_text}')
                else:
                    last_checked_dt = datetime.now() - timedelta(days=MAX_CHECK_DAY_COUNT)
                    last_checked_text = last_checked_dt.strftime("%Y年%m月%d日 %H:%M")
                    logger.info(f'最終確認メッセージ日時15日前作成 OK : {last_checked_text}')                
            except Exception as e:
                logger.error(f'[Exception] 最終確認メッセージ日時取得 エラー : {e}')
                break

            # メッセージ一覧ページ移動
            try:
                driver.wait_url_by_get("https://crowdworks.jp/messages?ref=login_header")
                sleep(1)
                logger.info(f'メッセージ一覧ページ移動 OK')
            except Exception as e:
                logger.error(f'[Exception] メッセージ一覧ページ移動 エラー : {e}')
                break

            is_finish = False
            is_error = False
            latest_msg_text = None
            check_count = 0
            reply_count = 0
            while not is_finish:

                # メッセージ日時一覧取得
                try:
                    sleep_random()
                    time_els = driver.find_elements(By.TAG_NAME, f"time")
                    sleep_random()
                    logger.info(f'メッセージ日時一覧取得 OK')
                except Exception as e:
                    logger.error(f'[Exception] メッセージ日時一覧取得 エラー : {e}')
                    break

                # 1ページ 最大20メッセージ
                for i in range(len(time_els)):

                    if i >= 20:
                        break

                    check_count += 1
                    logger.info(f'■■■■■■■ CHECK {check_count} ■■■■■■■■')

                    # メッセージ日時確認
                    try:
                        els = driver.find_elements(By.TAG_NAME, f"time")
                        el = els[i]
                        scroll_into_view_above(driver, el, base_offset=150, jitter=50)
                        sleep_random()
                        msg_date_text = el.text
                        msg_dt = datetime.strptime(msg_date_text, fmt)
                        if not latest_msg_text:
                            latest_msg_text = msg_date_text  # Parse成功したら最新を格納
                            logger.info(f'最新メッセージ日時として登録 : {msg_date_text} > {last_checked_text}')
                        if msg_dt <= last_checked_dt:
                            logger.info(f'メッセージ日時確認 OK : {msg_date_text} ≦ {last_checked_text} => 確認済メッセージ => 終了')
                            is_finish = True
                            break
                        logger.info(f'メッセージ日時確認 OK : {msg_date_text} > {last_checked_text} => 新規メッセージ')
                    except Exception as e:
                        logger.error(f'メッセージ日時確認 Error : {msg_date_text} : {e}')

                    # ワーカー情報取得
                    try:
                        img_el = el.find_element(By.XPATH, "preceding::img[1]")
                        count = 0
                        while count < 5:
                            if img_el.get_attribute("alt") == '送信者画像':
                                span_el = img_el.find_element(By.XPATH, "following::span[1]")
                                worker_name = span_el.text
                                logger.info(f'ワーカー情報取得 OK : {worker_name}')
                                break
                            img_el = img_el.find_element(By.XPATH, "preceding::img[1]")
                            count += 1
                    except Exception as e:
                        pass
                        # logger.error(f'ワーカー情報取得 Error : {e}')

                    # 個別メッセージURL取得
                    try:
                        a_el = el.find_element(By.XPATH, "following::a[1]")  # timeの“後ろにある最初の<a>”
                        msg_url = a_el.get_attribute("href")  # href="https://crowdworks.jp/messages/371240103" にアクセスすると "https://crowdworks.jp/proposals/371240103#scroll_to_message" にリダイレクト
                        logger.info(f'個別メッセージURL取得 OK : {msg_url}')
                    except Exception as e:
                        logger.error(f'個別メッセージURL取得 Error : {e}')
                        continue

                    # 個別メッセージURL移動
                    try:
                        driver.create_new_tab()
                        sleep_random()
                        driver.wait_url_by_get(msg_url)
                        sleep_random()
                        logger.info(f'個別メッセージURL移動 OK : {msg_url}')
                    except Exception as e:
                        logger.error(f'個別メッセージURL移動 Error : {msg_url} : {e}')
                        driver.reset_tabs()
                        continue
                    

                    # メッセージ数取得
                    try:
                        msgs_el = driver.find_element(By.ID, f"pack-message-thread")
                        msg_els = msgs_el.find_elements(By.XPATH, f"//div[contains(@class, 'intro-employer_talking')]/div")
                        msg_count = len(msg_els)
                        if len(msg_els) > 1:
                            logger.info(f'メッセージ数 {msg_count} のため、スキップします')
                            driver.reset_tabs()
                            continue
                        elif len(msg_els) < 1:
                            logger.info(f'メッセージ数 {msg_count} は想定外のため、スキップします')
                            driver.reset_tabs()
                            continue
                        logger.info(f'メッセージ数 {msg_count} のため、返信します')
                    except Exception as e:
                        logger.error(f'メッセージ数取得 Error : {e}')
                        driver.reset_tabs()
                        continue

                    # 返信メッセージ入力
                    try:
                        textarea_el = driver.find_element(By.ID, f"message_body")
                        scroll_into_view_above(driver, textarea_el, base_offset=150, jitter=50)
                        sleep_random()
                        textarea_el.send_keys(input["auto_reply_message"])
                        sleep_random()
                        logger.info(f'返信メッセージ入力 OK')
                    except Exception as e:
                        logger.error(f'返信メッセージ入力 Error : {e}')
                        driver.reset_tabs()
                        continue

                    # 返信メッセージ投稿
                    try:
                        button_els = textarea_el.find_elements(By.XPATH, "following::button")
                        is_posted = False
                        for button_el in button_els:
                            if "メッセージを投稿する" in button_el.text:
                                if not DEBUG_MODE:
                                    button_el.click()
                                    sleep(3)
                                    is_posted = True
                                    reply_count += 1
                                    logger.info(f'返信メッセージ投稿 OK')
                                    break
                                else:
                                    logger.info(f'返信メッセージ投稿 DEBUG Skip')
                                    is_posted = True
                                    break
                        if not is_posted:
                            logger.info(f'メッセージを投稿する ボタンが見つからないため、スキップします')
                        driver.reset_tabs()

                    except Exception as e:
                        logger.error(f'返信メッセージ投稿 Error : {e}')
                        driver.reset_tabs()

                # 終了
                if is_finish:
                    break

                # 次のページ移動
                try:
                    msgs_el = driver.find_element(By.ID, f"pack-messages-index-page-app")
                    a_els = msgs_el.find_elements(By.TAG_NAME, "a")
                    is_clicked = False
                    for a_el in reversed(a_els):
                        if "次のページ" in a_el.text:
                            scroll_into_view_above(driver, a_el, base_offset=150, jitter=50)
                            sleep_random()
                            a_el.click()
                            is_clicked = True
                            sleep_random()
                            logger.info(f'次のページ移動 クリック OK')
                            break
                    if not is_clicked:
                        logger.info(f'次のページ移動 ボタンなし => 終了')
                        is_finish = True
                except Exception as e:
                    logger.error(f'次のページ移動 Error => 終了 : {e}')
                    driver.reset_tabs()
                    is_finish = True
                    is_error = True


            # 前回メッセージ確認日時として保存
            if not is_error:
                data["last_checked_time"] = latest_msg_text
                last_checked_json.write_json(cfg, data)
                logger.info(f'前回メッセージ確認日時として保存 OK : {latest_msg_text}')
            else:
                logger.info(f'エラー発生により、前回メッセージ確認日時として保存しません : {latest_msg_text}')

            logger.info(f'メッセージ 確認数:{check_count} / 返信数:{reply_count}')
            break

        # ■■■■■■■■■■■■■■■■■■■■■■■■■■ 自動返信処理 終了 ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

    except Exception as e:
        logger.error(f'[Main Func Exception] Error : {e}')
    

    # ログアウト
    driver.wait_url_by_get("https://crowdworks.jp/dashboard")
    sleep_random()
    el = driver.find_element(By.XPATH, f"//img[contains(@alt, 'userIcon')]")
    el.click()
    sleep_random()
    els = driver.find_elements(By.XPATH, f"//a")
    is_clicked = False
    for el in els:
        if "ログアウト" in el.text:
            el.click()
            is_clicked = True
            logger.info(f'ログアウト OK')
            break
    if not is_clicked:
        logger.info(f'ログアウト NG')
    sleep(3)

    # アプリケーション終了
    logger.info('')  # ログ見やすく改行

    finish_page_and_driver(page, driver, logger)
    del openvpn

    logger.info("Application End")
    del logger


def sleep_random(a=0.3, b=0.7):
    time.sleep(random.uniform(a, b))

def scroll_into_view_above(driver, el, base_offset=140, jitter=40):
    """
    要素の少し上で停止。base_offset±jitter をランダムに引いて位置調整。
    """
    offset = int(base_offset + random.randint(-jitter, jitter))
    driver.execute_script3("""
        const el = arguments[0];
        const offset = arguments[1];

        // まずは画面内へ
        el.scrollIntoView({block: 'start', inline: 'nearest'});

        // 近いスクロール親を探す（モーダル/内部スクロール対応）
        function scrollParent(node){
            let p = node.parentElement;
            while (p && p !== document.body){
                const s = getComputedStyle(p);
                if (/(auto|scroll)/.test(s.overflowY) && p.scrollHeight > p.clientHeight) return p;
                p = p.parentElement;
            }
            return window;
        }

        const sp = scrollParent(el);
        if (sp === window){
            const rect = el.getBoundingClientRect();
            const y = rect.top + window.pageYOffset - offset;
            window.scrollTo({top: y, behavior: 'auto'});
        } else {
            // 内部スクロールの場合: 要素の相対位置を基準に
            const y = el.offsetTop - offset;
            sp.scrollTo({top: y, behavior: 'auto'});
        }
    """, el, offset)
    sleep(0.05)  # 安定化のため少し待つ


def isRecaptchaPage(page):
    if "recaptcha" in page.url:
        return True
    # if "Additional Verification Required" in page.html:
    #     return True
    # if "人間であることを確認します" in page.html:
    #     return True
    return False


def start_page_and_driver(init_url, setting_dic, logger):
    success = False
    # Chrome実行（Cloudflare Bot対策回避用）
    page = ChromiumPage()
    page.get(init_url)
    logger.info(f"ChromiumPage 起動")
    try_verify = 0
    if False and isRecaptchaPage(page):
        logger.info(f"recaptcha 確認開始")
        while try_verify < 50:
            if isRecaptchaPage(page):
                # 人間らしい動きで
                screen_width, screen_height = ag.size()
                target_x = (screen_width / 2) - 120 + random.randint(-5, 5)
                target_y = 280 + random.randint(-40, 40)
                # ag.moveTo(target_x + 10, target_y, duration=1)
                # ag.moveTo(target_x, target_y + 10, duration=1)
                ag.moveTo(target_x, target_y, duration=(random.randint(10, 20) / 10))
                ag.click()
                sleep(2)
                logger.info(f"recaptcha try{try_verify}")
            else:
                logger.info(f"recaptcha 成功")
                success = True
                break
            try_verify += 1

        logger.info(f"recaptcha 確認終了")
        sleep(1)
    else:
        success = True

    if not success:
        return success, page, None, None

    # インスタンスを作成
    driver = WebDriverEx(setting_dic, logger)
    actions = ActionChains(driver.driver)
    logger.info(f"WebDriverEx 起動")

    # ページアクセス
    driver.get(init_url)
    sleep(3)
    return success, page, driver, actions


def finish_page_and_driver(page, driver, logger):
    if driver is not None:
        try:
            driver.finalize()
            driver = None
            logger.info(f'driver終了')
        except Exception as e:
            logger.error(f'[DriverFinishException] Error : {e}')
    if page is not None:
        try:
            page.quit()
            logger.info(f'DrissionPage終了')
        except Exception as e:
            logger.error(f'[DrissionPageFinishException] Error : {e}')


if __name__ == "__main__":
    main()

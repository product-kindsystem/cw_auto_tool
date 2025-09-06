import logging
import datetime
import os
from operator import itemgetter

# https://www.sejuku.net/blog/23149
# LogLevel
# 名前	    設定値	役割
# NOTSET	    0	設定値などの記録（全ての記録）
# DEBUG	    10	動作確認などデバッグの記録
# INFO	    20	正常動作の記録
# WARNING	30	ログの定義名
# ERROR	    40	エラーなど重大な問題
# CRITICAL	50	停止など致命的な問題


class textlog:
    def __init__(self, log_base_dir_path, file_name_suffix):

        self.dirpath = log_base_dir_path

        # ログの出力名を設定
        logger = logging.getLogger('general.logger')

        # ログレベルの設定
        logger.setLevel(10)

        # ログのコンソール出力の設定
        sh = logging.StreamHandler()
        logger.addHandler(sh)

        # ログのファイル出力先を設定
        now = datetime.datetime.now()
        self.date_str = now.strftime('%Y-%m-%d')  # => 2021-01-23

        if os.path.exists(log_base_dir_path) == False:
            os.mkdir(log_base_dir_path)
        self.log_dir_path = log_base_dir_path / self.date_str
        if os.path.exists(self.log_dir_path) == False:
            os.mkdir(self.log_dir_path)

        log_file_name = f'{self.date_str}_{file_name_suffix}.log'
        filepath = self.log_dir_path / log_file_name

        fh = logging.FileHandler(filename=filepath, encoding='utf-8')
        logger.addHandler(fh)

        # ログの出力形式の設定
        formatter = logging.Formatter('%(asctime)s : [%(levelname)s] : %(message)s')
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)
        self.logger = logger

    def __del__(self):
        return

    def get_log_dir_path(self):
        return self.log_dir_path

    def is_need_refresh(self):
        now = datetime.datetime.now()
        cur_date_str = now.strftime('%Y-%m-%d')  # => 2021-01-23
        return self.date_str != cur_date_str

    def browser_log(self, file, driver, text):
        self.info(f'[{os.path.basename(file)}] {text}  ({driver.current_url})')

    def browser_error_log(self, file, driver, text):
        self.error(f'[{os.path.basename(file)}] {text}  ({driver.current_url})')

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

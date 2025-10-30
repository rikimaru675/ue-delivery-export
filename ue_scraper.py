from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import platform
import time
import re
import csv
import utils


class UeScraper:
    """UberEats配達員の売上データを自動取得するスクレイパー。"""

    TOPPAGE_URL = 'https://www.uber.com/global/ja/sign-in/'
    CSV_FIELD_NAMES = [
        '配達日', '配達件数', '配達時刻', '乗車時間', '乗車距離',
        '見積料金', '調整金', 'チップ', '売り上げ',
        'ピック場所', 'ドロップ場所', '詳細表示URL',
    ]
    TIMEOUTS_SEC = {
        'wait'          : 30,
        'password'      : 3,
        'menu'          : 3,
        'read_more'     : 3,
    }
    SLEEP_TIMES_SEC = {
        'read_more'     : 3,
        'detail_page'   : 5,
    }
    SMS_CODE_LEN = 4
    MOBILE_WIDTH_THRESHOLD = 1136

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = self._create_driver()

    # --------------------------------------------------
    # Driver設定
    # --------------------------------------------------
    def _create_driver(self):
        options = Options()
        # 起動時に最大化
        options.add_argument("--start-maximized")
        # Chromeは自動テスト ソフトウェア~~　を非表示
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 自動化ツールとしての検出を避ける設定
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)
        # webdriver検知を回避するスクリプト
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        })
        return driver

    def quit(self):
        if self.driver:
            self.driver.quit()

    # --------------------------------------------------
    # サインイン処理
    # --------------------------------------------------
    def sign_in(self):
        self._open_toppage()
        self._click_sign_in()
        self._input_email()
        self._verify_sms_code()
        self._verify_password()

    def _open_toppage(self):
        self.driver.get(self.TOPPAGE_URL)
        WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
        )

    def _click_sign_in(self):
        sign_in = WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'サインイン'))
        )
        sign_in.click()
        WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
        )

    def _input_email(self):
        email_box = self.driver.find_element(By.ID, 'PHONE_NUMBER_or_EMAIL_ADDRESS')
        email_box.send_keys(self.email)
        self.driver.find_element(By.ID, 'forward-button').click()
        WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
        )

    def _verify_sms_code(self):
        sms_code = self._get_sms_code()
        for i, num in enumerate(sms_code):
            field = self.driver.find_element(By.ID, f'PHONE_SMS_OTP-{i}')
            field.send_keys(num)
        WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
        )

    def _get_sms_code(self):
        while True:
            sms_code = input(f'Uberから通知された{self.SMS_CODE_LEN}桁の数字を半角で入力してください：')
            if re.fullmatch(rf"\d{{{self.SMS_CODE_LEN}}}", sms_code):
                return sms_code

    def _verify_password(self):
        try:
            # パスワードの入力フォームがあればパスワードを入力する
            password_field = WebDriverWait(self.driver, self.TIMEOUTS_SEC['password']).until(
                EC.presence_of_element_located((By.ID, 'PASSWORD'))
            )
            password_field.send_keys(self.password)
            self.driver.find_element(By.ID, 'forward-button').click()
            WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            # パスワードの入力が求められていないため何もしない
            pass

    # --------------------------------------------------
    # 売上ページへの遷移
    # --------------------------------------------------
    def navigate_to_driver_dashboard(self):
        """ユーザメニュー → 運転と配達 画面へ遷移"""
        self._open_user_menu()
        self._click_drive_and_delivery()

    def _open_user_menu(self):
        selector = (
            'div[data-testid="responsive-mobile-nav"] button[aria-label="loggedIn drawer"]'
            if self._is_mobile_view()
            else 'div[data-testid="responsive-desktop-nav"] button[aria-label="loggedIn drawer"]'
        )
        try:
            menu_button = WebDriverWait(self.driver, self.TIMEOUTS_SEC['menu']).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            menu_button.click()
        except TimeoutException:
            input('手動でユーザメニューを開いてください >')

    def _click_drive_and_delivery(self):
        elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            'div[data-baseweb="popover"] a[aria-label="運転と配達"][href="https://drivers.uber.com/"]'
        )
        if elements:
            elements[0].click()
            WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
            )
        else:
            input('手動で「運転と配達」をクリックしてください >')

    def _is_mobile_view(self):
        return self.driver.execute_script("return window.innerWidth;") < self.MOBILE_WIDTH_THRESHOLD

    # --------------------------------------------------
    # 売上データ取得
    # --------------------------------------------------
    def get_weekly_results(self):
        input('ブラウザで「週で検索」をクリックして週を選んでください >')
        self._read_all_results()
        return self._parse_results()

    def _read_all_results(self):
        """「さらに読み込む」ボタンを繰り返しクリック"""
        while True:
            try:
                read_more = WebDriverWait(self.driver, self.TIMEOUTS_SEC['read_more']).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="さらに読み込む"]'))
                )
                read_more.click()
                time.sleep(self.SLEEP_TIMES_SEC['read_more'])
            except TimeoutException:
                break

    def _parse_results(self):
        """売上一覧を解析し、詳細データを辞書リストで返す"""
        results = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, 'table._css-jkqalI tbody tr')

        # 売上日時が古いものから順に取得する
        for row in reversed(rows):
            event = row.find_element(By.CSS_SELECTOR, 'td:nth-child(1) p').text.strip()
            if event != 'Delivery':
                continue

            detail_url = row.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute('href')
            result = self._parse_detail_page(detail_url)
            results.append(result)

        return results

    def _parse_detail_page(self, url):
        """詳細ページを新しいタブで開いてデータ抽出"""
        driver = self.driver
        actions = ActionChains(driver)
        shortcut = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL

        link = driver.find_element(By.CSS_SELECTOR, f'a[href="{url}"]')
        actions.key_down(shortcut).click(link).key_up(shortcut).perform()

        WebDriverWait(driver, self.TIMEOUTS_SEC['wait']).until(
            EC.number_of_windows_to_be(2)
        )
        driver.switch_to.window(driver.window_handles[1])
        WebDriverWait(self.driver, self.TIMEOUTS_SEC['wait']).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'body'))
        )

        # ロボットと認識されないために、詳細ページを一定時間表示させる
        time.sleep(self.SLEEP_TIMES_SEC['detail_page'])

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = self._extract_detail_data(soup, url)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return data

    def _extract_detail_data(self, soup, url):
        """詳細ページのHTMLを解析"""
        data = {'詳細表示URL': url}

        # 日時
        data['配達日'] = ''
        data['配達時刻'] = ''
        element = soup.find('p', string=re.compile(r'Delivery\s+•'))
        if element:
            text = element.text.strip()
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*•\s*(\d{1,2}:\d{2})', text)
            if date_match:
                yyyy, mm, dd, time_part = date_match.groups()
                data['配達日'] = f"{int(yyyy):04d}/{int(mm):02d}/{int(dd):02d}"
                data['配達時刻'] = time_part

        # 売上金額
        data['売り上げ'] = 0
        element = soup.find('h2', string=re.compile(r'￥'))
        if element:
            text = element.text.strip()
            data['売り上げ'] = int(re.sub(r'[￥,]', '', text))

        # 見積金額
        data['見積料金'] = 0
        element = soup.find(string=re.compile(r'このサービスの見積もり料金は'))
        if element:
            text = element.text.strip()
            text = re.search(r'￥[\d,]+', text).group()
            data['見積料金'] = int(re.sub(r'[￥,]', '', text))

        # 乗車時間
        data['乗車時間'] = '0:00:00'
        element = soup.find(string=re.compile(r'\d+\s*分\s*\d+\s*秒'))
        if element:
            text = element.text.strip()
            data['乗車時間'] = utils.convert_to_hmmss(text)

        # 乗車距離
        data['乗車距離'] = 0.0
        element = soup.find(string=re.compile(r'\d+\.\d+\s*km'))
        if element:
            text = element.text.strip()
            data['乗車距離'] = float(text.replace('km', ''))

        # aria-label属性をすべて抽出
        aria_labels = soup.find_all(attrs={"aria-label": True})

        # ピック場所
        data['ピック場所'] = ''
        if len(aria_labels) > 0:
            data['ピック場所'] = aria_labels[0]['aria-label']

        # ドロップ場所
        data['ドロップ場所'] = ''
        if len(aria_labels) > 1:
            data['ドロップ場所'] = aria_labels[1]['aria-label']

        # 件数
        data['配達件数'] = 0
        if len(aria_labels) > 2:
            match = re.search(r'\d+\s+ポイント', aria_labels[2]['aria-label'])
            if match:
                text = re.search(r'\d+', match.group()).group()
                data['配達件数'] = int(text)

        # チップ
        data['チップ'] = 0
        if len(aria_labels) > 3:
            match = re.search(r'￥([\d,]+) のチップを含む', aria_labels[3]['aria-label'])
            if match:
                text = match.group(1).replace(',', '')
                data['チップ'] = int(text)

        # 調整金（マイナス値も許容する）
        data['調整金'] = data['売り上げ'] - data['見積料金'] - data['チップ']

        return data

    # --------------------------------------------------
    # CSV出力
    # --------------------------------------------------
    def save_results(self, results):
        with open('output.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_FIELD_NAMES)
            writer.writeheader()
            writer.writerows(results)

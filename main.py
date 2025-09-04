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
from datetime import datetime
import csv
import config

TOPPAGE_URL = 'https://www.uber.com/global/ja/sign-in/'
SMS_CODE_LEN = 4
WAIT_TIMEOUT_SEC = 30
PASSWORD_TIMEOUT_SEC = 3
SLEEP_TIME_SEC = 3
field_names = [
    'delivery_date',
    'delivery_count',
    'delivery_time',
    'ride_time',
    'ride_distance',
    'estimated_amount',
    'adjustment_amount',
    'tip_amount',
    'sales_amount',
    'pick_location',
    'drop_location',
    'detail_url',
]

# デバッグ用にステップ実行
def debug_wait():
    # is_debug = True
    is_debug = False
    if is_debug:    input('debug > ')

# ウィンドウ幅でモバイルか否かを判定する
def is_mobile_view(driver):
    size = 768  # 必要に応じて調整
    width = driver.execute_script("return window.innerWidth;")
    return width <= size

# 英語日付表記(3rd April 2025)をYYYYMMDD表記(2025/04/03)に変換する
def english_date_to_yyyymmdd(english_date_str):
    # th, st, nd, rd を除去
    cleaned_date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', english_date_str)

    # datetime に変換
    dt = datetime.strptime(cleaned_date_str, '%A, %B %d, %Y')

    # YYYY/MM/DDの形式に変換
    return dt.strftime('%Y/%m/%d')

# YYYY/MM/DD表記を英語日付表記に変換する
def yyyymmdd_to_english_date(date_str):
    # datetime オブジェクトに変換
    dt = datetime.strptime(date_str, '%Y/%m/%d')

    # 英語表記の文字列に変換
    month = dt.strftime('%B')
    day = dt.day
    year = dt.year

    return f'{month} {day}, {year}'

# h時間m分s秒表記からh:mm:ss表記に変換する
def convert_to_hmmss(time_str):
    # 正規表現で時間・分・秒を抽出（それぞれ無くてもOK）
    match = re.match(r'\s*(?:(\d+)\s*時間)?\s*(?:(\d+)\s*分)?\s*(?:(\d+)\s*秒)?', time_str)
    if match:
        hours   = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
    else:
        hours   = 0
        minutes = 0
        seconds = 0

    # h:mm:ss形式に整形
    return f"{hours}:{minutes:02d}:{seconds:02d}"

# データをCSVファイルに出力する
def output_to_csv(field, row_data):
    with open('output.csv', 'w', newline='', encoding='utf-8-sig') as f:    # Excelで使用するため文字エンコードは「UTF-8 with BOM」とする
        writer = csv.DictWriter(f, fieldnames=field)
        writer.writeheader()
        writer.writerows(row_data)



options = Options()
# シークレットモード
# options.add_argument('--incognito')
# 起動時に最大化
options.add_argument("--start-maximized")
# Chromeは自動テスト ソフトウェア~~　を非表示
options.add_experimental_option('excludeSwitches', ['enable-automation'])
# 自動化ツールとしての検出を避ける設定
options.add_experimental_option('useAutomationExtension', False)

# WebDriver起動
driver = webdriver.Chrome(options=options)
debug_wait()
# webdriver検知を回避するスクリプト注入
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    '''
})

# 結果格納用
delivery_results = []

try:
    # トップ画面
    driver.get(TOPPAGE_URL)
    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    debug_wait()

    # サインインをクリック
    sign_in = driver.find_element(By.LINK_TEXT, 'サインイン')
    sign_in.click()
    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    debug_wait()

    # 電話番号またはメールアドレス入力画面
    # メールアドレスを入力
    email = driver.find_element(By.ID, 'PHONE_NUMBER_or_EMAIL_ADDRESS')
    email.send_keys(config.EMAIL_ADDRESS)

    debug_wait()

    # 続行ボタンをクリック
    button = driver.find_element(By.ID, 'forward-button')
    button.click()
    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    debug_wait()

    # SMSコード入力画面
    while True:
        sms_code = input('Uberから通知された4桁の数字を【半角】で入力してください：')
        sms_code = sms_code.lower()
        if (len(sms_code) == SMS_CODE_LEN) and (sms_code.isdigit()):
            break

    debug_wait()

    codes = list(sms_code)
    code0 = driver.find_element(By.ID, 'PHONE_SMS_OTP-0')
    code0.send_keys(codes[0])
    code1 = driver.find_element(By.ID, 'PHONE_SMS_OTP-1')
    code1.send_keys(codes[1])
    code2 = driver.find_element(By.ID, 'PHONE_SMS_OTP-2')
    code2.send_keys(codes[2])
    code3 = driver.find_element(By.ID, 'PHONE_SMS_OTP-3')
    code3.send_keys(codes[3])

    # コードを入力すると自動的に次のページへ遷移する
    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    debug_wait()

    ##### パスワード入力画面
    try:
        # パスワードの入力フォームがあればパスワードを入力する
        password = WebDriverWait(driver, PASSWORD_TIMEOUT_SEC).until(EC.presence_of_element_located((By.ID, 'PASSWORD')))
        password.send_keys(config.PASSWORD)

        debug_wait()

        button = driver.find_element(By.ID, 'forward-button')
        button.click()

        WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

        debug_wait()
    except TimeoutException:
        # パスワードの入力が求められていないため何もしない
        pass

    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    ##### 稼働と乗車画面 #####
    if is_mobile_view(driver):
        selector = 'div[data-testid="responsive-mobile-nav"] button[data-tracking-alias="loggedin drawer activated"]'
    else:
        selector = 'div[data-testid="responsive-desktop-nav"] button[data-tracking-alias="loggedin drawer activated"]'

    # ユーザメニューを表示
    user_menu = driver.find_elements(By.CSS_SELECTOR, selector)
    if user_menu:
        user_menu[0].click()
        WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)
    else:
        input('手動でユーザメニューを表示させてください >')

    debug_wait()

    # 運転と配達をクリック
    drive_delivery = driver.find_elements(By.CSS_SELECTOR, 'div[data-baseweb="popover"] a[aria-label="運転と配達"][href="https://drivers.uber.com/"]')
    if drive_delivery:
        drive_delivery[0].click()
    else:
        input('手動で【運転と配達】をクリックしてください >')

    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    debug_wait()

    ##### Uberでの売上画面 #####

    input('ブラウザ上で【週で検索】をクリックして取得するデータの週を選択してください >')
    WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)

    # 売上結果をすべて読み込む
    while len(driver.find_elements(By.CSS_SELECTOR, 'button[data-baseweb="button"]._css-ATGrN')) > 0:
        # 【さらに読み込む】ボタンをクリック
        read_more = driver.find_element(By.CSS_SELECTOR, 'button[data-baseweb="button"]._css-ATGrN')
        read_more.click()
        WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)
        time.sleep(SLEEP_TIME_SEC)
        debug_wait()

    # 売上の行をすべて取得する
    rows = driver.find_elements(By.CSS_SELECTOR, 'table._css-jkqalI tbody tr')
    for row in reversed(rows):  # リストは日時が新しいものから並んでおり、古いものから順に取得するためにreversed()を使用
        # イベント名
        event_name = row.find_element(By.CSS_SELECTOR, 'td:nth-child(1) p').text.strip()
        debug_wait()

        # イベント名が【Delivery】以外は除外する
        if (event_name != 'Delivery'):
            continue

        # 日時（date + time）
        date_text = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) p:nth-child(1)').text.strip()
        time_text = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) p:nth-child(2)').text.strip()
        debug_wait()

        # 売り上げ（通貨付き文字列）
        earnings = row.find_element(By.CSS_SELECTOR, 'td:nth-child(3) p').text.strip()
        debug_wait()

        # 詳細ページのリンク
        link_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a')
        detail_url = link_element.get_attribute('href')
        debug_wait()

        # 詳細ページを新しいタブで開く
        if (link_element.get_attribute('target') == '_blank'):
            link_element.click()
        else:
            if platform.system() == 'Darwin':
                # macOSの場合
                shortcut_key = Keys.COMMAND
            else:
                # それ以外の場合 (Windows, Linux)
                shortcut_key = Keys.CONTROL
            actions = ActionChains(driver)
            actions.key_down(shortcut_key).click(link_element).key_up(shortcut_key).perform()

        # 詳細ページのタブが開くまで待機
        WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.number_of_windows_to_be(2))
        WebDriverWait(driver, WAIT_TIMEOUT_SEC).until(EC.presence_of_all_elements_located)
        debug_wait()

        # 詳細ページタブに切り替える
        handles = driver.window_handles
        driver.switch_to.window(handles[1])

        # 詳細ページを一定時間表示させる
        time.sleep(SLEEP_TIME_SEC)
        debug_wait()

        # 詳細ページのHTML取得
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        debug_wait()
        detail_result = {}

        # 日時
        element = soup.find('p', string=re.compile(r'Delivery\s+•'))
        if element:
            text = element.text.strip()
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*•\s*(\d{1,2}:\d{2})', text)
            if date_match:
                yyyy, mm, dd, time_part = date_match.groups()
                delivery_date = f"{int(yyyy):04d}/{int(mm):02d}/{int(dd):02d}"
                delivery_time = time_part
            else:
                delivery_date = ''
                delivery_time = ''
        else:
            delivery_date = ''
            delivery_time = ''

        debug_wait()

        # 売上金額
        element = soup.find('h2', string=re.compile(r'￥'))
        if element:
            text = element.text.strip()
            sales_amount = int(re.sub(r'[￥,]', '', text))
        else:
            sales_amount = 0

        debug_wait()

        # 見積金額
        element = soup.find(string=re.compile(r'このサービスの見積もり料金は'))
        if element:
            text = element.text.strip()
            text = re.search(r'￥[\d,]+', text).group()
            estimated_amount = int(re.sub(r'[￥,]', '', text))
        else:
            estimated_amount = 0

        debug_wait()

        # 乗車時間
        element = soup.find(string=re.compile(r'\d+\s*分\s*\d+\s*秒'))
        if element:
            text = element.text.strip()
            ride_time = convert_to_hmmss(text)
        else:
            ride_time = '0:00:00'

        debug_wait()

        # 乗車距離
        element = soup.find(string=re.compile(r'\d+\.\d+\s*km'))
        if element:
            text = element.text.strip()
            ride_distance = float(text.replace('km', ''))
        else:
            ride_distance = 0.0

        debug_wait()

        # aria-label属性をすべて抽出
        aria_labels = soup.find_all(attrs={"aria-label": True})

        debug_wait()

        # ピック場所
        pick_location = ''
        if len(aria_labels) > 0:
            pick_location = aria_labels[0]['aria-label']

        debug_wait()

        # ドロップ場所
        drop_location = ''
        if len(aria_labels) > 1:
            drop_location = aria_labels[1]['aria-label']

        debug_wait()

        # 件数
        delivery_count = 0
        if len(aria_labels) > 2:
            match = re.search(r'\d+\s+ポイント', aria_labels[2]['aria-label'])
            if match:
                text = re.search(r'\d+', match.group()).group()
                delivery_count = int(text)

        debug_wait()

        # チップ
        tip_amount = 0
        if len(aria_labels) > 3:
            match = re.search(r'￥([\d,]+) のチップを含む', aria_labels[3]['aria-label'])
            if match:
                text = match.group(1).replace(',', '')
                tip_amount = int(text)

        debug_wait()

        # 調整金（マイナス値も許容する）
        adjustment_amount = sales_amount - estimated_amount - tip_amount

        debug_wait()

        # 取得データを格納
        detail_result['delivery_date'] = delivery_date
        detail_result['delivery_count'] = delivery_count
        detail_result['delivery_time'] = delivery_time
        detail_result['ride_time'] = ride_time
        detail_result['ride_distance'] = ride_distance
        detail_result['estimated_amount'] = estimated_amount
        detail_result['adjustment_amount'] = adjustment_amount
        detail_result['tip_amount'] = tip_amount
        detail_result['sales_amount'] = sales_amount
        detail_result['pick_location'] = pick_location
        detail_result['drop_location'] = drop_location
        detail_result['detail_url'] = detail_url
        delivery_results.append(detail_result)

        # 詳細ページのタブを閉じる
        driver.close()

        debug_wait()

        # 元のタブに戻る
        driver.switch_to.window(handles[0])

        debug_wait()

    # ファイル出力
    output_to_csv(field_names, delivery_results)

    debug_wait()

    # サインアウト
    # メニューボタンをクリック
    # menu_button = driver.find_element(By.XPATH, '//*[@id="wrapper"]/div[1]/div[1]/div/button')
    # menu_button.click()

    debug_wait()

    # TODO サインアウトメニューを表示できるように要対応
    # user_button = driver.find_element(By.XPATH, '//*[@id="bui8val-0"]')
    # user_button.click()

    debug_wait()

    # logout_button = driver.find_element(By.XPATH, '//*[@id="bui8val-5"]')
    # logout_button.click()

except Exception as e:
    print(e)
finally:
    driver.quit()




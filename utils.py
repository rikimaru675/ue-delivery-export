from datetime import datetime
import re


def debug_wait():
    """デバッグ用にステップ実行"""
    # is_debug = True
    is_debug = False
    if is_debug:    input('debug > ')

def english_date_to_yyyymmdd(english_date: str) -> str:
    """英語日付表記(3rd April 2025)をYYYYMMDD表記(2025/04/03)に変換する"""
    # th, st, nd, rd を除去
    cleaned_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', english_date)

    # datetime に変換
    dt = datetime.strptime(cleaned_date, '%A, %B %d, %Y')

    # YYYY/MM/DDの形式に変換
    return dt.strftime('%Y/%m/%d')

def yyyymmdd_to_english_date(date: str) -> str:
    """YYYY/MM/DD表記を英語日付表記に変換する"""
    # datetime オブジェクトに変換
    dt = datetime.strptime(date, '%Y/%m/%d')

    # 英語表記の文字列に変換
    month = dt.strftime('%B')
    day = dt.day
    year = dt.year

    return f'{month} {day}, {year}'

def convert_to_hmmss(time: str) -> str:
    """h時間m分s秒表記からh:mm:ss表記に変換する"""
    hours   = 0
    minutes = 0
    seconds = 0

    # 正規表現で時間・分・秒を抽出（それぞれ無くてもOK）
    match = re.match(r'\s*(?:(\d+)\s*時間)?\s*(?:(\d+)\s*分)?\s*(?:(\d+)\s*秒)?', time)
    if match:
        hours   = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0

    # h:mm:ss形式に整形
    return f"{hours}:{minutes:02d}:{seconds:02d}"

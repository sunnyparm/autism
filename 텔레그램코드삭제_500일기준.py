import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import re
import sqlite3
import urllib3
import ssl
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter
try:
    import chardet  # optional
except Exception:
    chardet = None

DB_PATH = 'autismnews.db'
DAYS_WINDOW = 500  # 최근 500일
HEADER_TITLE = '한국자폐인사랑협회 기사'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sent_news (
                title TEXT,
                date TEXT,
                PRIMARY KEY (title, date)
            )
        """)
        conn.commit()

def is_already_sent(title, date):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sent_news WHERE title = ? AND date = ?", (title, date))
        return cur.fetchone() is not None

def save_sent(title, date):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO sent_news (title, date) VALUES (?, ?)", (title, date))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

# ==============================
# 수집 대상 URL (카테고리별)
# ==============================
urls = [
    ('https://www.autismkorea.kr/bbs/board.php?tbl=bbs31', '공지사항'),
    ('https://www.autismkorea.kr/bbs/board.php?tbl=bbs36', '뉴스레터'),
    ('https://www.autismkorea.kr/bbs/board.php?tbl=bbs32', '언론보도'),
    ('https://www.autismkorea.kr/bbs/board.php?tbl=bbs34', '외부기관 소식')
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        except ssl.SSLError:
            ctx.set_ciphers('ALL:!aNULL:!eNULL')
        self.poolmanager = PoolManager(*args, ssl_context=ctx, **kwargs)

def create_session_with_ssl_fallback():
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        return session
    except Exception:
        session = requests.Session()
        session.verify = False
        return session

session = create_session_with_ssl_fallback()
five_days_ago = datetime.now() - timedelta(days=DAYS_WINDOW)

init_db()
categorized_articles = {}

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        print(f"요청 시도 {attempt + 1}/{max_retries}: {url}")
        try:
            res = session.get(url, headers=headers, timeout=15, verify=False)
            print(f"상태 코드: {res.status_code}, 응답 길이: {len(res.content)}")
            return res
        except Exception as e:
            print(f"요청 실패 ({attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("재시도 중...")
            else:
                print("모든 시도 실패.")
                return None
    return None

for url, category in urls:
    print(f"\n=== {category} 수집 중 ===")
    res = make_request_with_retry(url)
    if res is None:
        continue

    if category not in categorized_articles:
        categorized_articles[category] = []

    raw = res.content
    enc_candidates = []
    try:
        head_snippet = raw[:4096].decode('ascii', errors='ignore')
        m = re.search(r'charset=([\w\-]+)', head_snippet, re.IGNORECASE)
        if m:
            enc_candidates.append(m.group(1).lower())
    except Exception:
        pass
    if res.encoding:
        enc_candidates.append(res.encoding.lower())
    if chardet is not None:
        try:
            detected = chardet.detect(raw).get('encoding')
            if detected:
                enc_candidates.append(detected.lower())
        except Exception:
            pass
    enc_candidates += ['utf-8', 'cp949', 'euc-kr']
    selected = None
    for enc in enc_candidates:
        try:
            trial = raw.decode(enc, errors='replace')
            if re.search(r'[\uac00-\ud7a3]', trial):
                selected = enc
                html = trial
                break
        except Exception:
            continue
    if selected is None:
        html = raw.decode('utf-8', errors='replace')
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table', class_='basic_board_list')
    if not table:
        items = soup.select('ul.horizontal_board li')
        if not items:
            print("목록을 찾지 못했습니다.")
            continue
        for li in items:
            a_tag = li.select_one('div.txt_box h4 a') or li.select_one('h4 a')
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get('href')
            full_url = urljoin(url, link)

            # 날짜 추출
            em = li.select_one('em')
            date_text = em.get_text(" ", strip=True) if em else li.get_text(" ", strip=True)
            m = re.search(r'(20\d{2}-\d{2}-\d{2})', date_text)
            if m:
                date_key = m.group(1)
                y, mo, d = map(int, date_key.split('-'))
                date_obj = datetime(y, mo, d)
            else:
                m2 = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', date_text)
                if not m2:
                    continue
                y = int('20' + m2.group(1))
                mo = int(m2.group(2))
                d = int(m2.group(3))
                date_obj = datetime(y, mo, d)
                date_key = date_obj.strftime('%Y-%m-%d')

            if date_obj >= five_days_ago:
                if not is_already_sent(title, date_key):
                    article_info = {'title': title, 'date': date_key, 'url': full_url}
                    categorized_articles[category].append(article_info)
                    save_sent(title, date_key)
        continue

    rows = table.find_all('tr')
    for row in rows:
        td_left = row.find('td', class_='left')
        if not td_left:
            continue
        a_tag = td_left.find('a')
        if not a_tag:
            continue
        title = a_tag.text.strip()
        link = a_tag.get('href')
        full_url = urljoin(url, link)

        spans = td_left.find_all('span')
        if len(spans) >= 2:
            date_str = spans[1].text.strip()
        else:
            continue

        try:
            year = int('20' + date_str.split('.')[0])
            month = int(date_str.split('.')[1])
            day = int(date_str.split('.')[2])
            date_obj = datetime(year, month, day)
            date_key = date_obj.strftime('%Y-%m-%d')
        except Exception:
            continue

        if date_obj >= five_days_ago:
            if not is_already_sent(title, date_key):
                article_info = {'title': title, 'date': date_key, 'url': full_url}
                categorized_articles[category].append(article_info)
                save_sent(title, date_key)

# ==============================
# 콘솔 출력
# ==============================
total_articles = sum(len(v) for v in categorized_articles.values())
if total_articles > 0:
    print(f"\n✅ 총 {total_articles}개 기사 수집 완료\n")
    for category, articles in categorized_articles.items():
        if not articles:
            continue
        print(f"\n📢 {category} ({len(articles)}개)\n" + "-"*60)
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"📅 {article['date']}")
            print(f"🔗 {article['url']}\n")
else:
    print(f"\n📭 최근 {DAYS_WINDOW}일 이내 신규 공지사항 없음\n")

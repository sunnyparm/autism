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

# --- 텔레그램 설정 (사용자 제공 정보) ---
TELEGRAM_BOT_TOKEN = '6250305411:AAHWIpJDIUU57x_cFORKGsPwecQq_QYlWmw'
TELEGRAM_CHAT_ID = 752516623

# 텔레그램 설정 확인
def check_telegram_config():
    """텔레그램 설정이 올바른지 확인"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  텔레그램 설정이 필요합니다!")
        print("1. 텔레그램에서 @BotFather와 대화하여 봇 생성")
        print("2. 봇 토큰과 채팅 ID를 코드에 설정")
        print("3. 자세한 방법은 '텔레그램_설정_가이드.md' 파일 참조")
        return False
    print(f"✅ 텔레그램 설정 확인됨 - 봇 토큰: {TELEGRAM_BOT_TOKEN[:10]}..., 채팅 ID: {TELEGRAM_CHAT_ID}")
    return True

DB_PATH = 'autismnews.db'
TEST_MODE = False  # 실제 모드: 텔레그램 전송 활성화
DEBUG_LIST_ALL = False  # 디버그: 날짜 필터와 무관하게 모든 행의 제목/일자를 출력
DAYS_WINDOW = 5  # 최근 5일 이내만 수집
HEADER_TITLE = '한국자폐인사랑협회 기사'

def init_db():
    if TEST_MODE:
        return
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
    if TEST_MODE:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sent_news WHERE title = ? AND date = ?", (title, date))
        return cur.fetchone() is not None

def save_sent(title, date):
    if TEST_MODE:
        return
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO sent_news (title, date) VALUES (?, ?)", (title, date))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

def send_telegram_message(message):
    """텔레그램으로 메시지를 전송합니다."""
    if TEST_MODE:
        print("테스트 모드: 텔레그램 전송 건너뜀")
        return False
        
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 봇 토큰 또는 chat_id가 설정되지 않았습니다. 메시지를 전송할 수 없습니다.")
        return False
    
    try:
        # telepot 대신 requests를 사용하여 텔레그램 API 직접 호출
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # 메시지가 너무 길면 분할
        max_length = 4096
        messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        
        for msg_part in messages:
            if msg_part.strip():
                data = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': msg_part,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=data, timeout=10)
                if response.status_code != 200:
                    print(f"텔레그램 전송 실패: {response.status_code} - {response.text}")
                    return False
        
        print("텔레그램 메시지 전송 프로세스 완료.")
        return True
        
    except Exception as e:
        print(f"오류: 텔레그램 메시지 전송 중 오류 발생: {e}")
        return False

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

# SSL 검증 경고 비활성화 (verify=False 사용 시)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        # SSL 검증 완전 비활성화
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # 다양한 SSL 설정 시도
        try:
            # 보안 레벨을 최소로 설정
            ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        except ssl.SSLError:
            try:
                # 대체 방법: 모든 암호화 방식 허용
                ctx.set_ciphers('ALL:!aNULL:!eNULL')
            except ssl.SSLError:
                pass
        
        # 프로토콜 버전 설정
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1
            ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        except AttributeError:
            # 구버전 Python 호환성
            try:
                ctx.protocol = ssl.PROTOCOL_TLS
            except:
                pass
        
        self.poolmanager = PoolManager(*args, ssl_context=ctx, **kwargs)

# 여러 SSL 설정 방법 시도
def create_session_with_ssl_fallback():
    """SSL 문제 해결을 위한 여러 방법을 시도하는 세션 생성"""
    
    # 방법 1: 개선된 TLSAdapter 사용
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        return session
    except Exception as e:
        print(f"TLSAdapter 실패: {e}")
    
    # 방법 2: 기본 세션에 SSL 비활성화
    try:
        session = requests.Session()
        session.verify = False
        return session
    except Exception as e:
        print(f"기본 세션 실패: {e}")
    
    # 방법 3: urllib3 직접 사용
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session = requests.Session()
        session.verify = False
        return session
    except Exception as e:
        print(f"urllib3 세션 실패: {e}")
    
    # 최후의 수단: 기본 requests
    return requests.Session()

session = create_session_with_ssl_fallback()

# 최근 5일 이내 기사만 수집
five_days_ago = datetime.now() - timedelta(days=DAYS_WINDOW)
msg = ''
count = 1
debug_count = 1  # DEBUG_LIST_ALL 출력용 순번

# 텔레그램 설정 확인
if not check_telegram_config():
    print("텔레그램 설정 후 다시 실행해주세요.")
    exit(1)

init_db()

def make_request_with_retry(url, max_retries=3):
    """SSL 오류를 포함한 재시도 로직이 있는 요청 함수"""
    for attempt in range(max_retries):
        print(f"요청 시작 (시도 {attempt + 1}/{max_retries}): {url}")
        
        try:
            # 다양한 SSL 설정으로 시도
            if attempt == 0:
                # 첫 번째 시도: 기본 설정
                res = session.get(url, headers=headers, timeout=15, verify=False)
            elif attempt == 1:
                # 두 번째 시도: 다른 SSL 설정
                import ssl
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                res = session.get(url, headers=headers, timeout=15, verify=False)
            else:
                # 세 번째 시도: requests 직접 사용
                res = requests.get(url, headers=headers, timeout=15, verify=False)
            
            print(f"상태 코드: {res.status_code}, 응답 길이: {len(res.content)}")
            return res
            
        except ssl.SSLError as e:
            print(f"SSL 오류 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("다른 SSL 설정으로 재시도...")
                continue
            else:
                print("모든 SSL 설정 시도 실패")
                return None
        except Exception as e:
            print(f"요청 실패 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("재시도...")
                continue
            else:
                print("모든 시도 실패")
                return None
    
    return None

# 카테고리별 기사 수집
categorized_articles = {}

for url, category in urls:
    print(f"\n=== {category} 수집 중 ===")
    res = make_request_with_retry(url)
    if res is None:
        continue
    
    # 카테고리별 기사 리스트 초기화
    if category not in categorized_articles:
        categorized_articles[category] = []
    # 응답 인코딩 판별: meta > headers > chardet > cp949 백업
    raw = res.content
    enc_candidates = []
    # meta charset 추출
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
    # 한국 사이트 일반 백업 인코딩
    enc_candidates += ['utf-8', 'cp949', 'euc-kr']
    # 후보 중 한글 검출되는 첫 디코딩 사용
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
        # 마지막 백업
        html = raw.decode('utf-8', errors='replace')
    soup = BeautifulSoup(html, 'html.parser')

    # -----------------------------
    # (1) 한국자폐인사랑협회 공지사항
    # -----------------------------
    table = soup.find('table', class_='basic_board_list')
    if not table:
        # Fallback: 카드형 목록 (ul.horizontal_board > li)
        items = soup.select('ul.horizontal_board li')
        if not items:
            print("목록 테이블/카드 목록을 찾지 못했습니다.")
            continue
        print(f"카드형 목록 개수: {len(items)}")
        for li in items:
            a_tag = li.select_one('div.txt_box h4 a') or li.select_one('h4 a')
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get('href')
            full_url = urljoin(url, link)
            # VIEW 링크 정규화
            try:
                parsed = urlparse(full_url)
                qs = parse_qs(parsed.query)
                num = qs.get('num', [None])[0]
                tbl = qs.get('tbl', [''])[0]
                if num:
                    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if not tbl:
                        # 원본 URL의 tbl 유지 시도
                        orig_qs = parse_qs(urlparse(url).query)
                        tbl = orig_qs.get('tbl', [''])[0]
                    if tbl:
                        full_url = f"{base}?tbl={tbl}&mode=VIEW&num={num}"
            except Exception:
                pass

            # 날짜 추출: '작성일' 주변 또는 YYYY-MM-DD 패턴 찾기
            date_key = None
            date_obj = None
            em = li.select_one('em')
            date_text = em.get_text(" ", strip=True) if em else li.get_text(" ", strip=True)
            m = re.search(r'(20\d{2}-\d{2}-\d{2})', date_text)
            if m:
                date_key = m.group(1)
                try:
                    y, mo, d = map(int, date_key.split('-'))
                    date_obj = datetime(y, mo, d)
                except Exception:
                    date_obj = None

            if not date_key or not date_obj:
                # 다른 포맷 시도: YY.MM.DD
                m2 = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', date_text)
                if m2:
                    y = int('20' + m2.group(1))
                    mo = int(m2.group(2))
                    d = int(m2.group(3))
                    try:
                        date_obj = datetime(y, mo, d)
                        date_key = date_obj.strftime('%Y-%m-%d')
                    except Exception:
                        date_key = None

            if not date_key:
                # 날짜 없으면 스킵
                continue

            if DEBUG_LIST_ALL:
                print(f"{debug_count}\t{title}\t{date_key}\t{full_url}")
                debug_count += 1

            # 최근 5일 이내 기사만 수집
            if date_obj >= five_days_ago:
                if not is_already_sent(title, date_key):
                    article_info = {
                        'title': title,
                        'date': date_key,
                        'url': full_url
                    }
                    categorized_articles[category].append(article_info)
                    print(f"{len(categorized_articles[category])}. {title} ({date_key})")
                    save_sent(title, date_key)
        # 카드형을 처리했으므로 테이블 파싱은 건너뜀
        continue
    rows = table.find_all('tr')

    print(f"행 개수: {len(rows)}")
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
        # 깔끔한 VIEW 링크로 정규화: ...&mode=VIEW&num=XXXX
        try:
            parsed = urlparse(full_url)
            qs = parse_qs(parsed.query)
            num = qs.get('num', [None])[0]
            tbl = qs.get('tbl', ['bbs31'])[0]
            if num:
                base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                full_url = f"{base}?tbl={tbl}&mode=VIEW&num={num}"
        except Exception:
            pass

        # 날짜는 <span> 중 두 번째 (예: 25.09.11)
        spans = td_left.find_all('span')
        if len(spans) >= 2:
            date_str = spans[1].text.strip()
        else:
            date_str = None

        if not date_str:
            continue

        # 날짜 형식 변환
        try:
            # '25.09.11' → '2025-09-11'
            year = int('20' + date_str.split('.')[0])
            month = int(date_str.split('.')[1])
            day = int(date_str.split('.')[2])
            date_obj = datetime(year, month, day)
            date_key = date_obj.strftime('%Y-%m-%d')
        except Exception:
            continue

        if DEBUG_LIST_ALL:
            print(f"{debug_count}\t{title}\t{date_key}\t{full_url}")
            debug_count += 1

        # 최근 5일 이내 기사만 수집
        if date_obj >= five_days_ago:
            if not is_already_sent(title, date_key):
                article_info = {
                    'title': title,
                    'date': date_key,
                    'url': full_url
                }
                categorized_articles[category].append(article_info)
                print(f"{len(categorized_articles[category])}. {title} ({date_key})")
                save_sent(title, date_key)

# ==============================
# 카테고리별 텔레그램 전송
# ==============================
total_articles = sum(len(articles) for articles in categorized_articles.values())

if total_articles > 0:
    print(f"\n=== 총 {total_articles}개 기사 수집 완료 ===")
    
    for category, articles in categorized_articles.items():
        if not articles:
            continue
            
        print(f"\n--- {category} ({len(articles)}개) ---")
        
        # 카테고리별 메시지 생성
        category_message = f"<b>📢 {category}</b>\n\n"
        
        for i, article in enumerate(articles, 1):
            # HTML 특수문자 이스케이프
            title = article['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            article_text = f"<b>{i}.</b> {title}\n📅 {article['date']}\n🔗 <a href='{article['url']}'>링크</a>\n\n"
            
            # 메시지 길이 확인 (4000자 제한)
            if len(category_message + article_text) > 4000:
                # 현재 메시지 전송
                print(f"전송할 메시지 ({category}):\n{category_message}")
                if not TEST_MODE:
                    send_telegram_message(category_message)
                else:
                    print("테스트 모드: 텔레그램 전송 건너뜀")
                
                # 새 메시지 시작
                category_message = f"<b>📢 {category} (계속)</b>\n\n" + article_text
            else:
                category_message += article_text
        
        # 마지막 메시지 전송
        if category_message.strip():
            print(f"전송할 메시지 ({category}):\n{category_message}")
            if not TEST_MODE:
                send_telegram_message(category_message)
            else:
                print("테스트 모드: 텔레그램 전송 건너뜀")
                
else:
    # 수집된 기사가 없는 경우
    no_news_message = f"<b>{HEADER_TITLE}</b>\n\n신규 공지사항 없음"
    print(no_news_message)
    
    if not TEST_MODE:
        send_telegram_message(no_news_message)
    else:
        print("테스트 모드: 텔레그램 전송 건너뜀")

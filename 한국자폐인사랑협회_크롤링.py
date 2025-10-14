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

DB_PATH = 'disablednews_sent.db'
TEST_MODE = True  # 테스트용: DB/텔레그램 비활성화, 크롤링 결과만 출력
DEBUG_LIST_ALL = True  # 디버그: 날짜 필터와 무관하게 모든 행의 제목/일자를 출력
DAYS_WINDOW = 5  # 최근 N일 이내만 수집
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

# ==============================
# 수집 대상 URL
# ==============================
urls = [
    'https://www.autismkorea.kr/bbs/board.php?tbl=bbs31',  # 공지사항
    'https://www.autismkorea.kr/bbs/board.php?tbl=bbs36',  # 뉴스레터
    'https://www.autismkorea.kr/bbs/board.php?tbl=bbs32',  # 언론보도
    'https://www.autismkorea.kr/bbs/board.php?tbl=bbs34'   # 외부기관 소식
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

five_days_ago = datetime.now() - timedelta(days=DAYS_WINDOW)
msg = ''
count = 1
debug_count = 1  # DEBUG_LIST_ALL 출력용 순번

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

for url in urls:
    res = make_request_with_retry(url)
    if res is None:
        continue
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

            if date_obj >= five_days_ago:
                if not is_already_sent(title, date_key):
                    line = f"{count}\t{title}\t{date_key}\t{full_url}"
                    print(line)
                    msg += line + "\n"
                    save_sent(title, date_key)
                    count += 1
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

        # 최근 5일 이내만 수집
        if date_obj >= five_days_ago:
            if not is_already_sent(title, date_key):
                line = f"{count}\t{title}\t{date_key}\t{full_url}"
                print(line)
                msg += line + "\n"
                save_sent(title, date_key)
                count += 1

# ==============================
# 테스트 모드: 콘솔 출력만
# ==============================
if TEST_MODE:
    print(HEADER_TITLE)
    if msg:
        print("수집 결과:\n" + msg)
    else:
        print("최근 5일 이내 신규 공지사항 없음")
else:
    # 실제 모드에서만 텔레그램 전송 (여기선 비활성화)
    if msg:
        msg = HEADER_TITLE + "\n" + msg
    pass

# 한국자폐인사랑협회 뉴스 크롤링 & 텔레그램 봇

한국자폐인사랑협회 웹사이트에서 최신 뉴스와 공지사항을 자동으로 수집하고 텔레그램으로 전송하는 Python 스크립트입니다.

## 주요 기능

- **카테고리별 뉴스 수집**: 한국자폐인사랑협회의 다음 섹션에서 뉴스를 수집합니다:
  - 📢 공지사항
  - 📢 뉴스레터  
  - 📢 언론보도
  - 📢 외부기관 소식
- **스마트 필터링**: 최근 5일 이내의 새로운 게시물만 수집
- **중복 방지**: SQLite 데이터베이스를 통한 중복 게시물 방지
- **텔레그램 자동 전송**: 카테고리별로 분류된 뉴스를 텔레그램으로 자동 전송
- **SSL 문제 해결**: 커스텀 어댑터를 통한 SSL 인증서 문제 해결

## 설치 및 실행

### 필요 라이브러리
```bash
pip install requests beautifulsoup4 urllib3 chardet
```

### 텔레그램 봇 설정

1. **텔레그램 봇 생성**:
   - 텔레그램에서 `@BotFather` 검색
   - `/newbot` 명령어로 봇 생성
   - 봇 토큰 복사

2. **채팅 ID 확인**:
   - 봇과 대화하거나 그룹에 봇 추가
   - `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` 접속
   - 채팅 ID 확인

3. **코드에 설정 적용**:
   ```python
   TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'
   TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'
   ```

### 실행
```bash
python 한국자폐인사랑협회_크롤링.py
```

## 설정 옵션

- `TEST_MODE`: 테스트 모드 (True/False) - 텔레그램 전송 비활성화
- `DAYS_WINDOW`: 수집할 최근 일수 (기본값: 5일)
- `DEBUG_LIST_ALL`: 디버그 모드 (모든 게시물 출력)
- `DB_PATH`: 데이터베이스 파일 경로 (기본값: 'autismnews.db')

## 데이터베이스

SQLite 데이터베이스를 사용하여 이미 전송된 뉴스를 추적합니다.
- **파일명**: `autismnews.db`
- **테이블**: `sent_news`
- **컬럼**: `title`, `date`

## 메시지 형식

텔레그램으로 전송되는 메시지는 다음과 같은 형식입니다:

```
📢 공지사항

1. 기사 제목
📅 2025-01-01
🔗 링크

2. 기사 제목
📅 2025-01-01
🔗 링크
```

## 자동화 설정

### ✅ Windows 작업 스케줄러 (권장)
1. 작업 스케줄러 열기
2. 기본 작업 만들기
3. 트리거: 매일 원하는 시간
4. 동작: 프로그램 시작
5. 프로그램: `C:\Python\python.exe`
6. 인수: `한국자폐인사랑협회_크롤링.py`
7. 시작 위치: `C:\Users\KR\Desktop\git_repo\autism`

### Linux/Mac Cron
```bash
# 매일 오전 9시에 실행
0 9 * * * cd /path/to/autism && /usr/bin/python3 한국자폐인사랑협회_크롤링.py
```

### ⚠️ PythonAnywhere에서 실행 시 주의사항

**PythonAnywhere 무료 계정의 제한:**
- 화이트리스트된 사이트만 접근 가능
- `autismkorea.kr`은 화이트리스트에 **없습니다**
- 무료 계정으로는 크롤링이 **불가능**합니다

**해결 방법:**
1. **PythonAnywhere 유료 계정** ($5/월) - 모든 사이트 접근 가능
2. **로컬 컴퓨터에서 실행** (Windows 작업 스케줄러 사용) ← 권장
3. **GitHub Actions** (무료 대안)
4. **AWS Lambda, Google Cloud Functions** 등

**테스트 방법:**
```bash
# PythonAnywhere에서 연결 테스트
python3 test_connection.py
```

자세한 내용은 `가상환경_문제_해결.md` 파일을 참고하세요.

## 문제 해결

### SSL 오류
- 스크립트에 SSL 문제 해결 로직이 포함되어 있습니다
- 여전히 문제가 발생하면 네트워크 설정을 확인하세요

### 텔레그램 전송 실패
- 봇 토큰과 채팅 ID가 올바른지 확인
- 봇이 해당 채팅방에 추가되어 있는지 확인

## 주의사항

- 이 스크립트는 교육 및 연구 목적으로만 사용하세요
- 웹사이트의 이용약관을 준수하세요
- 과도한 요청으로 서버에 부하를 주지 않도록 주의하세요
- 개인정보 보호를 위해 봇 토큰을 안전하게 보관하세요

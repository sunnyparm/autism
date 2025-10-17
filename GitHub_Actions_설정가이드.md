# GitHub Actions 무료 클라우드 자동화 설정 가이드

## 🎯 GitHub Actions란?

- GitHub에서 제공하는 **무료 자동화 서비스**
- 매월 **2,000분 무료** (이 스크립트는 1회 실행에 1분도 안 걸림)
- 컴퓨터 꺼도 GitHub 서버에서 자동 실행
- 매일 정해진 시간에 자동 실행 가능

---

## ✅ 설정 방법 (5분 완료)

### 1단계: GitHub 저장소 생성/확인

#### 방법 A: 기존 저장소가 있다면
- 현재 프로젝트가 이미 Git 저장소인지 확인

#### 방법 B: 새로 만들기
```bash
# 현재 폴더에서
git init
git add .
git commit -m "Initial commit"
```

---

### 2단계: GitHub에 저장소 생성

1. GitHub (https://github.com) 로그인
2. 우측 상단 `+` → `New repository` 클릭
3. 저장소 이름: `autism` (또는 원하는 이름)
4. Public 또는 Private 선택 (둘 다 Actions 무료 사용 가능)
5. `Create repository` 클릭

---

### 3단계: 로컬 코드를 GitHub에 업로드

```bash
# GitHub 저장소 주소로 연결
git remote add origin https://github.com/YOUR_USERNAME/autism.git

# 업로드
git branch -M main
git push -u origin main
```

**주의:** 텔레그램 봇 토큰이 코드에 노출되므로 **반드시 Private 저장소** 사용!

---

### 4단계: GitHub Secrets에 민감 정보 저장

**중요:** 봇 토큰을 코드에서 제거하고 GitHub Secrets로 관리해야 합니다.

1. GitHub 저장소 페이지에서 `Settings` 클릭
2. 좌측 메뉴에서 `Secrets and variables` → `Actions` 클릭
3. `New repository secret` 클릭
4. 다음 두 개의 Secret 추가:

**Secret 1:**
- Name: `TELEGRAM_BOT_TOKEN`
- Value: `6250305411:AAHWIpJDIUU57x_cFORKGsPwecQq_QYlWmw`

**Secret 2:**
- Name: `TELEGRAM_CHAT_ID`
- Value: `752516623`

---

### 5단계: 코드 수정 - Secrets 사용하도록 변경

`한국자폐인사랑협회_크롤링.py` 파일 수정:

**변경 전:**
```python
TELEGRAM_BOT_TOKEN = '6250305411:AAHWIpJDIUU57x_cFORKGsPwecQq_QYlWmw'
TELEGRAM_CHAT_ID = 752516623
```

**변경 후:**
```python
# GitHub Actions 환경변수에서 가져오기 (로컬에서도 작동하도록)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '6250305411:AAHWIpJDIUU57x_cFORKGsPwecQq_QYlWmw')
TELEGRAM_CHAT_ID = int(os.environ.get('TELEGRAM_CHAT_ID', '752516623'))
```

---

### 6단계: Workflow 파일 확인

이미 생성된 `.github/workflows/daily-crawler.yml` 파일 확인:

```yaml
name: Daily News Crawler

on:
  schedule:
    # 매일 한국 시간 오전 9시 (UTC 0시)
    - cron: '0 0 * * *'
  workflow_dispatch:  # 수동 실행도 가능

jobs:
  crawl:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4 urllib3 chardet
      
      - name: Run crawler
        env:
          OPENSSL_CONF: /dev/null
          PYTHONHTTPSVERIFY: '0'
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python 한국자폐인사랑협회_크롤링.py
```

---

### 7단계: GitHub에 업로드

```bash
git add .
git commit -m "GitHub Actions 설정 추가"
git push
```

---

### 8단계: 수동 테스트

1. GitHub 저장소 페이지에서 `Actions` 탭 클릭
2. 좌측에서 `Daily News Crawler` 클릭
3. 우측 `Run workflow` 버튼 클릭
4. `Run workflow` 재확인
5. 실행 결과 확인 (1-2분 소요)

---

## 🎉 완료!

이제 매일 한국 시간 오전 9시에 자동으로 뉴스를 수집하여 텔레그램으로 전송합니다!

---

## ⚙️ 실행 시간 변경

`.github/workflows/daily-crawler.yml` 파일의 `cron` 부분 수정:

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 0시 = 한국 9시
  - cron: '0 12 * * *'  # UTC 12시 = 한국 21시 (저녁)
```

**Cron 표현식:**
- `분 시 일 월 요일`
- `0 0 * * *` = 매일 00:00 (UTC)
- `30 8 * * *` = 매일 08:30 (UTC)
- `0 */6 * * *` = 6시간마다

**UTC ↔ 한국 시간 변환:**
- UTC +9시간 = 한국 시간
- 한국 오전 9시 → UTC 0시
- 한국 오후 6시 → UTC 9시

---

## 🔧 문제 해결

### Actions 실행 안 됨
- Settings → Actions → General → "Allow all actions" 확인

### 권한 오류
- Settings → Actions → General → Workflow permissions → "Read and write permissions" 선택

### 텔레그램 전송 실패
- Secrets가 올바르게 설정되었는지 확인
- Actions 로그에서 오류 메시지 확인

---

## 📊 장점 정리

✅ **완전 무료** (월 2,000분 제공, 실제 사용은 월 30분 정도)  
✅ **컴퓨터 꺼도 됨** (GitHub 서버에서 실행)  
✅ **안정적** (GitHub 인프라 사용)  
✅ **로그 확인 가능** (Actions 탭에서 실행 기록 확인)  
✅ **언제든 수동 실행** (Run workflow 버튼)  
✅ **DH_KEY 문제 없음** (Ubuntu OpenSSL 사용)  

---

## 💡 추가 팁

### 여러 시간대에 실행
```yaml
schedule:
  - cron: '0 0 * * *'   # 한국 오전 9시
  - cron: '0 9 * * *'   # 한국 오후 6시
  - cron: '0 12 * * *'  # 한국 오후 9시
```

### 특정 요일만 실행
```yaml
schedule:
  - cron: '0 0 * * 1-5'  # 월-금요일만
```

### 알림 받기
- GitHub 저장소 → Watch → Custom → Actions 체크
- 실행 실패 시 이메일로 알림 받음

---

## 🚀 다음 단계

1. ✅ GitHub 저장소 생성
2. ✅ Secrets 설정
3. ✅ 코드 수정 및 업로드
4. ✅ 수동 테스트
5. ✅ 내일 아침 자동 실행 확인!

설정 중 막히는 부분이 있으면 언제든 물어보세요! 😊


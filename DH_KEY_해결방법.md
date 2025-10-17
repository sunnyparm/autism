# DH_KEY_TOO_SMALL 오류 완벽 해결 가이드

## 🔍 문제 분석

테스트 결과:
- ✅ Google 접속 성공 → PythonAnywhere 네트워크는 정상
- ❌ autismkorea.kr 접속 실패 → **SSL DH 키 크기 문제**

**진짜 원인:** `autismkorea.kr` 서버가 오래된 SSL 설정(작은 DH 키)을 사용하고 있어서, 최신 OpenSSL(3.x)에서 보안상 거부함

## ✅ 해결 방법

### 방법 1: 로컬 Windows에서 실행 (강력 권장 ⭐⭐⭐⭐⭐)

**현재 로컬에서는 정상 작동하고 있습니다!**

이유: Windows Python의 OpenSSL이 더 완화된 설정을 가지고 있음

**Windows 작업 스케줄러로 자동화:**
```
프로그램: C:\Python\python.exe
인수: 한국자폐인사랑협회_크롤링.py
시작 위치: C:\Users\KR\Desktop\git_repo\autism
트리거: 매일 오전 9시
```

**장점:**
- ✅ 무료
- ✅ 이미 작동 중
- ✅ 추가 설정 불필요
- ✅ 완벽한 제어

---

### 방법 2: GitHub Actions (무료 클라우드 자동화 ⭐⭐⭐⭐)

`.github/workflows/daily-crawler.yml` 파일 생성:

```yaml
name: Daily News Crawler

on:
  schedule:
    # 매일 한국 시간 오전 9시 (UTC 0시)
    - cron: '0 0 * * *'
  workflow_dispatch:  # 수동 실행 가능

jobs:
  crawl:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
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
        run: |
          python 한국자폐인사랑협회_크롤링.py
```

**장점:**
- ✅ 완전 무료
- ✅ 24시간 자동 실행
- ✅ GitHub에서 관리
- ✅ DH_KEY 문제 없음 (Ubuntu의 OpenSSL이 더 유연함)

**설정 방법:**
1. GitHub 저장소에 `.github/workflows/` 폴더 생성
2. 위 파일 추가
3. GitHub Secrets에 텔레그램 봇 토큰 추가
4. 자동으로 매일 실행됨

---

### 방법 3: PythonAnywhere - OpenSSL 다운그레이드

PythonAnywhere에서 오래된 OpenSSL 버전 사용:

**Bash 콘솔에서:**
```bash
# Python 3.9 사용 (OpenSSL 1.1.1 사용)
python3.9 한국자폐인사랑협회_크롤링.py

# 또는 Python 3.8
python3.8 한국자폐인사랑협회_크롤링.py
```

**스케줄러 설정:**
```bash
cd /home/YOUR_USERNAME/autism && python3.9 한국자폐인사랑협회_크롤링.py
```

**참고:** Python 3.10 이하는 OpenSSL 1.1.1을 사용하여 DH_KEY 제한이 덜 엄격함

---

### 방법 4: 직접 HTTP 요청 (최후의 수단)

`urllib3`의 `contrib.pyopenssl` 사용:

```python
# 한국자폐인사랑협회_크롤링.py 맨 위에 추가
try:
    # pyOpenSSL을 사용하여 urllib3 패치
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
    print("✅ pyOpenSSL 주입 성공")
except ImportError:
    print("⚠️  pyOpenSSL 없음 - pip install pyOpenSSL")
```

**설치:**
```bash
pip install pyOpenSSL cryptography --user
```

---

## 🧪 각 방법 테스트

### 로컬 Windows 테스트:
```bash
python test_connection.py
# 결과: autismkorea.kr 접속 성공 예상
```

### PythonAnywhere Python 3.9 테스트:
```bash
python3.9 test_connection.py
# 결과: DH_KEY 오류 없을 가능성 높음
```

### GitHub Actions 테스트:
- 저장소에 파일 추가 후 "Actions" 탭에서 "Run workflow" 클릭

---

## 📊 방법 비교

| 방법 | 비용 | 난이도 | 안정성 | 추천도 |
|------|------|--------|--------|--------|
| **로컬 Windows** | 무료 | ⭐ 쉬움 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **GitHub Actions** | 무료 | ⭐⭐ 보통 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **PythonAnywhere 3.9** | 무료 | ⭐ 쉬움 | ⭐⭐⭐ | ⭐⭐⭐ |
| **PythonAnywhere 유료** | $5/월 | ⭐ 쉬움 | ⭐⭐⭐⭐ | ⭐⭐ |
| **pyOpenSSL** | 무료 | ⭐⭐⭐ 어려움 | ⭐⭐ | ⭐ |

---

## 🎯 최종 권장 사항

### 현재 상황:
- ✅ 로컬 Windows에서 **완벽하게 작동**
- ❌ PythonAnywhere에서 DH_KEY 오류

### 권장 순서:

1. **로컬 Windows 계속 사용** (가장 간단, 현재 작동 중)
   - Windows 작업 스케줄러로 자동화
   - 컴퓨터를 항상 켜놓거나 원하는 시간에만 실행

2. **GitHub Actions 도입** (무료 클라우드 자동화)
   - 컴퓨터 꺼도 됨
   - 완전 무료
   - 5분 설정으로 영구 자동화

3. **PythonAnywhere는 포기** (DH_KEY 문제 해결 복잡)
   - Python 3.9로 시도해볼 수는 있음
   - 하지만 다른 방법이 더 간단함

---

## 💡 즉시 실행 가능한 명령어

### PythonAnywhere에서 바로 테스트:
```bash
# Python 3.9로 테스트
python3.9 test_connection.py

# 성공하면 메인 스크립트 실행
python3.9 한국자폐인사랑협회_크롤링.py
```

### 로컬에서 작업 스케줄러 설정:
1. `Win + R` → `taskschd.msc`
2. "기본 작업 만들기"
3. 이름: "자폐협회 뉴스 크롤링"
4. 트리거: 매일 오전 9시
5. 동작: 프로그램 시작
6. 프로그램: `C:\Python\python.exe` (또는 `python` 명령어 전체 경로)
7. 인수: `한국자폐인사랑협회_크롤링.py`
8. 시작 위치: `C:\Users\KR\Desktop\git_repo\autism`
9. 완료!

---

## 🚀 결론

**가장 쉬운 해결책:** 로컬 Windows에서 계속 실행 + 작업 스케줄러

**컴퓨터 꺼도 되는 해결책:** GitHub Actions (무료)

**PythonAnywhere:** Python 3.9로 시도 가능하지만, 위 두 방법이 더 나음


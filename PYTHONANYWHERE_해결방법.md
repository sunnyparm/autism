# PythonAnywhere 403/SSL 오류 해결 방법

## 문제 상황
PythonAnywhere에서 한국자폐인사랑협회 웹사이트 크롤링 시 다음 오류 발생:
- `403 Forbidden` 오류
- `SSL: DH_KEY_TOO_SMALL` 오류

## 원인
1. **403 오류**: 서버에서 PythonAnywhere IP 대역을 차단하거나 봇 접근 차단
2. **SSL 오류**: PythonAnywhere의 Python/OpenSSL 버전이 오래된 DH 키를 지원하지 않음

## 해결 방법

### 방법 1: PythonAnywhere에서 환경 변수 설정 (권장)

PythonAnywhere 배시 콘솔에서 다음 명령어 실행:

```bash
# OpenSSL 보안 레벨 낮추기
export OPENSSL_CONF=/dev/null
export PYTHONHTTPSVERIFY=0

# 또는 Python 스크립트 실행 전에:
OPENSSL_CONF=/dev/null python 한국자폐인사랑협회_크롤링.py
```

### 방법 2: PythonAnywhere 스케줄 설정

PythonAnywhere의 "Tasks" 탭에서 스케줄 설정 시:

```bash
cd /home/YOUR_USERNAME/autism && OPENSSL_CONF=/dev/null python3 한국자폐인사랑협회_크롤링.py
```

### 방법 3: 스크립트 시작 부분에 추가

`한국자폐인사랑협회_크롤링.py` 파일 맨 위에 추가:

```python
import os
os.environ['OPENSSL_CONF'] = '/dev/null'
os.environ['PYTHONHTTPSVERIFY'] = '0'
```

### 방법 4: requests-html 또는 selenium 사용

더 강력한 크롤링이 필요한 경우:

```bash
pip install requests-html --user
```

```python
from requests_html import HTMLSession

session = HTMLSession()
response = session.get(url)
# JavaScript 렌더링도 가능
response.html.render()
```

### 방법 5: PythonAnywhere 유료 계정 (최종 해결책)

무료 계정은 화이트리스트된 사이트만 접근 가능합니다.
유료 계정($5/월)으로 업그레이드하면 모든 사이트 접근 가능합니다.

## 테스트 방법

1. PythonAnywhere 배시 콘솔에서:
```bash
cd autism
OPENSSL_CONF=/dev/null python3 한국자폐인사랑협회_크롤링.py
```

2. 오류가 계속되면 Python 버전 확인:
```bash
python3 --version
openssl version
```

3. 필요시 최신 Python 버전 사용:
```bash
python3.10 한국자폐인사랑협회_크롤링.py
```

## 주의사항

- PythonAnywhere 무료 계정은 외부 사이트 접근이 제한될 수 있습니다
- 화이트리스트: https://www.pythonanywhere.com/whitelist/
- `autismkorea.kr`이 화이트리스트에 없으면 유료 계정이 필요합니다

## 대안

로컬 컴퓨터나 다른 호스팅(Heroku, AWS Lambda, Google Cloud Functions 등)에서 실행하는 것을 권장합니다.


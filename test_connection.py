#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere 연결 테스트 스크립트
이 스크립트로 PythonAnywhere에서 외부 사이트 접근이 가능한지 확인하세요.
"""

import os
import sys

# OpenSSL 설정 파일 경로 지정
script_dir = os.path.dirname(os.path.abspath(__file__))
openssl_conf_path = os.path.join(script_dir, 'openssl.cnf')

# OpenSSL 설정 적용
if os.path.exists(openssl_conf_path):
    os.environ['OPENSSL_CONF'] = openssl_conf_path
    print(f"✅ OpenSSL 설정 파일 사용: {openssl_conf_path}")
else:
    os.environ['OPENSSL_CONF'] = '/dev/null'
    print("⚠️  OpenSSL 설정 파일 없음 - 기본 우회 방법 사용")

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

import requests
import ssl

print("=" * 70)
print("PythonAnywhere 연결 테스트")
print("=" * 70)
print()

print("📋 환경 정보")
print("-" * 70)
print(f"Python 버전: {sys.version}")
print(f"SSL 버전: {ssl.OPENSSL_VERSION}")
print(f"OPENSSL_CONF: {os.environ.get('OPENSSL_CONF', 'NOT SET')}")
print(f"PYTHONHTTPSVERIFY: {os.environ.get('PYTHONHTTPSVERIFY', 'NOT SET')}")
print()

# SSL 경고 비활성화
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("=" * 70)
print("테스트 1: Google (PythonAnywhere 화이트리스트에 있음)")
print("-" * 70)
try:
    res = requests.get('https://www.google.com', timeout=10, verify=False)
    print(f"✅ 성공!")
    print(f"   상태 코드: {res.status_code}")
    print(f"   응답 길이: {len(res.content)} bytes")
except Exception as e:
    print(f"❌ 실패!")
    print(f"   오류: {e}")
print()

print("=" * 70)
print("테스트 2: autismkorea.kr (목표 사이트)")
print("-" * 70)
try:
    res = requests.get('https://www.autismkorea.kr/', timeout=10, verify=False)
    print(f"✅ 성공!")
    print(f"   상태 코드: {res.status_code}")
    print(f"   응답 길이: {len(res.content)} bytes")
    print()
    print("🎉 autismkorea.kr 접근 가능! 크롤링 스크립트 실행 가능합니다.")
except requests.exceptions.ConnectionError as e:
    print(f"❌ 연결 실패!")
    print(f"   오류: {e}")
    print()
    print("⚠️  이것은 PythonAnywhere 무료 계정의 네트워크 제한 때문입니다!")
    print()
    print("해결 방법:")
    print("1. PythonAnywhere 유료 계정 ($5/월)으로 업그레이드")
    print("2. 로컬 컴퓨터에서 실행 (Windows 작업 스케줄러 사용)")
    print("3. GitHub Actions 무료 사용")
    print("4. AWS Lambda, Google Cloud Functions 등 다른 서비스 사용")
except Exception as e:
    print(f"❌ 기타 오류!")
    print(f"   오류: {e}")
print()

print("=" * 70)
print("테스트 3: 실제 게시판 페이지")
print("-" * 70)
try:
    res = requests.get('https://www.autismkorea.kr/bbs/board.php?tbl=bbs31', 
                      timeout=10, verify=False)
    if res.status_code == 403:
        print(f"❌ 403 Forbidden")
        print(f"   서버에서 봇 접근을 차단했습니다.")
        print()
        print("가능한 원인:")
        print("1. PythonAnywhere IP 차단")
        print("2. User-Agent 기반 봇 탐지")
        print("3. 속도 제한 (Rate Limiting)")
    elif res.status_code == 200:
        print(f"✅ 성공!")
        print(f"   상태 코드: {res.status_code}")
        print(f"   응답 길이: {len(res.content)} bytes")
        print()
        print("🎉 게시판 접근 가능! 크롤링 스크립트가 정상 작동할 것입니다.")
    else:
        print(f"⚠️  예상치 못한 상태 코드: {res.status_code}")
except requests.exceptions.ConnectionError as e:
    print(f"❌ 연결 실패!")
    print(f"   오류: {e}")
    print()
    print("⚠️  PythonAnywhere 무료 계정의 네트워크 제한!")
except Exception as e:
    print(f"❌ 오류!")
    print(f"   오류: {e}")
print()

print("=" * 70)
print("테스트 완료")
print("=" * 70)


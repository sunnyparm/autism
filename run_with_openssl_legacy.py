#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSSL 레거시 모드로 크롤링 스크립트 실행
DH_KEY_TOO_SMALL 오류 해결을 위한 래퍼 스크립트
"""

import os
import sys
import subprocess

# OpenSSL 레거시 모드 활성화
os.environ['OPENSSL_CONF'] = os.path.join(os.path.dirname(__file__), 'openssl.cnf')
os.environ['PYTHONHTTPSVERIFY'] = '0'

# cryptography 라이브러리 설치 확인 및 설치
try:
    import cryptography
    print("✅ cryptography 라이브러리 설치됨")
except ImportError:
    print("⚠️  cryptography 라이브러리 설치 중...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'cryptography', '--user'], 
                   capture_output=True)
    print("✅ cryptography 설치 완료")

# pyOpenSSL 설치 확인 및 설치
try:
    import OpenSSL
    print("✅ pyOpenSSL 라이브러리 설치됨")
except ImportError:
    print("⚠️  pyOpenSSL 라이브러리 설치 중...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyOpenSSL', '--user'], 
                   capture_output=True)
    print("✅ pyOpenSSL 설치 완료")

# urllib3 재설치 (pyOpenSSL 지원 포함)
print("🔄 urllib3 업그레이드 중...")
subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'urllib3[secure]', '--user'], 
               capture_output=True)

print("\n" + "=" * 70)
print("크롤링 스크립트 실행 시작")
print("=" * 70 + "\n")

# 메인 스크립트 실행
script_path = os.path.join(os.path.dirname(__file__), '한국자폐인사랑협회_크롤링.py')
subprocess.run([sys.executable, script_path])


# GitHub Actions 빠른 시작 가이드

## 🚀 5분 만에 시작하기

### 1️⃣ GitHub 계정 준비
- GitHub 계정이 없다면: https://github.com/join
- 이미 있다면 로그인: https://github.com/login

---

### 2️⃣ 저장소 생성

1. GitHub 우측 상단 **`+`** → **`New repository`** 클릭
2. 저장소 이름: **`autism`**
3. **Private** 선택 (봇 토큰 보호를 위해 필수!)
4. **Create repository** 클릭

---

### 3️⃣ 로컬 코드를 GitHub에 업로드

현재 폴더에서 PowerShell/CMD 실행:

```bash
# Git 초기화 (이미 했다면 생략)
git init

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: 자폐협회 뉴스 크롤러"

# GitHub 저장소 연결 (YOUR_USERNAME을 본인 GitHub ID로 변경!)
git remote add origin https://github.com/YOUR_USERNAME/autism.git

# 업로드
git branch -M main
git push -u origin main
```

**예시:**
```bash
# 예: GitHub ID가 "hong123"이라면
git remote add origin https://github.com/hong123/autism.git
```

**처음 push할 때 로그인 요청:**
- GitHub ID와 비밀번호 입력
- 또는 Personal Access Token 사용

---

### 4️⃣ GitHub Secrets 설정 (중요!)

1. GitHub 저장소 페이지에서 **`Settings`** 클릭
2. 좌측 메뉴 **`Secrets and variables`** → **`Actions`** 클릭
3. **`New repository secret`** 클릭

**Secret 1 추가:**
- Name: `TELEGRAM_BOT_TOKEN`
- Secret: `6250305411:AAHWIpJDIUU57x_cFORKGsPwecQq_QYlWmw`
- **Add secret** 클릭

**Secret 2 추가:**
- Name: `TELEGRAM_CHAT_ID`
- Secret: `752516623`
- **Add secret** 클릭

---

### 5️⃣ Actions 활성화 확인

1. 저장소 페이지에서 **`Actions`** 탭 클릭
2. "Workflows aren't being run..." 메시지가 나오면 **`I understand...`** 클릭
3. 좌측에 **`Daily News Crawler`** 워크플로우가 보이면 성공!

---

### 6️⃣ 수동 테스트 (중요!)

1. **`Actions`** 탭에서 **`Daily News Crawler`** 클릭
2. 우측 **`Run workflow`** 드롭다운 클릭
3. **`Run workflow`** 버튼 클릭
4. 페이지 새로고침 후 실행 중인 작업 클릭
5. 각 단계별 로그 확인

**예상 결과:**
- ✅ Checkout repository
- ✅ Set up Python
- ✅ Install dependencies
- ✅ Run crawler
- ✅ 텔레그램으로 메시지 수신!

---

## 🎉 완료!

이제 **매일 한국 시간 오전 9시**에 자동으로 실행됩니다!

컴퓨터를 꺼도 GitHub 서버에서 자동으로 뉴스를 수집하고 텔레그램으로 전송합니다.

---

## ⚙️ 실행 시간 변경하기

`.github/workflows/daily-crawler.yml` 파일 수정:

### 오전 6시로 변경:
```yaml
schedule:
  - cron: '0 21 * * *'  # UTC 21시 = 한국 오전 6시
```

### 오후 9시로 변경:
```yaml
schedule:
  - cron: '0 12 * * *'  # UTC 12시 = 한국 오후 9시
```

### 하루 2번 실행:
```yaml
schedule:
  - cron: '0 0 * * *'   # 오전 9시
  - cron: '0 12 * * *'  # 오후 9시
```

**변경 후:**
```bash
git add .github/workflows/daily-crawler.yml
git commit -m "실행 시간 변경"
git push
```

---

## 🔧 문제 해결

### Q: git push 시 인증 오류
**A:** Personal Access Token 사용
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. repo 권한 체크
4. 생성된 토큰을 비밀번호 대신 사용

### Q: Actions 탭이 안 보임
**A:** Settings → Actions → General → "Allow all actions" 체크

### Q: 텔레그램 메시지가 안 옴
**A:** 
1. Secrets가 올바르게 설정되었는지 확인
2. Actions 로그에서 오류 확인
3. 텔레그램 봇이 채팅방에 추가되어 있는지 확인

### Q: 매일 실행이 안 됨
**A:**
1. Actions가 활성화되어 있는지 확인
2. 저장소가 Private이어도 Actions 사용 가능
3. GitHub 계정이 인증되어 있는지 확인

---

## 📊 사용량 확인

- Settings → Billing → Usage this month
- 무료: 월 2,000분 제공
- 이 스크립트: 1회 실행 약 1분
- 하루 1회 실행: 월 30분 사용 (매우 여유로움!)

---

## 💡 추가 팁

### 로그 확인:
- Actions 탭에서 과거 실행 기록 모두 확인 가능

### 실행 기록 알림:
- Watch → Custom → Actions 체크 → 실패 시 이메일 알림

### 즉시 실행:
- Actions → Daily News Crawler → Run workflow

---

## 📞 도움이 필요하면

자세한 설명은 `GitHub_Actions_설정가이드.md` 파일을 참고하세요!

설정 중 문제가 생기면 언제든 물어보세요! 😊


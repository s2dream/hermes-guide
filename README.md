# hermes-guide

Hermes Agent의 Ubuntu 설치·모델 설정부터 텔레그램·웹 UI 연동, 다중 사용자 정보 탐색 서비스의 요구사항과 설계까지 다루는 비공식 한국어 가이드입니다.

## 가이드 보기

웹사이트는 [GitHub Pages](https://s2dream.github.io/hermes-guide/)에서 볼 수 있습니다. 상단 메뉴는 Ubuntu 설치, 텔레그램, 웹 UI, 서비스 설계의 네 범주로 구성되어 있습니다. 웹 UI 메뉴에는 제품별 연결 안내가, 서비스 설계 메뉴에는 설계 가이드, 정보 탐색 실행 화면과 정치·연예 사례 연구가 있습니다.

- **GitHub에서 읽기:** 이 README에서 설치 과정과 문제 해결 방법을 바로 읽을 수 있습니다.
- **디자인된 가이드 보기:** 저장소 전체를 내려받아 [index.html](index.html)을 본인 컴퓨터의 웹브라우저에서 여세요. 추가 페이지의 `assets/`와 상대 링크를 유지해야 합니다. 문서 읽기는 별도 서버나 빌드가 필요하지 않습니다. 정보 탐색 화면의 사례 데이터 로딩은 GitHub Pages 또는 아래 로컬 서버에서 사용하세요.
- HTML 페이지는 명령어 복사 버튼, 제공자 탭, 단계 체크와 문제 해결 아코디언을 제공합니다. 명령은 사용자가 본인의 Ubuntu 터미널에서 실행합니다.

공식 자료 확인일: **2026-10-18**. 실제 Ubuntu에서 Hermes를 설치하거나 공급자 계정으로 로그인한 실기 검증을 의미하지는 않습니다. 제공자 메뉴, 모델 이름, 계정 자격, 요금·한도는 변경될 수 있으므로 최신 공식 문서를 확인하세요.

## 텔레그램·웹 UI 연결 가이드

기본 설치와 첫 대화를 마친 뒤 다음 HTML 페이지를 브라우저에서 여세요. 메인 설치 페이지의 상단 메뉴와 첫 화면 바로가기에서도 각 안내로 이동할 수 있습니다.

| 안내 | 내용 |
| --- | --- |
| [텔레그램 연결](telegram.html) | BotFather 봇 생성, 숫자 사용자 ID 허용, 게이트웨이 실행, 문제 해결 |
| [웹 UI 비교와 공통 준비](web-ui.html) | 후보 비교, 인기도 기준, Hermes API 키, Ubuntu Docker 네트워크와 API 점검 |
| [Open WebUI 연결](open-webui.html) | Docker 실행, 관리자 연결 설정, 모델 선택 |
| [NextChat 연결](nextchat.html) | BASE_URL 설정, 사용자 지정 모델, 화면 접속 암호 |
| [LobeHub 연결](lobechat.html) | 구 LobeChat의 현재 Compose 설치, OpenAI 호환 제공자, 사설 IP 허용 |

**선정 기준과 확인일: 2026-10-24.** 비교한 오픈소스 웹 UI 후보 중 공개 GitHub 저장소의 누적 별 수 상위 3개를 골랐습니다. 이는 실제 사용자 수나 Hermes 연동 점유율을 뜻하지 않습니다.

1. [Open WebUI](https://github.com/open-webui/open-webui): 156,589개
2. [NextChat](https://github.com/ChatGPTNextWeb/NextChat): 88,884개
3. [LobeHub](https://github.com/lobehub/lobehub): 83,451개

AnythingLLM, LibreChat, Hermes WebUI, Hugging Face Chat UI도 비교 페이지에 소개했습니다. 별 수는 GitHub 공개 API의 `stargazers_count` 조회값이며 이후 바뀔 수 있습니다. 내장 `hermes dashboard`는 별도 선택지로 소개합니다.

추가 안내는 [Hermes Telegram 문서](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram), [Hermes API 서버 문서](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server), [Open WebUI 연동 문서](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui), 각 UI의 공식 문서·소스를 확인해 작성했습니다. NextChat와 LobeHub는 OpenAI 호환 엔드포인트 설정을 조합한 안내입니다. 실제 설치·로그인 및 모든 부가 기능의 호환성을 검증한 것은 아닙니다.

웹 UI 3개는 Hermes와 Docker Engine이 같은 Ubuntu에 있는 구성입니다. Docker 브리지 주소에 Hermes API를 바인딩하고 `host.docker.internal`을 매핑하는 공통 준비를 먼저 따르세요. 각 UI의 환경 파일은 저장소 밖에 보관합니다.

## 정보 탐색 서비스 설계

[서비스 설계 가이드](service-design.html)에서는 Hermes를 자체 UI로 여러 사용자가 쓰는 정보 탐색 서비스로 만들기 위한 설계 제안을 다룹니다.

- 사용자 대상·자료 범위·규모에 관한 가정과 결정 항목
- 기능 요구사항과 완료 기준, 사용자 흐름과 화면 구성 예시
- 서비스 API·영속 대기열·사용자별 Hermes 실행 환경의 책임 분리
- 계정·데이터·메모리·도구·네트워크 격리와 근거 수집·검증
- 자체 API 계약 초안, 실행·이벤트·취소·장애 복구
- 데이터 모델·보존·예산·관측, 단계별 개발과 출시 평가

기본안은 초대형 공개 웹 탐색 MVP입니다. 사용자 10명·동시 작업 3개 등의 수치는 논의를 위한 제안이며 측정 결과나 확정 요구사항이 아닙니다. 현재 저장소에는 초대 토큰 로그인·조사 API·SQLite 작업 큐·Hermes 어댑터를 갖춘 로컬 파일럿이 있습니다. 외부 공개 운영을 위한 컨테이너 격리·OIDC·TLS·비용 집계는 아직 없으며, 운영 서비스는 GitHub Pages와 별도로 구축해야 합니다. Hermes 공식 기능과 이 서비스에 제안한 설계는 본문에서 구분합니다.

## 정보 탐색 에이전트 실행

[조사 화면](research.html)에서 기존 정치·연예 사례를 체험하고, 로컬 서버에 로그인해 사용자별 이력·작업 취소·근거가 연결된 보고서를 사용할 수 있습니다.

```bash
# 저장소 루트, Python 3.11 이상 · Ubuntu/Linux
python -m research_service.server add-user alice
python -m research_service.server serve
```

초대 토큰으로 `http://127.0.0.1:8787/research.html`에 로그인합니다. 체험 모드는 기존 편집 사례를 읽습니다. 실제 조사는 준비된 Hermes 소스·Python 환경, 모델 API와 Tavily 키를 설정한 뒤 실행합니다. [설정·도구·API·검증 안내](research_service/README.md)를 참고하세요. GitHub Pages에는 사례 체험과 가이드만 배포되며 비밀 키·조사 DB·사용자 기록을 게시하지 않습니다. 정기 실행이나 자동 시작은 설정하지 않았습니다.

## 정치·연예 뉴스 사례 연구

추상적인 서비스 설계를 실제 결과로 연결하기 위해 2026-10-25 KST 기준의 수동 웹 리서치 사례를 추가했습니다.

| 페이지 | 내용 |
| --- | --- |
| [사례 비교와 결과](case-studies.html) | 분야별 3개 이슈, 요구사항 비교, 조사 방법·지표의 한계 |
| [정치·정책 사례](case-politics.html) | CPTPP 연내 신청 지시, 규제합리화, 군사당국회담 제안 |
| [연예·문화 사례](case-entertainment.html) | BIFF 수상 결과, MAMA 후보 콘텐츠·행사 일정, TWS 발매 공지 |

- [핵심 주장 20개와 출처 레코드 12개](data/news-case-studies-2026-10-25.json)
- [회귀 입력과 기대 동작 20개](data/news-evaluation-2026-10-25.json)

실제 원문을 열람해 편집한 참고 결과이며, Hermes 자동 실행 결과나 성능 평가가 아닙니다. 전체 뉴스의 순위·대표성·정치적 균형을 측정한 표본도 아닙니다. 공식 발표·배경 자료·언론 보도를 구분하고, 원문의 공개 날짜와 사건 날짜·예정 상태를 따로 기록했습니다. 정부 첨부 원문도 확인했으며 원문 전체·뉴스 사진은 저장소에 재배포하지 않습니다. 회귀 입력에는 실제 사건과 구분한 합성 보안 테스트가 포함되어 있습니다.

## 0. 시작 전 준비

Ubuntu의 일반 사용자 계정에서 시작합니다. 원격 서버라면 SSH로 접속한 터미널을 사용하세요. 아래 명령은 Bash 기준입니다.

- 인터넷에 연결된 Ubuntu
- 시스템 패키지 설치용 sudo 권한
- 로그인에 사용할 내 웹브라우저
- ChatGPT 계정 또는 Gemini API 키

**중요한 작업 폴더부터 열지 마세요.**

Hermes는 파일을 바꾸거나 명령을 실행할 수 있는 에이전트입니다. 처음에는 별도의 연습 폴더에서 사용하고, 중요한 파일은 백업해 두세요. `root` 계정 대신 일반 계정으로 진행합니다.

## 1. 필수 도구 준비

패키지 목록을 새로 읽고, 설치에 필요한 도구를 준비합니다.

```bash
sudo apt update
sudo apt install -y curl git tar coreutils ca-certificates build-essential libatomic1
```

한 줄씩 실행해도 됩니다. sudo 비밀번호를 입력할 때 글자가 표시되지 않는 것은 정상이에요. 여기의 비밀번호는 Ubuntu 계정 비밀번호입니다.

## 2. 공식 설치기로 Hermes 설치

일반 사용자 터미널에서 아래 명령을 실행합니다.

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

**이 명령 앞에는 sudo를 붙이지 마세요.**

설치기가 Python 등 필요한 실행 환경과 Hermes를 준비합니다. Python 버전을 따로 맞추거나 가상환경을 직접 만들 필요는 없습니다. 설정 질문이 나오면 화면 안내에 따라 진행하세요.

### 실행 전에 설치 스크립트를 보고 싶다면

이 명령은 인터넷에서 받은 스크립트를 바로 실행합니다. 먼저 [공식 install.sh](https://hermes-agent.nousresearch.com/install.sh)를 열어 출처와 내용을 확인할 수 있습니다. 회사 장비에서는 소프트웨어 설치 정책도 확인하세요.

근거: [Hermes 공식 설치 문서 ↗](https://hermes-agent.nousresearch.com/docs/getting-started/installation)

## 3. 터미널에 변경 사항 적용

방금 설치한 hermes 명령을 현재 터미널에서도 찾도록 합니다.

```bash
source ~/.bashrc
```

새 터미널을 열어도 됩니다. Zsh를 사용한다면 `source ~/.zshrc`를 실행하세요.

## 4. 사용할 모델 연결

아래 명령으로 설정 메뉴를 열고, 원하는 연결 방법을 고르세요.

```bash
hermes model
```

### ChatGPT 계정으로 연결하기

별도 API 키 없이 로그인

1. **제공자 메뉴에서 ChatGPT or Codex Subscription을 선택합니다.** OpenAI API 키를 넣는 별도 경로와 구분하세요.
2. **터미널에 표시된 URL을 내 브라우저에서 엽니다.** 표시된 기기 코드를 입력하고 본인 ChatGPT 계정으로 로그인합니다. SSH 서버에 설치 중이어도 로그인은 내 컴퓨터의 브라우저에서 할 수 있어요. 직접 시작한 로그인 요청인지 확인하세요.
3. **권한 화면을 확인하고, 터미널로 돌아옵니다.** 연결이 완료되면 표시된 목록에서 사용할 Codex 모델을 선택합니다. 모델 이름을 임의로 입력하기보다 현재 목록을 사용하세요.

**로그인 성공이 무제한 사용을 뜻하지는 않아요.**

계정·플랜별 자격과 사용 한도를 확인하세요. Hermes 문서는 이 연결의 세부 요금·할당량 반영 방식을 모두 보장하지 않습니다. [OpenAI의 현재 플랜 안내](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)와 계정의 사용량 화면을 기준으로 판단하세요.

근거: [Hermes 제공자·인증 문서 ↗](https://hermes-agent.nousresearch.com/docs/integrations/providers)

### Gemini API 키로 연결하기

AI Studio / Gemini API

1. **[Google AI Studio의 API 키 페이지 ↗](https://aistudio.google.com/apikey)를 엽니다.** 본인 Google 계정으로 프로젝트와 키를 준비하세요. 과금이 필요한 경우 프로젝트의 요금·한도를 먼저 확인합니다.
2. **Hermes의 제공자 메뉴에서 More providers… → Google AI Studio를 선택합니다.**
3. **키 입력 안내에 따라 API 키를 등록합니다.** 키는 내 터미널의 설정 과정에서만 입력하세요. 키를 직접 관리한다면 Hermes는 `~/.hermes/.env`의 `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`를 사용합니다. 실제 키를 명령줄에 적으면 셸 기록에 남을 수 있어요.
4. **현재 표시되는 Gemini 모델을 선택합니다.** 선택 가능한 모델은 키와 프로젝트에 따라 달라집니다. 이미 종료된 모델명을 오래된 글에서 복사하지 마세요.

**Gemini 앱의 Pro 구독과 API 사용은 구분해야 해요.**

이 가이드는 AI Studio API 키를 이용합니다. Hermes에는 소비자용 Google AI Pro/Ultra 구독 로그인 경로가 문서화되어 있지 않습니다. API 무료 한도나 프로젝트 과금을 확인하세요. 에이전트는 한 번의 요청에도 모델을 여러 번 호출할 수 있습니다.

근거: [Hermes Gemini 가이드](https://hermes-agent.nousresearch.com/docs/guides/google-gemini) · [Google API 결제 안내 ↗](https://ai.google.dev/gemini-api/docs/billing)

이미 설치 중에 연결했다면 다시 설정할 필요는 없습니다. 새 제공자를 추가할 때는 대화 안의 `/model`이 아니라 터미널의 `hermes model`을 사용하세요.

## 5. 점검하고 첫 대화 시작

진단 결과에서 필요한 항목을 확인한 뒤 Hermes를 실행합니다.

```bash
hermes doctor
```

선택 기능에 관한 경고는 기본 대화에 필요하지 않을 수 있습니다. 공급자 인증이나 실행 환경 오류가 있으면 해당 진단부터 해결하세요.

```bash
hermes
```

첫 질문 예시:

> 안녕! 한국어로 답해 줘. 파일을 바꾸거나 명령을 실행하지 말고, 네가 도와줄 수 있는 일을 간단히 설명해 줘.

**답변이 오면 기본 연결 완료!**

이제 작은 작업부터 시작하세요. 대화를 종료하려면 `/quit`을 입력할 수 있습니다.

## 안전하게 오래 사용하려면

**비밀은 저장소에 올리지 않기**

API 키, 인증 토큰, `.env`, `auth.json`을 GitHub에 올리지 마세요. `~/.hermes` 폴더 전체를 공개하거나 스크린샷에 키를 담지 않습니다.

**작은 권한과 작은 작업부터**

연습 폴더에서 시작하고 파일 변경·명령 실행 내용을 확인하세요. 중요 파일과 운영 서버 작업은 별도 검토가 필요합니다.

**모델로 전송할 내용 확인하기**

선택한 모델 서비스로 대화와 작업 맥락이 전달될 수 있습니다. 비공개 문서나 개인 정보는 서비스의 데이터 정책을 확인한 뒤 사용하세요.

**사용량과 비용 확인하기**

긴 작업은 여러 호출로 이어질 수 있습니다. 공급자 대시보드에서 할당량과 결제 상태를 확인하고, 예상하지 못한 사용량이 보이면 작업을 멈추세요.

## 자주 막히는 곳

오류에 맞는 항목을 확인하세요. 먼저 진단하고, 필요한 부분만 고칩니다.

### `hermes: command not found`가 나와요

먼저 새 터미널을 열거나 `source ~/.bashrc`를 실행하세요. 계속 못 찾는다면 현재 터미널의 PATH에 설치 위치를 넣어 확인합니다.

```bash
export PATH="$HOME/.local/bin:$PATH"
hermes doctor
```

이 export는 현재 셸에만 적용됩니다. 다른 사용자나 root로 설치했는지도 확인하세요. 진단 없이 폴더를 지우고 재설치하지 마세요.

### 설치 중 `libatomic.so.1` 오류가 나와요

최소 Ubuntu 이미지에서 필요한 시스템 라이브러리가 없을 수 있습니다. 1단계의 `libatomic1` 설치가 성공했는지 확인하고, 설치기가 알려준 재시도 명령을 따르세요. 관리자 권한이 없다면 시스템 관리자에게 패키지 설치를 요청합니다.

### ChatGPT 로그인 코드가 만료되었어요

`hermes model`을 다시 실행하고 ChatGPT/Codex 항목을 선택해 새 코드를 받으세요. 이전 코드 대신 새 코드로 직접 시작한 로그인만 승인합니다. 조직에서 기기 코드 로그인을 막았다면 [공식 문서의 Codex 브라우저 인증 안내](https://hermes-agent.nousresearch.com/docs/integrations/providers)를 확인하세요.

### Gemini 키 오류 또는 `401 / 403`이 나와요

AI Studio 키인지, 키가 유효한지, 프로젝트에 해당 모델 접근 권한이 있는지 확인하세요. `hermes model`로 설정을 다시 확인한 뒤 `hermes doctor`를 실행합니다. 오류를 공유할 때는 키와 토큰을 가리세요.

### `429` 또는 사용량 제한 메시지가 나와요

공급자 대시보드에서 요청 속도·할당량·결제 상태를 확인하세요. 무료 한도는 에이전트 작업으로 빠르게 소진될 수 있습니다. 반복 재시도보다 안내된 재설정 시간을 기다리거나, 비용을 확인한 뒤 사용 방식을 조정하세요.

### 목록에 있던 모델이 사라졌어요

모델 제공 여부는 바뀝니다. `hermes model`에서 지금 제공되는 모델을 다시 선택하세요. 오래된 모델 ID나 다른 제공자의 모델 이름을 그대로 넣지 않는 편이 안전합니다.

### 브라우저 도구만 오류가 나요

기본 대화 연결과 브라우저 기능 설치는 별개입니다. Linux 브라우저에는 추가 시스템 라이브러리가 필요할 수 있어요. `hermes doctor` 결과와 설치기의 재시도 안내를 확인하세요. 이 가이드의 패키지 목록이 모든 브라우저 기능 의존성을 포함하는 것은 아닙니다.

## 공식 자료로 더 확인하기

2026년 10월 18일 기준으로 아래 문서를 확인했습니다.
설치기, 메뉴, 인증 조건, 모델과 요금은 이후 변경될 수 있습니다.

- [Hermes 설치 문서](https://hermes-agent.nousresearch.com/docs/getting-started/installation)
- [모델 제공자·인증 방법](https://hermes-agent.nousresearch.com/docs/integrations/providers)
- [Hermes의 Google Gemini 가이드](https://hermes-agent.nousresearch.com/docs/guides/google-gemini)
- [ChatGPT 플랜으로 Codex 사용하기](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [Gemini API 결제·한도 안내](https://ai.google.dev/gemini-api/docs/billing)
- [Google AI Studio API 키](https://aistudio.google.com/apikey)

HTML 페이지는 설치 방법을 설명하는 정적 문서입니다. 로그인 정보나 API 키를 입력받지 않으며, 명령을 실행하거나 Hermes 서비스를 호스팅하지 않습니다. 단계 체크는 이 페이지를 열어 둔 동안만 유지됩니다.

## HTML 파일 구성과 접근성

- `index.html`: 기본 설치 가이드와 연동 페이지 바로가기; 설치용 JavaScript 포함
- `telegram.html`, `web-ui.html`, `open-webui.html`, `nextchat.html`, `lobechat.html`: 추가 연결 안내 페이지
- `service-design.html`: 다중 사용자 정보 탐색 서비스의 요구사항·설계 제안
- `case-studies.html`, `case-politics.html`, `case-entertainment.html`: 실제 원문에 기반한 사례 연구
- `data/news-*.json`: 주장·출처와 미실행 회귀 평가 입력
- `assets/case-studies.js`: 고정 사례 카드의 분야별 필터
- `assets/guide.css`: 모든 HTML 페이지가 사용하는 공통 색상·타이포그래피·반응형 스타일
- `assets/guide.js`: 추가 페이지의 복사·목차 기능
- `assets/navigation.js`: 공통 웹 UI 펼침 메뉴의 Escape·바깥 클릭·포커스 처리; JavaScript 없이도 펼치기와 링크 이동 가능
- 모든 페이지에 동일한 로고·상단 메뉴·푸터 적용
- 모바일·데스크톱 반응형 레이아웃
- 외부 폰트·라이브러리·분석 도구·백엔드 없이 작동
- 로그인 정보나 API 키를 수집하지 않음
- 단계 체크는 현재 페이지 세션 동안만 유지되며 저장하지 않음
- 탭은 클릭 또는 좌우 화살표, Home, End로 이동
- HTTPS/localhost에서는 Clipboard API를 우선 사용하고, 제한된 경우 복사 대체 경로 또는 직접 선택 안내 제공
- JavaScript가 꺼져도 모든 설치 내용과 두 제공자 안내를 읽을 수 있음
- 인쇄 시 두 제공자 안내를 모두 표시
- `prefers-reduced-motion` 지원

비공개 저장소도 비밀 보관 장소로 사용하지 마세요. **API 키, 인증 토큰, `.env`, `auth.json`, `~/.hermes`의 개인 설정이나 대화 데이터를 커밋하지 마세요.**

이 가이드는 Nous Research, OpenAI 또는 Google의 공식 문서가 아닙니다. 제품명은 해당 소유자의 상표입니다. 저장소의 기존 [Apache License 2.0](LICENSE)을 유지합니다.

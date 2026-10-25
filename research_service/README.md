# 정보 탐색 에이전트 로컬 파일럿

정치·연예 조사를 위한 자체 UI, 초대 토큰 로그인, 사용자별 이력, SQLite 영속 작업 큐와 Hermes 실행 어댑터입니다. **정기 실행·cron·외부 배포를 설정하지 않습니다.** 서버를 직접 시작한 동안, 사용자가 등록한 작업만 실행합니다.

## 바로 실행

Ubuntu/Linux, Python 3.11 이상에서 저장소 루트 기준으로 실행합니다. 체험·API 서버에는 외부 Python 패키지가 필요 없습니다.

```bash
python -m research_service.server add-user alice
python -m research_service.server serve
```

첫 명령이 출력하는 초대 토큰을 안전하게 보관하고 `http://127.0.0.1:8787/research.html`에서 로그인합니다. 사용자를 추가하면 이력·작업·결과 다운로드가 계정별로 나뉩니다. 같은 브라우저에서는 한 계정만 로그인합니다. 다른 브라우저 프로필로 계정을 나누어 검증할 수 있습니다. 토큰은 비밀번호와 같습니다. DB에는 SHA-256 해시만 보관합니다. 토큰 재출력은 지원하지 않습니다.

```bash
python -m research_service.server add-user bob
python -m research_service.server disable-user alice
```

비활성 계정은 신규 요청·이력·기존 세션 접근이 즉시 거부되고, 진행 작업은 워커에서 중단됩니다. 초대 토큰을 교체하려면 기존 계정을 비활성화한 뒤 새 계정을 발급합니다. 계정 삭제·토큰 회전 UI는 아직 없습니다.

- `Ctrl+C`로 서버와 실행 작업을 중단합니다. 재부팅 시 자동 시작하지 않습니다.
- 기본 DB는 `.research/research.sqlite3`입니다. 이 디렉터리는 Git에서 제외하며 비밀 값·작업 데이터는 공개하지 않습니다.
- 다른 DB: `python -m research_service.server --db /private/path/research.sqlite3 serve --port 8788`
- 동일 DB는 파일 잠금으로 서버 하나만 사용합니다. 대기 작업은 다음 수동 시작 때 이어집니다. 실행 도중 비정상 종료된 작업은 `interrupted`이며 비용 중복을 피하기 위해 자동 재실행하지 않습니다.
- GitHub Pages의 [사례 체험](https://s2dream.github.io/hermes-guide/research.html)은 로그인·백엔드 없이 기존 편집 데이터를 읽습니다. 실제 검색이나 Hermes 실행을 가장하지 않습니다.

## 실제 Hermes 조사 설정

1. [Hermes 공식 Python 연동 안내](https://hermes-agent.nousresearch.com/docs/guides/python-library)에 따라 **별도 Hermes 소스와 실행 환경을 준비**합니다. Hermes를 이 서버의 `requirements.txt`에 넣어 설치하지 않습니다. 설치 안내의 `source ./activate`로 준비한 환경에서 `command -v python`과 소스의 절대 경로를 확인하세요.
2. 그 환경에서 PDF를 사용한다면 이 저장소의 `research_service/requirements-pdf.txt`를 `python -m pip install -r /absolute/path/to/hermes-guide/research_service/requirements-pdf.txt`로 설치합니다(pypdf 6.21.2 검증). HWPX·HTML·텍스트는 표준 라이브러리로 읽습니다. HWP 바이너리·스캔 PDF·동영상·OCR·로그인 필요 자료는 지원하지 않습니다.
3. 저장소 루트에서 환경 파일을 복사하고 **실제 값은 서버의 Git 제외 경로에만 입력**합니다.

```bash
mkdir -p .research
chmod 700 .research
cp research_service/config.example.env .research/runtime.env
chmod 600 .research/runtime.env
# 편집기에서 .research/runtime.env의 경로·모델·키를 실제 값으로 변경
set -a
source .research/runtime.env
set +a
python -m research_service.server doctor
python -m research_service.server serve
```

`HERMES_SOURCE`는 `run_agent.py`가 있는 디렉터리, `HERMES_PYTHON`은 해당 소스를 실행할 준비된 Python의 절대 경로입니다. 모델은 공급자에서 사용할 수 있는 ID로 직접 지정합니다. 기본은 OpenRouter + `OPENROUTER_API_KEY`; 직접 OpenAI 사용 시 `RESEARCH_PROVIDER=openai`와 `OPENAI_API_KEY`를 설정합니다. 현재 어댑터는 이 두 명시적인 API 키 방식만 지원하며 개인 Hermes의 OAuth·구독·프로필·`.env`를 자동으로 가져오지 않습니다.

`doctor`는 환경 값 유무와 경로만 확인합니다. 의존 패키지·모델 권한·잔액·API 연결 성공까지 확인한 결과가 아닙니다. 로그인한 뒤 실제 조사 방식을 선택하고 작은 질문으로 첫 작업을 실행해 확인하세요. 실패 시 보고서를 성공으로 표시하지 않습니다. 모델·검색 공급자 요금이 발생할 수 있습니다. 실제 비용 집계는 아직 없으므로 공급자 계정에서 지출 한도를 설정하세요.

## 세 도구와 보고서 검증

Hermes 내장 도구를 교체하지 않고 `guide_research`라는 사용자 정의 toolset을 등록합니다. 모델에 노출된 실제 도구 이름이 다음 세 개와 정확히 같은지 실행 전에 검사하고, 다르면 거부합니다.

| 도구 | 구현 | 제한 |
| --- | --- | --- |
| `research_search` | Tavily 뉴스 검색 API | 4회 × 결과 최대 5개, 질문의 시작·종료일 전달 |
| `research_extract` | 공개 HTTPS HTML·텍스트·PDF 읽기 | 원문 레코드·ID·조회 시각·게시일(명시 시)·해시 기록 |
| `read_document` | 공개 HTTPS HWPX·PDF 첨부 읽기 | 로컬 파일 접근 없음; ZIP/XML 크기 제한 |

앞서 소개한 Hermes 내장 `web_search`·`web_extract`와 용도가 같습니다. 이번 파일럿은 서버가 실제 읽은 본문을 직접 기록할 수 있도록 별도 어댑터를 사용합니다. 검색 결과 요약은 출처로 등록하지 않습니다. 첨부 링크는 웹 원문의 링크 목록을 통해 찾아 읽을 수 있습니다. 분야별 공식 기록 검색·내부 문서·X·브라우저 자동화는 아직 없습니다.

- 총 원문 읽기 8회, 파일당 4 MiB, 모델에 전달·검증하는 본문은 앞 24,000자. 긴 문서의 뒤쪽은 읽지 못할 수 있으며 `truncated`로 표시합니다.
- PDF 100쪽·HWPX 압축 해제 64 MiB 제한. 원문 이동마다 HTTPS와 공개 IP를 재검사하고, DNS 결과를 소켓에 고정합니다. 내부·루프백·메타데이터·IPv4 mapped IPv6 주소, URL 자격 증명, 443 이외 포트를 차단합니다. 쿠키·프록시 환경은 원문 읽기에 전달하지 않습니다.
- Hermes 대화 12회전, 출력 최대 5,000토큰, 작업 전체 300초. 임의 셸·파일·메모리·브라우저·cron 도구를 노출하지 않습니다.
- Linux 실행 프로세스는 가상 메모리 2 GiB, CPU 시간 240초, 개별 출력 파일 16 MiB로 제한합니다. 한도 초과는 실패로 처리합니다. 컨테이너의 사용자·네트워크 격리를 대체하지 않습니다.
- 매 작업을 별도 프로세스, 빈 Hermes home·작업 디렉터리에서 실행합니다. 개인 기록·MCP·프로필·SOUL·백그라운드 리뷰를 사용하지 않습니다. 모델이 도구 호출을 통해 일정을 등록할 수 없습니다.
- 모델은 JSON으로 주장·상태·사건일·발췌를 반환합니다. 서비스는 출처 ID가 실제 수집 목록에 있는지, 8~150자의 발췌가 본문에 정확히 있는지, 출처당 발췌 총량이 500자 이하인지 검사합니다. 모델이 보낸 출처 URL을 신뢰하지 않습니다.
- 근거가 없으면 `insufficient_evidence`; 파싱·인용 검사에 실패하면 `failed`. 기계 검사가 주장 의미의 적합성·진실성·정치적 균형을 보증하지 않습니다. 요약·상태·날짜의 의미 검수와 원문 최신성 확인이 필요합니다.
- 게시일은 페이지의 명시적인 메타데이터가 없으면 `null`이며 사건일로 채우지 않습니다. 기간 필터는 검색 공급자에 전달하는 조건입니다. 원문의 사건이 그 기간에 속하는지는 모델과 검수자가 별도로 확인해야 합니다.
- 원문 전체는 실행 중 임시 영역·메모리에서만 처리하고 최종 DB에는 선택한 짧은 발췌와 메타데이터를 저장합니다. 자동 보존 만료·삭제는 아직 없습니다. 토큰·가격·성능·자동 정확도는 미측정입니다.

## API

브라우저는 같은 출처의 API와 HttpOnly·SameSite=Strict 세션 쿠키를 사용합니다. CLI는 `Authorization: Bearer <초대 토큰>`으로 접근할 수 있습니다. 요청 사용자 ID·내부 Hermes 경로·도구 설정은 API 입력으로 받지 않습니다.

| 메서드·경로 | 동작 |
| --- | --- |
| `GET /api/health` | 설정 여부·미설정 환경 이름·정기 실행 없음 |
| `POST /api/login` | `{"token":"..."}` → 12시간 세션 |
| `POST /api/logout` | `{}` → 현재 세션 폐기 |
| `GET /api/me` | 현재 계정 |
| `GET /api/research` | 본인 최근 100개 작업 |
| `POST /api/research` | 아래 JSON + `Idempotency-Key`로 작업 생성 |
| `GET /api/research/{id}` | 본인 상태·진행 기록·결과 |
| `POST /api/research/{id}/cancel` | `{}` → 중단 요청 |
| `GET /api/research/{id}/download` | 같은 소유권 검사 후 JSON 다운로드 |

```json
{
  "question": "이번 주 정책 발표에서 제안과 확정된 내용을 구분해줘.",
  "domain": "politics",
  "mode": "live",
  "start_date": "2026-10-19",
  "end_date": "2026-10-25"
}
```

`domain`: `politics` / `entertainment`, `mode`: `demo` / `live`. 질문 5~2,000자. 요청 키는 사용자별 8~128자이며 같은 키·같은 내용은 같은 작업, 다른 내용은 409입니다. 서버에 재시도해도 기존 결과를 재사용합니다. UI는 응답을 받지 못한 요청의 키를 유지하여 같은 내용을 재시도할 때 중복 생성을 막습니다. 탭을 닫았다면 이력부터 확인하세요.

단일 워커가 순서대로 실행합니다. 사용자당 대기·실행 작업 5개, 전체 20개까지입니다. 상태는 `queued → running → completed/insufficient_evidence/failed`; 취소는 `cancelling → cancelled`입니다. 실제 자식 프로세스 종료를 기다린 후 `cancelled`로 바뀝니다. 큐에서 취소한 작업은 즉시 `cancelled`입니다. 이벤트는 상태 조회 시 함께 제공하며 SSE는 아직 없습니다.

## 검증과 남은 범위

```bash
python -m unittest discover -s tests -v
```

PDF 테스트는 pypdf가 설치된 환경에서 실행하며, 없으면 그 테스트만 건너뜁니다. 브라우저 검증은 Playwright·Chromium을 준비한 환경에서 `python tests/check_research_ui.py`로 실행할 수 있습니다.

권한 분리·계정 철회·멱등성·입력 제한·큐·중단·복구·인용 변조·공개 URL 검사·첨부 추출·Hermes 어댑터 계약을 자동 테스트합니다. 모의 Hermes와 모의 네트워크를 쓰는 테스트를 실제 유료 모델·Tavily 통합 실행으로 해석하지 마세요. 기존 `data/news-evaluation-2026-10-25.json`의 20개 뉴스 평가 입력은 여전히 실제 Hermes에 실행하지 않은 평가셋입니다.

현재 구현은 **외부 공개 전의 로컬 파일럿**입니다. OS 계정·네트워크·자원까지 나누는 컨테이너 샌드박스는 아니며, 문서 파서와 모델 라이브러리도 같은 호스트 사용자 권한으로 실행합니다. 공개 다중 사용자 운영 전에는 사용자별 컨테이너, 네트워크 egress 정책, CPU·메모리 제한, TLS·OIDC·CSRF 검토, DB 백업·보존·삭제, 사용량·금액 한도, 관측·실제 뉴스 품질 평가를 추가해야 합니다. [운영 설계](../service-design.html)의 출시 조건은 계속 유효합니다.

정기 실행이 필요하면 **대상 질문·출처·주기·시간대·비용 한도·중단 방법·결과 전달 위치를 제시하고 사용자 허가를 받은 뒤** 별도로 설정합니다. 이 코드에 스케줄러·자동 시작·예약 워크플로는 없습니다.

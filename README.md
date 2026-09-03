# Balance AI — 수면·운동 건강관리 에이전트

최종 제출용 요구사항 매핑과 스크린샷은 [SUBMISSION.md](SUBMISSION.md), 발표 대본과 예상 질문은 [PRESENTATION.md](PRESENTATION.md)에서 확인할 수 있습니다.

수면 시간과 운동 시간을 날짜별로 기록하고, 시계열 요약을 주입받은 AI 코치에게 내 데이터에 근거한 질문을 할 수 있는 웹 서비스입니다. 120일치 재현 가능한 가상 데이터 생성, CRUD, 대화 자동 저장/불러오기, 이중 추세 차트, CSV 다운로드와 다크 모드를 지원합니다.

> 이 서비스의 답변은 건강 습관 관리를 위한 참고 정보이며 의료 진단을 대신하지 않습니다.

## 주요 기능과 데이터 흐름

1. 프론트엔드가 Firestore의 `data` 컬렉션을 CRUD합니다.
2. `/api/data/summary`가 기간, 평균·최대·최소, 최근 7일 변화, 건강 균형 달성률을 계산합니다.
3. `/api/chat`이 요약을 시스템 프롬프트에 삽입해 Google Gemini를 호출합니다.
4. 사용자 질문과 AI 답변은 `conversations` 컬렉션에 자동 저장됩니다.
5. 프론트에서 저장된 대화를 선택하면 전체 메시지를 다시 표시합니다.

데이터 문서는 과제의 `(date, value, memo)` 구조를 따릅니다.

```json
{
  "date": "2026-09-03",
  "value": { "sleep_hours": 7.4, "exercise_minutes": 42 },
  "memo": "저녁 산책 후 숙면"
}
```

`data/{autoId}`에는 위 필드와 생성 시각을, `conversations/{autoId}`에는 `title`, `messages`, `created_at`, `updated_at`을 저장합니다. 수면은 0–24시간, 운동은 0–1,440분, 미래 날짜와 빈 메시지는 Pydantic에서 거부합니다.

## 기술 스택

- Backend: Python 3.10+, FastAPI, Pydantic, Firebase Admin SDK, Google Gen AI SDK
- Database: Firebase Firestore
- Frontend: HTML, CSS, JavaScript(Canvas API), 프레임워크 없음
- Deploy: Render(백엔드), Vercel(프론트엔드)

## 로컬 실행

### 1. Firebase 준비

Firebase Console에서 프로젝트와 Firestore Database를 생성하고, 프로젝트 설정 → 서비스 계정에서 새 비공개 키를 발급합니다. 키 JSON은 Git에 커밋하지 마세요.

### 2. 백엔드

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

`.env`에 실제 키를 입력합니다. 서비스 계정은 한 줄 JSON 문자열 또는 파일 경로 중 하나를 사용합니다.

```dotenv
GEMINI_API_KEY=AI Studio에서_발급받은_키
GEMINI_MODEL=gemini-2.5-flash
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
# FIREBASE_SERVICE_ACCOUNT_PATH=C:/secure/service-account.json
ALLOWED_ORIGINS=http://localhost:5500,https://your-app.vercel.app
ALLOWED_ORIGIN_REGEX=https://[a-z0-9-]+-your-vercel-team\.vercel\.app
```

API는 `http://localhost:8000`, Swagger UI는 `http://localhost:8000/docs`에서 확인합니다. 가상 데이터는 화면 버튼 또는 다음 요청으로 한 번 생성합니다. 같은 날짜는 중복 생성하지 않으므로 다시 실행해도 안전합니다.

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/data/seed
```

### 3. 프론트엔드

`frontend/config.js`의 주소가 `http://localhost:8000`인지 확인하고 정적 서버를 실행합니다.

```powershell
cd frontend
py -m http.server 5500
```

브라우저에서 `http://localhost:5500`에 접속합니다. HTML 파일을 직접 열면 브라우저 보안 정책 때문에 요청이 제한될 수 있습니다.

### 테스트

```powershell
backend\.venv\Scripts\python.exe -m pytest -q
```

배포 사이트 제출용 화면을 다시 생성하려면 개발 의존성을 설치한 뒤 저장소 루트에서 자동화 스크립트를 실행합니다.

```powershell
cd backend
pip install -r requirements-dev.txt
cd ..
python scripts/capture_submission.py
```

## API

| Method | Endpoint | 설명 |
|---|---|---|
| POST / GET | `/api/data` | 기록 추가 / 날짜순 조회 |
| PUT / DELETE | `/api/data/{id}` | 기록 수정 / 삭제 |
| GET | `/api/data/summary` | 프롬프트용 통계와 최근 추세 |
| POST | `/api/data/seed` | 고정 시드 기반 가상 데이터 120일 생성 |
| GET | `/api/data/export.csv` | CSV 다운로드 |
| POST / GET | `/api/conversations` | 대화 직접 저장 / 목록 조회(messages 포함) |
| GET / DELETE | `/api/conversations/{id}` | 특정 대화 전체 조회 / 삭제 |
| POST | `/api/chat` | 요약 주입 → Gemini 호출 → 대화 자동 저장 |

정적 경로인 `/summary`, `/seed`, `/export.csv`는 `/{record_id}`보다 먼저 선언해 충돌하지 않습니다.

## 배포

### Render 백엔드

1. GitHub 저장소를 연결하고 Root Directory를 `backend`로 지정합니다.
2. 저장소의 `render.yaml`을 이용하거나 Build Command `pip install -r requirements.txt`, Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT`를 입력합니다.
3. `GEMINI_API_KEY`, `GEMINI_MODEL`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `ALLOWED_ORIGINS`를 환경 변수로 등록합니다. 필요하면 `ALLOWED_ORIGIN_REGEX`로 본인 Vercel 팀의 미리보기 도메인만 허용합니다. API 키와 서비스 계정 JSON은 Secret으로 관리합니다.
4. `https://<render-service>.onrender.com/docs`에서 Swagger를 확인합니다.

무료 인스턴스는 첫 요청 때 콜드스타트가 발생할 수 있어 화면에 최대 1분 대기 안내를 표시합니다.

### Vercel 프론트엔드

1. 같은 저장소를 Import하고 Root Directory를 `frontend`로 지정합니다.
2. Framework Preset은 `Other`로 설정합니다. 저장소의 `vercel.json`이 Build Command `npm run build`와 Output Directory `dist`를 지정합니다.
3. 환경 변수 `API_BASE_URL=https://<render-service>.onrender.com`을 등록합니다. 빌드 시 `build-config.js`가 이 값을 `config.js`에 반영합니다.
4. 발급된 Vercel 주소를 백엔드의 `ALLOWED_ORIGINS`에 추가하고 재배포합니다.

### 배포 URL (배포 후 교체)

- Frontend: `https://3-2-son884999-oss-projects.vercel.app`
- Backend API: `https://balance-ai-api.onrender.com`
- Swagger: `https://balance-ai-api.onrender.com/docs`

## 제출 스크린샷 체크리스트

- 대시보드: 요약 카드와 차트, 실제 질문과 AI 답변이 한 화면에 보이게 캡처
- 건강 기록: 새 기록 추가 또는 수정/삭제 직후 목록과 완료 알림이 보이게 캡처
- 대화 기록: 이전 상담 카드 목록 및 선택 후 복원된 메시지가 보이게 캡처

## 보안·비용 안내

키 파일과 `.env`는 `.gitignore`에 포함되어 있습니다. 브라우저에는 Gemini/Firebase 비밀 키를 넣지 않습니다. Gemini 호출은 최근 메시지 12개, 출력 700토큰으로 제한했습니다. CORS는 등록한 로컬/배포 출처만 허용하며, 운영 환경에서 `*` 사용은 권장하지 않습니다.

### 과제 명세와 Gemini 사용

과제의 “GPT API” 항목을 특정 OpenAI 제품이 아니라 생성형 AI API 요구사항으로 인정받을 수 있는지 담당자에게 확인하는 것이 안전합니다. 구현 원리는 동일합니다. Firestore 요약을 시스템 지시문에 주입하고 Gemini가 해당 컨텍스트에 근거해 답변하며, 결과를 다시 Firestore에 저장합니다.

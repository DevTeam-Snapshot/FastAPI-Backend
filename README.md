# FastAPI Backend

- 담당자: AI 11기 2팀 Snapshot 정서호
- 숙박업 소상공인을 위한 생성형 AI 광고 제작 서비스의 백엔드 저장소입니다.
- React와 REST API로 통신하고, 모델 서버와 gRPC로 통신합니다.
- 광고 기획 세션, 원본 이미지, 광고 초안, 처리 상태와 이미지 URL을 관리합니다.

## 1. 주요 기능

V2에서는 다음 흐름을 구현했습니다.

```text
React
  → 광고 기획 세션 생성
  → 모델과 대화하며 광고 기획서 작성
  → 원본 이미지 업로드
  → 완성된 기획서 확정
  → A·B·C 광고 초안 생성
  → 초안 선택 또는 1회 재생성
  → 완성된 광고 이미지 다운로드
```

광고 기획 질문은 다음 순서로 진행합니다.

```text
lodging_type
→ lodging_information
→ selling_points
→ lodging_service
→ mood
→ color_preference
→ target_audience
→ ad_copy
→ complete
```

광고 초안은 세 가지 방향으로 생성합니다.

```text
room    : selling_points를 활용한 객실·전망·공간 중심
emotion : mood와 color_preference를 활용한 감성·분위기 중심
benefit : lodging_service를 활용한 서비스·혜택 중심
```

초안 상태는 다음과 같이 관리합니다.

```text
pending → processing → completed
                     ↘ failed
```

모델 또는 외부 서비스 오류로 최초 생성에 실패하면 실패한 1회차 초안만 같은 `draft_id`로 다시 시도합니다. 이 경우 사용자의 재생성 기회는 소모하지 않습니다.

## 2. Docker Compose 실행 방법

이 저장소의 `compose.yaml`은 FastAPI와 PostgreSQL을 함께 실행합니다.

### 환경변수 파일 생성

```bash
cp .env.example .env
cp .postgres.env.example .postgres.env
```

실제 비밀번호와 API 키는 Git에 올리지 않습니다.

### 실행

```bash
docker compose up --build -d
```

### 상태 및 로그 확인

```bash
docker compose ps
docker compose logs -f backend
```

### 접속 주소

```text
Swagger UI: http://127.0.0.1:9000/docs
백엔드 상태: http://127.0.0.1:9000/health
모델 상태: http://127.0.0.1:9000/api/model/health
```

현재 Compose는 백엔드와 PostgreSQL만 실행합니다. 실제 모델 연동은 메인 저장소의 Compose에서 진행합니다.

### 종료

```bash
docker compose down
```

PostgreSQL 데이터는 Docker Volume에 저장되어 유지됩니다.

## 3. API

현재 다음 기능을 제공합니다.

- 광고 기획 세션 생성 및 조회
- 원본 이미지 업로드
- 사용자 답변 전달 및 다음 질문 요청
- 완성된 광고 기획서 저장
- A·B·C 광고 초안 생성 및 재생성
- 최초 초안 생성 실패 재시도
- 광고 초안 조회 및 최종 선택
- 원본 이미지와 결과 이미지 조회
- 완성된 광고 이미지 PNG 다운로드
- 백엔드 및 모델 서버 상태 확인

상세 URL, 필드 설명과 Request·Response Body는 [`document/api-spec.html`](document/api-spec.html) 및 팀 Notion의 백엔드 API 명세에서 관리합니다.

## 4. 기술 스택

| 구분 | 기술 |
| --- | --- |
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL 17.11, SQLAlchemy, Alembic, Psycopg |
| Image | Pillow |
| Model communication | gRPC, Protobuf, grpcio-status |
| Infrastructure | Docker, Docker Compose, Docker Hub, GCP VM |

## 5. 폴더 구조

```text
FastAPI-Backend/
├── alembic/
│   └── versions/
├── app/
│   ├── api/routes/
│   │   ├── health.py
│   │   ├── model_health.py
│   │   ├── planning_sessions.py
│   │   ├── planning_turns.py
│   │   ├── advertisement_drafts.py
│   │   ├── draft_downloads.py
│   │   └── image_generations.py
│   ├── clients/
│   │   ├── planning_agent.py
│   │   ├── draft_image.py
│   │   ├── grpc_draft_image.py
│   │   └── grpc_error.py
│   ├── core/
│   ├── db/
│   ├── grpc_stubs/
│   ├── models/
│   ├── schemas/
│   └── services/
├── document/
│   ├── api-spec.html
│   └── v2-model-contract-update.txt
├── Image/
├── compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 6. 주요 폴더별 역할

| 폴더 | 역할 |
| --- | --- |
| `app/api/routes/` | REST API 주소와 요청·응답 처리 |
| `app/clients/` | 모델 서버 gRPC 통신과 오류 처리 |
| `app/models/` | PostgreSQL 테이블 구조 정의 |
| `app/schemas/` | API 요청과 응답 데이터 검증 |
| `app/services/` | 기획 세션, 초안 생성 및 이미지 저장 로직 |
| `app/grpc_stubs/` | proto와 자동 생성된 gRPC 코드 |
| `alembic/` | 데이터베이스 구조 변경 이력 |
| `document/` | 백엔드 API 명세와 모델 서버 연동 계약 문서 |
| `Image/` | 원본 이미지와 생성 결과 저장 |

## 7. 이미지 저장 구조

```text
Image/
├── requests/
│   └── {session_id}/original.{확장자}
└── results/
    └── {draft_id}/generated.png
```

원본 이미지는 JPEG, PNG, WebP 형식을 지원하며 최대 크기는 25MiB입니다.

광고 초안은 `1080 × 1350` 크기의 PNG로 생성하고 검증합니다.

DB에는 이미지 파일 자체가 아닌 이미지 URL과 파일 정보를 저장합니다.

완성된 광고 초안은 다음 API를 통해 PNG 파일로 다운로드할 수 있습니다.

```text
GET /api/drafts/{draft_id}/download
```

## 8. 구현 완료 상태

- 기획 세션 생성·조회 및 최종 저장
- 이미지 업로드·검증·저장
- 모델과 대화하며 광고 기획서 작성
- A·B·C 광고 초안 생성·조회·선택
- 세션당 성공한 재생성 1회 제한
- 최초 생성 모델 오류 재시도
- 시스템 오류와 사용자 재생성 기회 분리
- 초안 생성 상태 및 오류 관리
- 기획 대화와 이미지 생성 gRPC 클라이언트 구현
- 구조화된 gRPC 오류 처리
- 실제 V2 모델 서버와 gRPC 통합
- React부터 FastAPI와 모델 서버까지 전체 연동
- 생성 이미지 저장 및 React 화면 출력
- 광고 이미지 PNG 다운로드
- PostgreSQL 및 Docker Compose 실행

최종 백엔드 기능 구현을 완료했습니다.

추후 개선 과제:

- 사용자 인증 및 권한 검사
- 외부 파일 스토리지 적용
- 모델 요청 큐와 재시도 정책 고도화
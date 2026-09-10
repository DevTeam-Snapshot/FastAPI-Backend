# FastAPI Backend

- 담당자: AI 11기 2팀 Snapshot 정서호
- 숙박업 소상공인을 위한 생성형 AI 광고 이미지 제작 서비스의 백엔드 저장소입니다.
- React와 REST API로 통신합니다.
- OpenAI 이미지 생성 API를 사용하는 모델 서버와 gRPC로 통신합니다.
- 이미지 생성 요청, 파일 저장, PostgreSQL 기록 및 처리 상태를 관리합니다.

## 1. 주요 기능

현재 v1에서는 다음 흐름을 구현합니다.

```text
React
  └─ 숙소 정보 + 광고 문구 + 추가 지시사항 + 원본 이미지
        ↓ REST API
FastAPI
  ├─ 원본 이미지 저장
  ├─ PostgreSQL 요청 기록
  ├─ 처리 상태 관리
  └─ 이미지 모델 서버 호출
        ↓ gRPC
Image Model Server
  └─ OpenAI Image API를 이용한 광고 이미지 생성
        ↓ PNG bytes
FastAPI
  ├─ 결과 이미지 저장
  ├─ 결과 URL 및 completed 상태 기록
  └─ React에 생성 결과 반환
```

이미지 생성 상태는 다음 순서로 관리합니다.

```text
pending → processing → completed
                     ↘ failed
```

## 2. Docker Compose 실행 방법

이 저장소의 `compose.yaml`은 FastAPI 백엔드와 PostgreSQL을 함께 실행합니다.

### 환경변수 파일 생성

다음 예시 파일을 복사해 실제 환경변수 파일을 생성합니다.

```bash
cp .env.example .env
cp .postgres.env.example .postgres.env
```

`.env`와 `.postgres.env`의 데이터베이스 이름, 사용자 및 비밀번호는 동일하게 설정해야 합니다.

실제 비밀번호와 API 키는 Git에 올리지 않습니다.

### 백엔드와 PostgreSQL 실행

```bash
docker compose up --build -d
```

컨테이너 상태를 확인합니다.

```bash
docker compose ps
```

백엔드 로그를 확인합니다.

```bash
docker compose logs backend
```

### 접속 주소

```text
Swagger UI: http://127.0.0.1:9000/docs
백엔드 상태: http://127.0.0.1:9000/health
모델 상태: http://127.0.0.1:9000/api/model/health
```

모델 서버가 실행되지 않은 경우 모델 상태 확인 및 이미지 생성 요청에서 HTTP 503이 반환되는 것이 정상입니다.

### 컨테이너 종료

```bash
docker compose down
```

PostgreSQL 데이터는 Docker Volume에 저장되므로 일반적인 `docker compose down`으로는 삭제되지 않습니다.

## 3. API

| Method | 경로 | 역할 |
| --- | --- | --- |
| GET | `/health` | FastAPI 실행 상태 확인 |
| GET | `/api/model/health` | 이미지 모델 서버의 gRPC Health Check |
| POST | `/api/image-generations` | 이미지 생성 요청 및 처리 |
| GET | `/api/image-generations/{generation_id}` | 생성 요청 상태 및 결과 조회 |
| GET | `/images/requests/...` | 저장된 원본 이미지 조회 |
| GET | `/images/results/...` | 저장된 결과 이미지 조회 |

### 이미지 생성 요청

`multipart/form-data` 형식으로 요청합니다.

| 필드 | 형식 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `hotel_description` | string | 필수 | 숙소명, 주소, 유형, 특징 등 숙소 정보 |
| `ad_copy` | string | 필수 | 광고 이미지에 반영할 광고 문구 |
| `additional_instructions` | string | 선택 | 분위기, 색상, 배치 등 추가 지시사항 |
| `image` | file | 필수 | 숙소 원본 이미지 |

지원하는 이미지 형식:

```text
JPEG, PNG, WebP
```

기본 최대 업로드 크기:

```text
25MB
```

### 이미지 생성 응답

```json
{
  "id": "생성 요청 UUID",
  "hotel_description": "숙소 정보",
  "ad_copy": "광고 문구",
  "additional_instructions": "추가 지시사항",
  "original_filename": "hotel.webp",
  "original_image_url": "/images/requests/UUID/original.webp",
  "generated_image_url": "/images/results/UUID/generated.png",
  "status": "completed",
  "error_message": null,
  "created_at": "생성 시각",
  "updated_at": "수정 시각"
}
```

DB에는 이미지 파일 자체가 아닌 이미지 URL을 저장합니다. 실제 파일은 `Image` 폴더에 저장합니다.

## 4. 기술 스택

### Backend

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| Python | 3.12 | 백엔드 애플리케이션 개발 |
| FastAPI | 0.141.1 | REST API 서버 개발 |
| Uvicorn | 0.52.4 | FastAPI 애플리케이션 실행 |
| Pydantic Settings | 2.15.0 | 환경변수 로드 및 검증 |
| python-multipart | 0.0.32 | 이미지 및 Form 데이터 처리 |

### Database

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| PostgreSQL | 17.11 | 이미지 생성 요청, 상태 및 URL 저장 |
| SQLAlchemy | 2.0.52 | Python ORM 및 DB 처리 |
| Alembic | 1.19.1 | 데이터베이스 스키마 변경 이력 관리 |
| Psycopg | 3.3.5 | SQLAlchemy와 PostgreSQL 연결 |

### Model communication

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| gRPC | 1.78.0 | FastAPI와 이미지 모델 서버 통신 |
| Protobuf | 6.33.4 | gRPC 요청 및 응답 계약 정의 |
| grpcio-tools | 1.78.0 | proto 기반 Python stub 생성 |

### Infrastructure

| 기술 | 사용 목적 |
| --- | --- |
| Docker | 운영체제와 관계없는 실행 환경 구성 |
| Docker Compose | 백엔드와 PostgreSQL 실행 |
| Docker Hub | 멀티플랫폼 백엔드 이미지 공유 |
| GCP VM | 통합 테스트 및 배포 |

## 5. 폴더 구조

```text
FastAPI-Backend/
├── alembic/
│   ├── versions/
│   │   ├── 4e693f85ad1d_create_test_items_table.py
│   │   ├── 7e852317dc01_drop_test_items_table.py
│   │   ├── 3717430aca14_create_image_generations_table.py
│   │   └── 855b4583d0fc_replace_prompt_with_advertisement_fields.py
│   ├── env.py
│   ├── script.py.mako
│   └── README
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── model_health.py
│   │       └── image_generations.py
│   │
│   ├── clients/
│   │   └── model.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── grpc_stubs/
│   │   ├── hotel_advertisement_image.proto
│   │   ├── hotel_advertisement_image_pb2.py
│   │   └── hotel_advertisement_image_pb2_grpc.py
│   │
│   ├── models/
│   │   └── image_generation.py
│   │
│   ├── schemas/
│   │   └── image_generation.py
│   │
│   └── services/
│       ├── image_generation_service.py
│       └── image_storage.py
│
├── Image/
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   └── test_health.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── .postgres.env.example
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── README.md
└── requirements.txt
```

각 Python 패키지 폴더에는 해당 폴더를 Python 패키지로 인식시키는 `__init__.py`가 포함됩니다.

## 6. 주요 파일별 역할

### 애플리케이션과 API

| 파일 | 역할 |
| --- | --- |
| `app/main.py` | FastAPI 애플리케이션, CORS, API 라우터 및 이미지 정적 경로를 등록합니다. |
| `app/api/router.py` | 기능별 API 라우터를 하나로 통합합니다. |
| `app/api/routes/health.py` | FastAPI 실행 상태 확인 API를 정의합니다. |
| `app/api/routes/model_health.py` | 이미지 모델 서버의 gRPC 상태 확인 API를 정의합니다. |
| `app/api/routes/image_generations.py` | 이미지와 광고 정보를 받고 모델 호출 및 결과 반환 흐름을 처리합니다. |

### 모델 서버 통신

| 파일 | 역할 |
| --- | --- |
| `app/clients/model.py` | 이미지 bytes와 광고 정보를 모델 서버에 전달하고 PNG bytes를 받습니다. |
| `app/grpc_stubs/hotel_advertisement_image.proto` | FastAPI와 이미지 모델 서버가 사용할 gRPC 계약입니다. |
| `app/grpc_stubs/hotel_advertisement_image_pb2.py` | proto 메시지의 Python 코드입니다. |
| `app/grpc_stubs/hotel_advertisement_image_pb2_grpc.py` | gRPC 서비스와 클라이언트 stub의 Python 코드입니다. |

`pb2.py`와 `pb2_grpc.py`는 자동 생성 파일이므로 직접 수정하지 않습니다.

### 이미지 및 상태 관리

| 파일 | 역할 |
| --- | --- |
| `app/services/image_storage.py` | 원본 이미지와 생성 이미지를 폴더에 저장하고 URL을 생성합니다. |
| `app/services/image_generation_service.py` | 처리 상태 변경, 생성 결과 저장 및 실패 상태 기록을 담당합니다. |
| `app/models/image_generation.py` | `image_generations` 테이블의 SQLAlchemy 모델을 정의합니다. |
| `app/schemas/image_generation.py` | 이미지 생성 API의 응답 형식과 상태 값을 정의합니다. |

### 환경설정과 데이터베이스

| 파일 | 역할 |
| --- | --- |
| `app/core/config.py` | `.env`의 DB, 모델 서버, 이미지 저장 설정을 읽고 검증합니다. |
| `app/db/base.py` | SQLAlchemy 모델이 상속하는 공통 `Base`를 정의합니다. |
| `app/db/session.py` | PostgreSQL 엔진과 요청별 DB 세션을 관리합니다. |
| `alembic/env.py` | DB 주소 및 SQLAlchemy 모델 정보를 Alembic과 연결합니다. |
| `alembic/versions/` | 데이터베이스 구조 변경 이력을 저장합니다. |

### 실행 환경

| 파일 | 역할 |
| --- | --- |
| `Dockerfile` | FastAPI 백엔드 이미지를 생성합니다. |
| `compose.yaml` | FastAPI와 PostgreSQL을 함께 실행합니다. |
| `requirements.txt` | Python 패키지와 버전을 관리합니다. |
| `.env.example` | 백엔드 환경변수 작성 예시입니다. |
| `.postgres.env.example` | PostgreSQL 컨테이너 환경변수 작성 예시입니다. |
| `.dockerignore` | Docker 이미지에 포함하지 않을 파일을 지정합니다. |
| `.gitignore` | Git에서 추적하지 않을 파일과 이미지를 지정합니다. |

## 7. 이미지 저장 구조

```text
Image/
├── requests/
│   └── {request_id}/
│       └── original.{확장자}
└── results/
    └── {request_id}/
        └── generated.png
```

실제 이미지는 Git에 올리지 않으며 `Image/.gitkeep`만 저장소에 포함합니다.

## 8. 현재 테스트 상태

확인된 항목:

- 이미지 업로드 형식 및 최대 용량 검사
- 원본 이미지 폴더 저장
- PostgreSQL 요청 기록
- `pending → processing → failed` 상태 변경
- 모델 서버 미연결 시 HTTP 503 반환
- gRPC 송수신 최대 크기 32MiB 적용
- Docker 멀티플랫폼 이미지 빌드
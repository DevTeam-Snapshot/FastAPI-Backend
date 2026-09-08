# FastAPI-backend
- 담당자: AI 11기 2팀(SnapShot) 정서호
- AI 광고 제작 서비스의 백엔드 저장소
- React와는 REST API로 통신합니다.
- vLLM 모델 서버와는 gRPC로 통신합니다.

## Docker Compose 실행 방법

FastAPI 백엔드와 PostgreSQL을 Docker Compose로 함께 실행합니다.
`.env`와 `.postgres.env`의 DB 사용자, 비밀번호, 데이터베이스 이름은 동일해야 합니다. (노션 참고)

### 백엔드와 PostgreSQL 실행

```bash
docker compose up --build -d
```

### 컨테이너 종료

```bash
docker compose down
```

- 브라우저에서 http://127.0.0.1:9000/docs 접속합니다.
- PostgreSQL 컨테이너 및 DB 환경변수 설정이 필요합니다. (.env 설정)

## 1. 기술 스택
### Backend

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| Python | 3.12 | 백엔드 애플리케이션 개발 언어 |
| FastAPI | 0.141.1 | REST API 서버 개발 |
| Uvicorn | 0.52.4 | FastAPI 애플리케이션 실행 |
| Pydantic | 2.13.5 | API 요청·응답 데이터 검증 |
| Pydantic Settings | 2.15.0 | 환경변수 로드 및 설정값 검증 |
| python-multipart | 0.0.32 | 이미지 및 폼 데이터 업로드 처리 |

### Database

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| PostgreSQL | 17.11 | 회원, 숙소, 생성 기록 및 피드백 저장 |
| SQLAlchemy | 2.0.52 | Python 코드에서 PostgreSQL 데이터 처리 |
| Alembic | 1.19.1 | 데이터베이스 스키마 변경 이력 관리 |
| Psycopg | 3.3.5 | SQLAlchemy와 PostgreSQL 연결 |

### Infrastructure

| 기술 | 사용 목적 |
| --- | --- |
| Docker | 운영체제와 관계없는 백엔드 실행 환경 구성 |
| Docker Hub | 팀 공통 Docker 이미지 공유 |
| GCP VM | 백엔드 및 AI 서비스 테스트·배포 |

## 2. 폴더 구조

기능별 책임을 분리해 유지보수와 확장이 쉽도록 구성했습니다.

```text
FastAPI-Backend/
├── alembic/
│   ├── versions/
│   │   └── 4e693f85ad1d_create_test_items_table.py
│   ├── env.py
│   ├── script.py.mako
│   └── README
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── model_health.py
│   │       ├── integration.py
│   │       └── test_items.py
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   └── model.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── grpc_stubs/
│   │   ├── __init__.py
│   │   ├── vllm_engine.proto
│   │   ├── vllm_engine_pb2.py
│   │   └── vllm_engine_pb2_grpc.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── test_item.py
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── integration_test.py
│       └── test_item.py
│
├── tests/
│   ├── __init__.py
│   └── test_health.py
│
├── .dockerignore
├── .gitignore
├── alembic.ini
├── Dockerfile
├── README.md
└── requirements.txt
```
- *test 관련 파일은 실제 도메인 모델 확정 후 제거하거나 교체 예정*

## 3. 파일별 역할

### 애플리케이션과 API

| 파일 | 역할 |
| --- | --- |
| `app/main.py` | FastAPI 애플리케이션을 생성하고 CORS와 통합 라우터를 등록합니다. |
| `app/api/router.py` | 기능별 라우터를 하나로 모아 `main.py`에 전달합니다. |
| `app/api/routes/health.py` | 백엔드 실행 상태를 확인하는 API를 정의합니다. |
| `app/api/routes/test_items.py` | 테스트 데이터를 저장하고 조회하는 임시 POST·GET API를 정의합니다. |

### 환경설정과 데이터베이스

| 파일 | 역할 |
| --- | --- |
| `app/core/config.py` | `.env`의 환경변수를 읽고 자료형을 검증합니다. |
| `app/db/base.py` | 모든 SQLAlchemy 모델이 상속하는 공통 `Base`를 정의합니다. |
| `app/db/session.py` | DB 접속 URL, SQLAlchemy 엔진 및 요청별 세션을 관리합니다. |
| `app/models/test_item.py` | 임시 `test_items` 테이블의 SQLAlchemy 모델을 정의합니다. |
| `app/schemas/test_item.py` | 테스트 API의 요청 및 응답 데이터 형식을 검증합니다. |

### 데이터베이스 마이그레이션

| 파일 | 역할 |
| --- | --- |
| `alembic.ini` | Alembic의 실행 경로와 로그 등 기본 설정을 관리합니다. |
| `alembic/env.py` | 환경변수의 DB 주소와 SQLAlchemy 모델 정보를 Alembic에 연결합니다. |
| `alembic/versions/` | DB 구조의 변경 이력을 마이그레이션 파일로 저장합니다. |
| `alembic/script.py.mako` | 새로운 마이그레이션 파일을 생성할 때 사용하는 템플릿입니다. |

### 테스트 및 실행 환경

| 파일 | 역할 |
| --- | --- |
| `tests/test_health.py` | 상태 확인 API 테스트를 작성할 예정인 파일입니다. |
| `requirements.txt` | 필요한 Python 패키지와 버전을 관리합니다. |
| `Dockerfile` | FastAPI 백엔드 Docker 이미지 생성 방법을 정의합니다. |
| `.dockerignore` | Docker 이미지에서 제외할 파일과 폴더를 지정합니다. |
| `.gitignore` | Git에서 추적하지 않을 파일과 폴더를 지정합니다. |
| 각 폴더의 `__init__.py` | 해당 폴더를 Python 패키지로 인식할 수 있게 합니다. |

---

프로젝트 진행에 따라 내용 추가 예정.
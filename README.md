# FastAPI-backend
- 담당자: AI 11기 2팀(SnapShot) 정서호
- AI 광고 제작 서비스의 백엔드 저장소
- 본 저장소의 FastAPI 백엔드는 프론트엔드, 데이터베이스 및 AI 모델 서버를 연결합니다.

## Docker 실행
```text
docker pull westhooo/snapshot-backend:0.1.0
docker run --rm -p 8000:8000 westhooo/snapshot-backend:0.1.0
```
- 본 버전은 실행을 위한 최소 단위의 DockerFile 입니다.(0904)
- 브라우저에서 http://localhost:8000으로 접속합니다.

## 1. 기술 스택
### Backend

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| Python | 3.12 | 백엔드 애플리케이션 개발 언어 |
| FastAPI | 0.141.1 | REST API 서버 개발 |
| Uvicorn | 0.52.4 | FastAPI 애플리케이션 실행 |
| python-multipart | 0.0.32 | 이미지 및 폼 데이터 업로드 처리 |

### Database

| 기술 | 버전 | 사용 목적 |
| --- | --- | --- |
| MariaDB | 12.3.3 | 회원, 숙소, 생성 기록 및 피드백 저장 |
| SQLAlchemy | 2.0.52 | Python 코드에서 MariaDB 데이터 처리 |
| Alembic | 1.19.1 | 데이터베이스 스키마 변경 이력 관리 |
| PyMySQL | 1.2.0 | SQLAlchemy와 MariaDB 연결 |

### Infrastructure

| 기술 | 사용 목적 |
| --- | --- |
| Docker | 운영체제와 관계없는 백엔드 실행 환경 구성 |
| Docker Hub | 팀 공통 Docker 이미지 공유 |
| GCP VM | 백엔드 및 AI 서비스 테스트·배포 |

## 2. 폴더 구조
- FastAPI 백엔드의 역할을 명확하게 분리하고, 기능 확장과 테스트를 쉽게 하기 위해 계층별 구조를 사용합니다.
- 목적별 파일을 분리하여 main.py에 객체를 가져오는 방식으로 진행

```text
FastAPI-Backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── api/
│       ├── __init__.py
│       ├── router.py
│       └── routes/
│           ├── __init__.py
│           └── health.py
│
├── tests/
│   ├── __init__.py
│   └── test_health.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

현재 구조는 초기(9월 3일 ver.)구조 입니다.

## 3. 파일별 역할

### 애플리케이션 파일

| 파일 | 역할 |
| --- | --- |
| `app/main.py` | FastAPI 애플리케이션을 생성하고 통합 라우터를 등록하는 시작점입니다. |
| `app/api/router.py` | 기능별 API 라우터를 하나로 모아 `main.py`에 전달합니다. |
| `app/api/routes/health.py` | 백엔드 서버가 정상적으로 실행 중인지 확인하는 상태 확인 API를 정의합니다. |

### 테스트 파일

| 파일 | 역할 |
| --- | --- |
| `tests/test_health.py` | 상태 확인 API가 정상적인 응답을 반환하는지 테스트합니다. |

### 환경 및 실행 파일

| 파일 | 역할 |
| --- | --- |
| `requirements.txt` | 백엔드 실행에 필요한 Python 패키지와 버전을 관리합니다. |
| `Dockerfile` | FastAPI 백엔드 Docker 이미지를 만드는 방법을 정의합니다. |
| `.dockerignore` | Docker 이미지에 복사하지 않을 파일과 폴더를 지정합니다. |
| `.gitignore` | Git 저장소에서 추적하지 않을 파일과 폴더를 지정합니다. |

---

프로젝트 진행에 따라 내용 추가 예정.

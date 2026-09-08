# FastAPI 백엔드 인수인계

## 1. 저장소 정보

- 팀 백엔드 저장소: https://github.com/DevTeam-Snapshot/FastAPI-Backend
- 개인 Fork: https://github.com/tjgh8167/FastAPI-backend
- 모델 저장소: https://github.com/DevTeam-Snapshot/vLLM-Model
- 백엔드 통합 브랜치: `5-vllm-grpc-client`
- 백엔드 작업 커밋: `c625ec9`
- 팀 저장소 main 확인 커밋: `23d8693`

팀장님은 팀 저장소의 `main` 브랜치를 클론하면 됩니다.

```bash
git clone https://github.com/DevTeam-Snapshot/FastAPI-Backend.git
cd FastAPI-Backend
```

## 2. 현재 구현된 기능

- FastAPI 서버와 Swagger
- React 개발 서버용 CORS
- PostgreSQL 연결
- SQLAlchemy ORM
- Alembic 마이그레이션
- 테스트 데이터 POST·GET API
- React·FastAPI·DB 통합 테스트 API
- vLLM gRPC HealthCheck 클라이언트
- vLLM gRPC Generate 클라이언트
- Qwen chat template 적용
- `output_ids` 문자열 디코딩
- `<think>...</think>` 영역 제거
- 모델 연결 실패 시 HTTP 503 처리
- FastAPI와 PostgreSQL용 `compose.yaml`

현재 실제 vLLM 서버와의 최종 Generate 연동은 아직 검증하지 못했습니다.

## 3. 통신 구조

```text
React
  │ REST API
  ▼
FastAPI
  ├── SQLAlchemy ORM ──> PostgreSQL
  └── gRPC ────────────> vLLM Qwen3-0.6B
```

사용 포트:

```text
React:                8080
FastAPI VM 접속 포트:   9000
FastAPI 컨테이너 포트:   8000
PostgreSQL:           5432
vLLM 호스트 테스트 포트:  15051
vLLM 컨테이너 포트:      50051
```

## 4. 환경변수 준비

실제 비밀번호와 토큰은 Git이나 이 문서에 작성하지 않습니다.

프로젝트 최상단에 `.postgres.env`와 `.env`가 필요합니다.

환경변수에 대한 정보는 Notion의 Backend 라이브러리를 참고해주시면 됩니다.

백엔드 Compose는 컨테이너 내부의 `DB_HOST`를 `postgres`로 자동 변경합니다.

## 5. FastAPI와 PostgreSQL 실행

백엔드 저장소에서 실행합니다.

```bash
docker compose up --build -d
```

이 명령으로 다음 작업이 수행됩니다.

1. PostgreSQL 실행
2. PostgreSQL HealthCheck
3. FastAPI 이미지 빌드
4. Alembic 마이그레이션
5. FastAPI 실행

상태 확인:

```bash
docker compose ps
```

정상 기준:

```text
snapshot-postgres: healthy
snapshot-backend: Up
```

백엔드 로그:

```bash
docker compose logs --tail 100 backend
```

FastAPI 확인:

```bash
curl http://127.0.0.1:9000/health
```

정상 결과:

```json
{"status":"ok"}
```

Swagger:

```text
http://127.0.0.1:9000/docs
```

## 6. 모델 서버 실행

모델 담당자가 모델 저장소에서 실행합니다.

```bash
docker compose \
  -f docker-compose.grpc.yml \
  up --build -d
```

모델 로그:

```bash
docker compose \
  -f docker-compose.grpc.yml \
  logs -f llm-service
```

최초 실행은 vLLM 이미지와 Qwen 모델을 내려받으므로 시간이 오래 걸릴 수 있습니다.

## 7. 백엔드와 모델 네트워크 연결

백엔드와 모델은 서로 다른 Compose로 실행되기 때문에 기본 네트워크가 다릅니다.

백엔드 `.env`는 다음 값을 사용해야 합니다.

```env
MODEL_GRPC_TARGET=llm-service:50051
```

환경변수를 수정했다면 백엔드를 다시 생성합니다.

```bash
docker compose up -d --force-recreate backend
```

그다음 백엔드를 모델 네트워크에 연결합니다.

```bash
docker network connect \
  vllm-model-network \
  snapshot-backend
```

`already exists in network` 오류가 나오면 이미 연결된 상태이므로 다시 실행하지 않아도 됩니다.

백엔드에 적용된 모델 주소 확인:

```bash
docker exec snapshot-backend \
  printenv MODEL_GRPC_TARGET
```

정상 출력:

```text
llm-service:50051
```

## 8. 모델 HealthCheck

```bash
curl -i \
  http://127.0.0.1:9000/api/model/health
```

성공 결과:

```http
HTTP/1.1 200 OK
```

```json
{"healthy":true}
```

`503 Service Unavailable`이 나오면 아래 문제 해결 내용을 확인합니다.

## 9. 테스트 데이터 준비

현재 통합 API는 PostgreSQL의 `test_items` 테이블을 사용합니다.

기존 데이터 조회:

```bash
curl http://127.0.0.1:9000/api/test-items
```

데이터가 없다면 등록합니다.

```bash
curl -X POST \
  http://127.0.0.1:9000/api/test-items \
  -H "Content-Type: application/json" \
  -d '{"text":"1번 텍스트"}'
```

## 10. 백엔드·DB·모델 통합 테스트

```bash
curl -X POST \
  http://127.0.0.1:9000/api/integration-test \
  -H "Content-Type: application/json" \
  -d '{
    "question":"오션뷰 호텔 광고 문구를 만들어줘",
    "index":1
  }'
```

성공 결과 형태:

```json
{
  "index": 1,
  "db_text": "1번 텍스트",
  "model_answer": "vLLM이 실제로 생성한 광고 문구"
}
```

`db_text`와 `model_answer`가 함께 반환되면 백엔드·DB·모델 연동 성공입니다.

## 11. React 연동 테스트

프론트엔드 담당자가 같은 VM에서 React 컨테이너를 실행합니다.

React는 다음 백엔드 API를 호출합니다.

```text
POST /api/integration-test
```

요청 데이터:

```json
{
  "question": "오션뷰 호텔 광고 문구를 만들어줘",
  "index": 1
}
```

React 화면에 `db_text`와 `model_answer`가 모두 표시되면 전체 연동 성공입니다.

## 12. 자주 발생할 수 있는 문제

### Git pull 시 untracked 파일 충돌

오류:

```text
The following untracked working tree files would be overwritten
```

기존 파일을 삭제하지 말고 stash로 보관합니다.

```bash
git stash push \
  --include-untracked \
  -m "GCP VM 기존 파일 백업"
```

```bash
git pull --ff-only
```

바로 `git stash pop`을 실행하면 최신 파일과 다시 충돌할 수 있으므로 필요한 파일만 비교합니다.

### Docker 권한 오류

오류:

```text
permission denied while trying to connect to the docker API
```

확인:

```bash
groups
ls -l /var/run/docker.sock
```

docker 그룹 권한이 없다면:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

공용 VM에서 `chmod 666 /var/run/docker.sock`은 사용하지 않습니다.

### PostgreSQL 이미지 Pull 취소

오류:

```text
failed to extract layer
context canceled
```

먼저 재시도합니다.

```bash
docker pull postgres:17.11
docker compose up --build -d
```

반복되면 확인합니다.

```bash
df -h /var/lib/docker
docker system df
```

### 컨테이너 이름 충돌

오류:

```text
container name is already in use
```

기존 상태를 먼저 확인합니다.

```bash
docker ps -a
```

다른 팀원이 사용하는 컨테이너인지 확인한 뒤 처리합니다.

### PostgreSQL 연결 오류

확인:

```bash
docker compose ps
docker compose logs postgres
docker compose logs backend
```

다음 값이 서로 같은지 확인합니다.

```text
POSTGRES_USER = DB_USER
POSTGRES_PASSWORD = DB_PASSWORD
POSTGRES_DB = DB_NAME
```

### 모델 API가 503을 반환

확인 순서:

1. vLLM 컨테이너가 실행 중인지 확인
2. 모델 로딩이 완료됐는지 로그 확인
3. `MODEL_GRPC_TARGET=llm-service:50051`인지 확인
4. 백엔드와 모델이 같은 네트워크에 있는지 확인
5. 포트가 `50051`인지 확인

```bash
docker ps
docker network inspect vllm-model-network
docker exec snapshot-backend printenv MODEL_GRPC_TARGET
```

### PyTorch 관련 경고

다음 메시지는 백엔드에서 모델이 아닌 토크나이저만 사용하기 때문에 발생하는 경고입니다.

```text
None of PyTorch, TensorFlow, or Flax have been found
```

FastAPI가 정상 실행된다면 이 경고 때문에 PyTorch를 추가로 설치하지 않아도 됩니다.

### VS Code 포트가 9001로 표시

Mac 또는 Windows의 9000번이 이미 사용 중이면 VS Code가 VM 9000번을 로컬 9001번으로 자동 전달할 수 있습니다.

이 경우 접속 주소:

```text
http://127.0.0.1:9001/docs
```

VM 내부 FastAPI 포트는 여전히 9000번입니다.

`localhost`와 `127.0.0.1`은 모두 자기 컴퓨터의 loopback 주소이므로 둘 다 정상입니다.

## 13. 종료와 데이터 보존

백엔드와 PostgreSQL 종료:

```bash
docker compose down
```

PostgreSQL 데이터는 `snapshot-postgres-data` 볼륨에 남습니다.

다음 명령은 DB 볼륨까지 삭제하므로 임의로 실행하지 않습니다.

```bash
docker compose down -v
```

## 14. 현재 남은 작업

- 실제 vLLM `HealthCheck()` 성공 확인
- 실제 vLLM `Generate()` 응답 확인
- Backend와 vLLM의 Docker 네트워크 연결 확인
- React에서 통합 API 호출
- React 화면에서 `db_text`, `model_answer` 확인
- 전체 연동 성공 후 Docker 이미지 태그 고정

## 15. 최종 성공 기준

다음 네 항목이 모두 성공해야 합니다.

```text
GET  /health                 → 200, status=ok
GET  /api/test-items         → PostgreSQL 데이터 반환
GET  /api/model/health       → 200, healthy=true
POST /api/integration-test   → db_text와 model_answer 반환
```
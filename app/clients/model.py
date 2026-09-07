# 모델 클라이언트
class ModelClient:
    # 답변 생성
    async def generate(self, question: str) -> str:
        # 아직 모델이 없으니 질문한 내용 그대로 답변으로 나올 수 있도록 테스트 설정
        return(
            f"질문을 정상적으로 받았습니다: {question}"
            )

# 클라이언트 객체 생성
model_client = ModelClient()
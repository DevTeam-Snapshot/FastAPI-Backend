from transformers import AutoTokenizer
import grpc
from app.core.config import get_settings
from app.grpc_stubs import (
    vllm_engine_pb2,
    vllm_engine_pb2_grpc
)
import re
from uuid import uuid4

# 모델 클라이언트
class ModelClient:
    def __init__(self):
        settings = get_settings()
        self.grpc_target = settings.model_grpc_target
        self.timeout = settings.model_timeout_seconds
        self.model_name  = settings.model_name
        self.model_revision = settings.model_revision
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            revision = self.model_revision
        )

    # 질문에 대한 답변 형식 출력 
    def build_prompt(self, question: str) -> str:
        messages = [
            {
                "role" : "user",
                "content" : question
            }
        ]
 
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize = False,
            add_generation_prompt = True,
            enable_thinking = False
        )

        return prompt

    # vLLM 서버가 정상 작동 중인지 확인
    async def health_check(self) -> bool:
        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target
            ) as channel:
                
                # VLLM 클라이언트 생성
                stub = vllm_engine_pb2_grpc.VllmEngineStub(channel)
                request = vllm_engine_pb2.HealthCheckRequest()

                # 모델 서버에 HealthCheck 요청 전송
                response = await stub.HealthCheck(
                    request,
                    timeout = self.timeout
                )

                return response.healthy
        except grpc.aio.AioRpcError as error:
            raise ConnectionError(
                f"vLLM gRPC 서버 연결 실패: {error.code().name}"
            ) from error
        

    def remove_thinking(self, answer: str) -> str:
        cleaned_answer = re.sub(
            r"<think>.*?</think>",
            "",
            answer,
            flags=re.DOTALL
        )
        return cleaned_answer.strip()

    # vLLM 모델 서버에 질문 -> 답변 생성
    async def generate(self, question: str) -> str:
        # 위에서 정의한 템플릿 적용
        prompt = self.build_prompt(question)
        request = vllm_engine_pb2.GenerateRequest(
            request_id = str(uuid4()),
            text = prompt,

            sampling_params = vllm_engine_pb2.SamplingParams(
                temperature = 0.0,
                max_tokens = 80,
                skip_special_tokens = True,
                seed = 42
            ),

            stream = False
        )

        # 답변 생성
        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target
            ) as channel:

                stub = vllm_engine_pb2_grpc.VllmEngineStub(channel)
                response_stream = stub.Generate(
                    request,
                    timeout = self.timeout
                )

                output_ids = None

                async for response in response_stream: 
                    # complete가 나오면 결과 생성
                    if response.HasField("complete"):
                        output_ids = response.complete.output_ids
                        break
                # complete가 없다면
                if output_ids is None:
                    raise RuntimeError(
                        "vLLM 서버에서 최종 생성 결과를 받지 못했습니다."
                    )

                model_answer = self.tokenizer.decode(
                    output_ids,
                    skip_special_tokens = True
                )

                # thinking 영역이 남아있다면 제거 (만약)
                return self.remove_thinking(model_answer)
            
        except grpc.aio.AioRpcError as error:
            raise ConnectionError(
                f"vLLM Generate 요청 실패: {error.code().name}"
            ) from error

# 클라이언트 객체 생성
model_client = ModelClient()
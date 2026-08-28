# Implementation Plan: AI 블로그 생성 기능 연결

## Overview

이 구현 계획은 Marblo의 AI 블로그 생성 기능을 실제로 동작하게 만드는 것을 목표로 합니다. AWS Bedrock Converse API를 통해 Nova Lite(기본) 또는 Claude 모델에 연결하고, 사진 분석→생성 파이프라인을 자동화하며, 사용자의 작성 의도(topic/additional_context)를 프롬프트에 반영합니다.

**핵심 변경 영역:**
- `app/config.py` — Bedrock 설정 추가
- `app/utils/s3_client.py` — S3 바이트 조회 헬퍼 추가
- `app/utils/ai_client.py` — Bedrock Converse 경로 구현
- `app/routers/photos.py` — 재사용 가능한 분석 로직 리팩터링
- `app/routers/marblo.py` — 파이프라인 자동화 + 의도 전달
- `app/services/generation_service.py` — 의도 반영 + 템플릿 폴백 제거

**전제 조건:**
- Bedrock Nova Lite 접근이 us-east-1에서 확인됨 (converse 호출 테스트 완료)
- EC2 IAM 역할에 `bedrock:InvokeModel` 권한 포함 (terraform/main.tf 참조)

## Tasks

- [x] 1. Bedrock 설정 추가 (`app/config.py`)
  - [x] 1.1 `Settings` 클래스에 Bedrock 관련 필드 추가
    - `use_bedrock: bool` (기본값 `true`) — Bedrock 경로 활성화 플래그
    - `bedrock_model_id: str` (기본값 `amazon.nova-lite-v1:0`) — 생성 모델 ID
    - `bedrock_max_tokens: int` (기본값 `2048`) — 요청당 최대 출력 토큰
    - `bedrock_region: str` (기본값 `us-east-1`) — Bedrock 리전
    - 환경 변수(`USE_BEDROCK`, `BEDROCK_MODEL_ID`, `BEDROCK_MAX_TOKENS`, `BEDROCK_REGION`)에서 읽도록 구현
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 9.1, 9.2, 9.3_

- [x] 2. S3 바이트 조회 헬퍼 추가 (`app/utils/s3_client.py`)
  - [x] 2.1 `S3Client.get_object_bytes(s3_key: str) -> Optional[bytes]` 메서드 구현
    - `s3_client.get_object(Bucket=..., Key=s3_key)["Body"].read()`로 메모리 조회
    - 기존 재시도 로직(`MAX_RETRIES`, 지수 백오프) 적용
    - 실패 시 `None` 반환 + 로그
    - _Requirements: 3.1_

- [x] 3. AIClient Bedrock Converse 경로 구현 (`app/utils/ai_client.py`)
  - [x] 3.1 `_get_bedrock_client()` 메서드 구현
    - boto3 `bedrock-runtime` 클라이언트 지연 초기화
    - 명시적 자격 증명 없이 IAM 역할/기본 체인 사용 (`boto3.client("bedrock-runtime", region_name=...)`)
    - _Requirements: 1.1, 1.3_
  - [x] 3.2 `_invoke_converse(messages, system_prompt) -> Optional[str]` 구현
    - Converse API 호출 (`bedrock.converse(modelId=..., messages=..., inferenceConfig={maxTokens: ...})`)
    - 재시도 대상 오류(`ThrottlingException`, `ServiceUnavailableException`, `InternalServerException`, `ModelTimeoutException`) 정의
    - 최대 3회 지수 백오프 재시도
    - `asyncio.to_thread()`로 동기 boto3 호출 오프로딩
    - _Requirements: 1.2, 1.4, 2.4, 9.2_
  - [x] 3.3 `_extract_text(converse_response) -> str` 헬퍼 구현
    - `output.message.content`의 모든 text 블록을 순서대로 결합하여 반환
    - _Requirements: 1.2_
  - [ ]* 3.4 `_extract_text` 속성 테스트 작성 (Hypothesis)
    - **Property 1: Converse 응답 텍스트 추출 보존**
    - **Validates: Requirements 1.2**

- [x] 4. AIClient `analyze_photo` 시그니처 변경
  - [x] 4.1 `analyze_photo(image_bytes: bytes, image_format: str, photo_title: Optional[str]) -> Optional[dict]` 시그니처로 변경
    - 기존 `image_url: str` 파라미터 제거
    - Converse `image` 블록 형식으로 비전 호출 (`{"image": {"format": ..., "source": {"bytes": image_bytes}}}`)
    - 분석 프롬프트를 system prompt로 전달, 이미지+요청을 messages로 전달
    - 응답 텍스트를 JSON 파싱하여 분석 dict 반환, 파싱 실패 시 `None`
    - _Requirements: 3.1_
  - [x] 4.2 기존 `_call_claude` 기반 호출을 `_invoke_converse` 기반으로 전환
    - `generate_blog_post`, `analyze_writing_style`, `call_claude` 메서드 내부에서 `_invoke_converse` 사용
    - `use_bedrock=False`일 때 기존 직접 Anthropic API 경로 유지 (하위 호환)
    - _Requirements: 1.1, 2.4_

- [x] 5. Checkpoint — config 및 AIClient 단위 테스트 확인
  - boto3 모킹으로 `_invoke_converse` 재시도 로직 검증
  - 설정 기본값/환경 변수 오버라이드 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. photos.py 분석 로직 리팩터링
  - [x] 6.1 `analyze_photo_record(photo, db, s3_client, ai_client) -> bool` 내부 함수 도입
    - `analysis_status="analyzing"` 상태 갱신
    - `s3_client.get_object_bytes(photo.s3_key)`로 이미지 바이트 조회
    - `ai_client.analyze_photo(image_bytes, photo.file_format, photo.file_name)` 호출
    - 결과 `None`이면 `status="failed"` + 로그 + `False` 반환
    - 결과를 `PhotoMetadata` 필드로 매핑 (description, location, price, date, category, confidence_scores)
    - 확인 안 된 항목은 `None`으로 저장 (부분 성공)
    - 기존 레코드가 있으면 upsert
    - `status="completed"` + `True` 반환
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  - [ ] 6.2 기존 `analyze_photo` 엔드포인트가 `analyze_photo_record` 호출하도록 리팩터링
    - 공개 URL 대신 S3 바이트 사용
    - _Requirements: 3.1_
  - [ ]* 6.3 분석 결과→PhotoMetadata 매핑 속성 테스트 작성
    - **Property 2: 분석 결과→PhotoMetadata 매핑 필드 보존**
    - **Validates: Requirements 3.2, 3.5**

- [ ] 7. marblo.py 파이프라인 + 의도 전달
  - [ ] 7.1 `generate_post_mvp` 함수에서 `posting_intent` 구성
    - `posting_intent = {"topic": request.topic, "additional_context": request.additional_context}`
    - _Requirements: 5.1_
  - [ ] 7.2 요청된 사진 중 `analysis_status="pending"`인 것 동기 분석
    - `for photo in pending: await analyze_photo_record(...)` 루프
    - 분석 완료 후 DB 세션 refresh하여 최신 상태 확인
    - _Requirements: 4.1, 4.2_
  - [ ] 7.3 모든 사진 분석 실패 시 오류 반환 (템플릿 미반환)
    - `if all(p.analysis_status == "failed" for p in photos):`
    - `raise HTTPException(status_code=502, detail="모든 사진 분석에 실패하여 글을 생성할 수 없습니다.")`
    - _Requirements: 4.4, 7.1, 7.2_
  - [ ] 7.4 `gen_service.generate_post(...)` 호출 시 `posting_intent` 전달
    - `posting_intent=posting_intent` 키워드 인자 추가
    - _Requirements: 5.1_
  - [ ] 7.5 생성 예외(`RuntimeError`/`ValueError`) → HTTP 5xx 변환 + 로그
    - `except (RuntimeError, ValueError) as e: raise HTTPException(status_code=502, detail=str(e))`
    - _Requirements: 7.1, 7.3_
  - [ ]* 7.6 파이프라인 속성 테스트 작성 (분석 모킹)
    - **Property 3: 분석 파이프라인 후 pending 잔여 없음**
    - **Validates: Requirements 4.2**

- [ ] 8. Checkpoint — photos.py, marblo.py 단위 테스트 확인
  - 분석 상태 전이(pending→analyzing→completed/failed) 검증
  - 의도 전달 검증
  - 오류 표면화 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. GenerationService 의도 반영 + 폴백 제거
  - [ ] 9.1 `generate_blog_post`, `generate_post` 시그니처에 `posting_intent: Optional[dict] = None` 추가
    - `_create_generation_prompt`로 전달
    - _Requirements: 5.1_
  - [ ] 9.2 `_create_generation_prompt`에서 `posting_intent` 프롬프트 반영
    - `topic` 존재 시 "주제: {topic}" 섹션 추가
    - `additional_context` 존재 시 "추가 컨텍스트: {additional_context}" 섹션 추가
    - 둘 다 비어 있으면 사진 메타데이터만으로 진행
    - **한국어 작성 지시 추가**: "자연스러운 한국어로 블로그 본문을 작성하라"
    - _Requirements: 5.2, 5.3, 5.4, 8.1_
  - [ ] 9.3 템플릿 폴백 제거
    - `_call_claude_for_generation`이 `None` 반환 시 `RuntimeError` 발생
    - `_generate_template_draft` 호출 경로 제거 (기본 성공 경로에서)
    - _Requirements: 7.1, 7.2_
  - [ ] 9.4 파싱 실패(`ValueError`) 그대로 전파
    - 이미 `_parse_generated_content`가 `ValueError` 발생 → 상위에서 처리
    - _Requirements: 7.4_
  - [ ] 9.5 다중 사진 메타데이터 컨텍스트 포함 검증
    - `_fetch_photos_with_metadata`가 모든 유효 사진 순회 확인
    - 무효/미소유 사진 제외 + 로그
    - _Requirements: 6.2, 6.3_
  - [ ]* 9.6 프롬프트 의도 포함 속성 테스트 작성
    - **Property 4: 프롬프트가 작성 의도를 포함**
    - **Validates: Requirements 5.2, 5.3**
  - [ ]* 9.7 유효 사진 컨텍스트 포함 속성 테스트 작성
    - **Property 5: 모든 유효 사진이 생성 컨텍스트에 포함**
    - **Validates: Requirements 6.2, 6.3**
  - [ ]* 9.8 초안-사진 연결 보존 속성 테스트 작성
    - **Property 6: 초안-사진 연결의 개수·순서 보존**
    - **Validates: Requirements 6.4**
  - [ ]* 9.9 생성 실패 오류 표면화 속성 테스트 작성
    - **Property 7: 생성 실패 시 템플릿을 성공으로 반환하지 않음**
    - **Validates: Requirements 7.1, 7.2**

- [ ] 10. Checkpoint — GenerationService 단위 테스트 확인
  - 의도 반영, 폴백 제거, 다중 사진 처리 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. 파싱 로직 속성 테스트 작성
  - [ ]* 11.1 파싱 불가 응답 오류 신호 속성 테스트
    - **Property 8: 파싱 불가 응답은 항상 오류로 신호**
    - **Validates: Requirements 7.4**
  - [ ]* 11.2 생성 결과 파싱 라운드트립 속성 테스트
    - **Property 9: 생성 결과 파싱 라운드트립**
    - **Validates: Requirements 8.2**

- [ ] 12. 통합 테스트 및 배포 검증
  - [ ] 12.1 로컬 통합 테스트 실행
    - Bedrock 모킹으로 전체 파이프라인(업로드→분석→생성) 검증
    - 실제 Bedrock 호출은 스모크 테스트로 별도 확인
    - _Requirements: 전체_
  - [ ] 12.2 EC2 배포 및 E2E 스모크 테스트
    - 코드를 EC2(`54.86.13.231`)에 배포
    - 실제 사진 1장으로 업로드→분석→생성 전체 경로 수동 테스트
    - 생성된 결과가 템플릿이 아닌 실제 AI 생성 내용인지 확인
    - _Requirements: 1.1, 3.1, 4.2, 5.1, 6.2, 7.2, 8.1_
  - [ ] 12.3 systemd 서비스 등록 권장 사항 확인 (선택)
    - `marblo.service` 유닛 파일 생성 권장
    - `Restart=always`, `ExecStart=uvicorn app.main:app --host 0.0.0.0 --port 8000`
    - 현재는 수동 uvicorn 기동이므로, 이 태스크는 권장 사항 문서화로 대체 가능
    - _Requirements: 운영 안정성_

- [ ] 13. Final Checkpoint — 전체 테스트 통과 확인
  - 모든 단위 테스트, 속성 테스트, 통합 테스트 통과 확인
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- 태스크에 `*` 표시된 항목은 **선택적(optional)** 테스트 태스크입니다. MVP 우선 시 건너뛸 수 있습니다.
- 각 태스크는 특정 요구사항(Requirements)을 참조합니다. 구현 시 design.md의 해당 섹션을 함께 확인하세요.
- Checkpoint 태스크는 중간 검증 지점으로, 테스트 실패 시 이전 태스크를 수정한 후 진행합니다.
- 속성 테스트는 Hypothesis 라이브러리를 사용하며, 각 테스트는 최소 100회 반복합니다.
- Bedrock 모델 접근 활성화(us-east-1)는 이미 확인되었으므로 별도 전제 조건 태스크는 포함하지 않았습니다.
- EC2 배포는 현재 수동 uvicorn 기동 방식을 사용합니다. systemd 등록은 권장 사항입니다.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["3.2", "3.3"] },
    { "id": 3, "tasks": ["3.4", "4.1"] },
    { "id": 4, "tasks": ["4.2"] },
    { "id": 5, "tasks": ["6.1"] },
    { "id": 6, "tasks": ["6.2", "6.3"] },
    { "id": 7, "tasks": ["7.1", "7.2"] },
    { "id": 8, "tasks": ["7.3", "7.4", "7.5"] },
    { "id": 9, "tasks": ["7.6"] },
    { "id": 10, "tasks": ["9.1"] },
    { "id": 11, "tasks": ["9.2", "9.3", "9.4", "9.5"] },
    { "id": 12, "tasks": ["9.6", "9.7", "9.8", "9.9"] },
    { "id": 13, "tasks": ["11.1", "11.2"] },
    { "id": 14, "tasks": ["12.1"] },
    { "id": 15, "tasks": ["12.2"] },
    { "id": 16, "tasks": ["12.3"] }
  ]
}
```

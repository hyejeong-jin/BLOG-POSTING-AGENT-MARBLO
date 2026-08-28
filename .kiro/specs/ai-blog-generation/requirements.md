# Requirements Document

## Introduction

Marblo(마블로)는 사용자가 사진을 업로드하고 작성 의도(포스팅 주제)를 설명하면 AI가 한국어 블로그 초안을 작성해 주는 서비스입니다. 현재 핵심 생성 기능은 기술적으로 존재하지만, 실제 AI 백엔드가 연결되어 있지 않아 결과물이 "형편없다"는 문제가 있습니다. 구체적으로는 생성된 글이 "[초안] 사진 이야기 - 직접 작성해주세요" 같은 빈 템플릿과 "사진 분석 데이터가 없습니다" 자리표시자로 출력되고, 여러 장을 선택해도 사진 1장만 반영되는 증상이 확인되었습니다.

이 스펙은 다음 근본 원인을 해결하는 것을 목표로 합니다.

- `app/utils/ai_client.py`가 직접 Anthropic API 경로만 지원하고 AWS Bedrock 경로가 구현되어 있지 않아, `CLAUDE_API_KEY`가 없으면 `app/services/generation_service.py`의 `_generate_template_draft()`로 조용히 폴백함.
- `app/routers/marblo.py`의 `generate-post` 엔드포인트가 `topic`과 `additional_context`를 받지만 `GenerationService.generate_post()`로 전달하지 않아 사용자 작성 의도가 프롬프트에 반영되지 않음.
- `/photos/upload` 이후 `analysis_status="pending"` 상태의 Photo 레코드만 생성되고, 생성 전에 비전 분석을 자동으로 트리거하지 않아 `PhotoMetadata`가 비어 있음.
- 다중 사진의 업로드 → 분석 → 생성 흐름이 안정적으로 연결되어 있지 않음.

사용자가 결정한 방향: AI 백엔드로 **AWS Bedrock**을 사용하고, 모델은 설정/환경 변수로 선택 가능하게 한다. 기본 모델은 저렴한 **Amazon Nova Lite**(비전 지원)로 시작하고, 환경 변수로 Claude Haiku 등으로 상향 조정할 수 있게 한다. EC2 IAM 역할이 이미 Bedrock 접근을 허용하므로(`terraform/main.tf`의 `bedrock:InvokeModel` 권한) 별도 API 키 관리는 필요하지 않다.

### Non-Goals (이번 스펙 범위 외)

- 글쓰기 스타일 학습 / VectorDB 연동 (별도 후속 스펙에서 다룸)
- 인프라 접근 복구(SSM 등) (별도로 처리 중)

## Glossary

- **Marblo_System**: Marblo 애플리케이션 전체(FastAPI 백엔드 + 정적 프런트엔드).
- **Generation_Service**: `app/services/generation_service.py`의 `GenerationService`. 사진 메타데이터와 작성 의도를 바탕으로 블로그 초안을 생성하는 서비스.
- **AI_Client**: `app/utils/ai_client.py`의 `AIClient`. AI 모델 호출을 담당하는 클라이언트.
- **Bedrock_Backend**: `AI_Client` 내부의 AWS Bedrock 호출 경로. EC2 IAM 역할의 `bedrock:InvokeModel` 권한을 사용.
- **Generation_Model**: 텍스트 생성 및 비전 분석에 사용하는 Bedrock 파운데이션 모델. 기본값은 Amazon Nova Lite, 환경 변수로 변경 가능.
- **Photo_Analysis**: 업로드된 사진에서 설명/위치/가격/날짜/카테고리를 추출하는 비전 분석 작업. 결과는 `PhotoMetadata`에 저장됨.
- **PhotoMetadata**: `app/models/db_models.py`의 사진 분석 결과 저장 모델.
- **Posting_Intent**: 사용자가 제공하는 작성 의도. `GeneratePostRequest`의 `topic`과 `additional_context`로 구성됨.
- **Generate_Post_Endpoint**: `app/routers/marblo.py`의 `POST /marblo/generate-post` 엔드포인트.
- **Upload_Photo_Endpoint**: `app/routers/photos.py`의 `POST /photos/upload` 엔드포인트.
- **Analyze_Photo_Endpoint**: `app/routers/photos.py`의 `POST /photos/{photo_id}/analyze` 엔드포인트.
- **Analysis_Status**: Photo 레코드의 분석 상태 필드(`pending`, `analyzing`, `completed`, `failed`).
- **Blog_Draft**: 생성된 블로그 초안(제목 + 본문). `status="draft"`로 저장됨.

## Requirements

### Requirement 1: AWS Bedrock 기반 AI 생성 연결

**User Story:** 운영자로서, AI 생성 요청이 AWS Bedrock을 통해 처리되기를 원한다. 그래야 별도의 API 키 관리 없이 IAM 역할만으로 실제 AI 결과물을 얻을 수 있다.

#### Acceptance Criteria

1. WHERE `use_bedrock` 설정이 활성화되어 있고 EC2 IAM 역할에 `bedrock:InvokeModel` 권한이 부여되어 있는 경우, THE AI_Client SHALL AWS Bedrock 경로를 통해 Generation_Model을 호출한다.
2. WHEN AI_Client가 Bedrock_Backend를 통해 텍스트 생성을 요청하는 경우, THE AI_Client SHALL Bedrock 응답에서 생성된 텍스트를 추출하여 반환한다.
3. THE Bedrock_Backend SHALL API 키(`CLAUDE_API_KEY`) 없이 IAM 역할 자격 증명만으로 Generation_Model을 호출한다.
4. WHEN Bedrock_Backend 호출이 5xx 계열의 일시적 오류로 실패하는 경우, THE AI_Client SHALL 최대 3회까지 지수 백오프로 재시도한다.

### Requirement 2: 생성 모델 설정 가능

**User Story:** 운영자로서, 생성에 사용할 Bedrock 모델을 환경 변수로 지정하고 싶다. 그래야 기본은 저렴한 모델로 두고 필요할 때 더 좋은 모델로 바꿀 수 있다.

#### Acceptance Criteria

1. WHERE 모델 환경 변수가 설정되지 않은 경우, THE Marblo_System SHALL Generation_Model 기본값으로 Amazon Nova Lite를 사용한다.
2. WHERE 모델 환경 변수가 설정된 경우, THE Marblo_System SHALL 지정된 모델 식별자(예: Claude Haiku)를 Generation_Model로 사용한다.
3. THE Marblo_System SHALL 선택된 Generation_Model 식별자를 애플리케이션 설정(`app/config.py`)에서 단일 지점으로 읽어온다.
4. WHEN 생성 또는 분석 요청이 처리되는 경우, THE AI_Client SHALL 설정된 Generation_Model 식별자를 Bedrock 호출에 사용한다.

### Requirement 3: 비전 기반 사진 분석

**User Story:** 사용자로서, 업로드한 사진에서 설명/위치/가격/날짜/카테고리가 자동으로 추출되기를 원한다. 그래야 생성된 글이 사진의 실제 내용을 반영한다.

#### Acceptance Criteria

1. WHEN Analyze_Photo_Endpoint가 사진에 대한 분석을 요청받는 경우, THE AI_Client SHALL Bedrock_Backend의 비전 지원 Generation_Model을 사용하여 사진을 분석한다.
2. WHEN Photo_Analysis가 성공적으로 완료되는 경우, THE Marblo_System SHALL 추출된 설명, 위치, 가격, 날짜, 카테고리를 PhotoMetadata에 저장한다.
3. WHEN Photo_Analysis가 성공적으로 완료되는 경우, THE Marblo_System SHALL 해당 Photo의 Analysis_Status를 `completed`로 갱신한다.
4. IF Photo_Analysis가 실패하는 경우, THEN THE Marblo_System SHALL 해당 Photo의 Analysis_Status를 `failed`로 갱신하고 실패 사유를 로그에 기록한다.
5. WHERE 사진에서 특정 항목(위치, 가격, 날짜 중 하나)이 확인되지 않는 경우, THE Marblo_System SHALL 해당 항목을 비어 있는 값으로 저장하고 나머지 확인된 항목은 정상 저장한다.

### Requirement 4: 업로드 → 분석 → 생성 흐름 자동 연결

**User Story:** 사용자로서, 사진을 업로드하고 글을 생성하면 별도 조작 없이 분석이 먼저 수행되기를 원한다. 그래야 생성 시점에 사진 메타데이터가 비어 있지 않다.

#### Acceptance Criteria

1. WHEN Generate_Post_Endpoint가 생성 요청을 받는 경우, THE Marblo_System SHALL 요청에 포함된 각 Photo의 Analysis_Status를 확인한다.
2. WHILE 요청에 포함된 Photo 중 Analysis_Status가 `pending`인 Photo가 존재하는 동안, THE Marblo_System SHALL 생성 이전에 해당 Photo에 대한 Photo_Analysis를 트리거한다.
3. WHEN 요청된 모든 Photo의 Photo_Analysis가 완료되거나 실패로 확정된 경우, THE Generation_Service SHALL 확보된 PhotoMetadata를 사용하여 생성을 진행한다.
4. IF 요청된 모든 Photo의 Analysis_Status가 `failed`인 경우, THEN THE Generate_Post_Endpoint SHALL 오류 메시지를 반환하고 빈 템플릿 초안을 반환하지 않는다.

### Requirement 5: 작성 의도(주제 + 추가 컨텍스트) 반영

**User Story:** 사용자로서, 내가 입력한 포스팅 주제와 추가 설명이 생성된 글에 반영되기를 원한다. 그래야 결과물이 내 의도에 맞는다.

#### Acceptance Criteria

1. WHEN Generate_Post_Endpoint가 `topic` 또는 `additional_context`를 포함한 요청을 받는 경우, THE Generate_Post_Endpoint SHALL Posting_Intent를 Generation_Service의 `generate_post()` 호출에 전달한다.
2. WHEN Generation_Service가 Posting_Intent를 전달받는 경우, THE Generation_Service SHALL Posting_Intent를 Generation_Model에 전달하는 생성 프롬프트에 포함한다.
3. WHERE `topic`이 제공된 경우, THE Generation_Service SHALL 생성된 Blog_Draft가 해당 주제를 반영하도록 프롬프트에 주제를 명시한다.
4. WHERE `topic`과 `additional_context`가 모두 비어 있는 경우, THE Generation_Service SHALL 사진 메타데이터만으로 생성을 진행한다.

### Requirement 6: 다중 사진 처리

**User Story:** 사용자로서, 여러 장의 사진을 선택하면 모두 업로드·분석되고 생성 결과에 반영되기를 원한다. 그래야 사진 1장만 반영되는 문제가 사라진다.

#### Acceptance Criteria

1. WHEN Upload_Photo_Endpoint가 여러 사진 파일을 순차적으로 받는 경우, THE Marblo_System SHALL 각 사진마다 개별 Photo 레코드를 생성하고 각 `photo_id`를 반환한다.
2. WHEN Generate_Post_Endpoint가 복수의 `photo_ids`를 포함한 요청을 받는 경우, THE Generation_Service SHALL 요청된 모든 유효한 Photo의 PhotoMetadata를 생성 컨텍스트에 포함한다.
3. IF `photo_ids` 중 일부 Photo가 조회되지 않거나 사용자 소유가 아닌 경우, THEN THE Generation_Service SHALL 유효한 Photo만으로 생성을 진행하고 제외된 Photo를 로그에 기록한다.
4. WHEN Blog_Draft가 저장되는 경우, THE Marblo_System SHALL 생성에 사용된 모든 유효한 Photo를 표시 순서와 함께 Blog_Draft에 연결한다.

### Requirement 7: 폴백 및 오류 표면화

**User Story:** 사용자로서, AI 생성이 불가능할 때 빈 템플릿 대신 명확한 안내를 받고 싶다. 그래야 무엇이 잘못되었는지 알 수 있다.

#### Acceptance Criteria

1. IF Bedrock_Backend 또는 Generation_Model을 사용할 수 없는 경우, THEN THE Generate_Post_Endpoint SHALL 사용자에게 생성 실패를 알리는 명확한 오류 응답을 반환한다.
2. IF 생성이 실패하는 경우, THEN THE Marblo_System SHALL "[초안] 사진 이야기 - 직접 작성해주세요" 형태의 빈 템플릿 초안을 성공 결과로 반환하지 않는다.
3. WHEN 생성 실패 오류가 반환되는 경우, THE Generate_Post_Endpoint SHALL 실패 원인을 로그에 기록한다.
4. IF Generation_Model 응답이 파싱 불가능한 형식인 경우, THEN THE Generation_Service SHALL 생성 실패로 처리하고 오류를 표면화한다.

### Requirement 8: 한국어 출력 품질

**User Story:** 한국 사용자로서, 생성된 글이 자연스러운 한국어로 작성되고 사진과 의도를 반영하기를 원한다. 그래야 초안을 바로 다듬어 쓸 수 있다.

#### Acceptance Criteria

1. THE Generation_Service SHALL Generation_Model에 한국어로 블로그 본문을 작성하도록 지시하는 프롬프트를 전달한다.
2. WHEN Blog_Draft가 성공적으로 생성되는 경우, THE Generation_Service SHALL 제목과 본문을 모두 포함한 Blog_Draft를 반환한다.
3. WHEN Blog_Draft가 성공적으로 생성되는 경우, THE Generation_Service SHALL 본문에 확보된 PhotoMetadata의 내용과 Posting_Intent를 반영한다.
4. WHERE 생성된 본문 길이가 설정된 최소/최대 길이 범위를 벗어나는 경우, THE Generation_Service SHALL 길이 범위 위반을 로그에 기록한다.

### Requirement 9: 비용 절약형 설정

**User Story:** 운영자로서, 월 사용량이 적기 때문에(약 10회/월) 저렴한 모델과 절약형 토큰 설정을 기본값으로 두고 싶다. 그래야 불필요한 비용이 발생하지 않는다.

#### Acceptance Criteria

1. THE Marblo_System SHALL Generation_Model 기본값으로 저비용 모델인 Amazon Nova Lite를 사용한다.
2. THE Marblo_System SHALL 생성 요청당 최대 출력 토큰 수를 설정 값으로 제한한다.
3. WHERE 운영자가 모델 또는 최대 토큰 환경 변수를 조정한 경우, THE Marblo_System SHALL 코드 수정 없이 해당 설정 값을 적용한다.

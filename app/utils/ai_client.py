"""
AI client for Claude integration via AWS Bedrock or direct API.

This module provides functionality for:
- Interfacing with Claude AI models
- Photo analysis and description generation
- Blog post generation from metadata
- Writing style analysis
- Implementing exponential backoff retry logic
"""

import asyncio
import json
import re
from typing import Optional

import boto3
from botocore.exceptions import ClientError
import httpx

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class AIClient:
    """
    AI client wrapper for Claude API integration.
    
    Supports:
    - Direct Anthropic Claude API
    - AWS Bedrock Claude integration (via Converse API)
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1
    
    # Retryable Bedrock errors (transient server/throttle errors)
    RETRYABLE_ERRORS = {
        "ThrottlingException",
        "ServiceUnavailableException",
        "InternalServerException",
        "ModelTimeoutException",
    }
    
    def __init__(self, use_bedrock: bool | None = None):
        """
        Initialize AI client.
        
        Args:
            use_bedrock: Whether to use AWS Bedrock (vs direct API).
                         If None, reads from settings.use_bedrock.
        """
        self.use_bedrock = settings.use_bedrock if use_bedrock is None else use_bedrock
        self.claude_api_key = settings.claude_api_key
        self.claude_model = settings.claude_model
        self.api_base_url = "https://api.anthropic.com/v1"
        
        # Bedrock configuration
        self.model_id = settings.bedrock_model_id
        self.max_tokens = settings.bedrock_max_tokens
        self._bedrock = None  # Lazy initialization
        
        if not self.claude_api_key and not self.use_bedrock:
            logger.warning("Claude API key not configured, some features will be unavailable")
    
    def _get_bedrock_client(self):
        """
        Get or create the Bedrock runtime client (lazy initialization).
        
        Uses IAM role credentials via boto3 default credential chain.
        No explicit credentials are passed to support EC2 instance profiles.
        
        Returns:
            boto3 bedrock-runtime client
        """
        if self._bedrock is None:
            self._bedrock = boto3.client(
                "bedrock-runtime",
                region_name=settings.bedrock_region
            )
            logger.info(
                "Bedrock client initialized",
                region=settings.bedrock_region,
                model_id=self.model_id
            )
        return self._bedrock
    
    def _extract_text(self, converse_response: dict) -> str:
        """
        Extract text from Bedrock Converse API response.
        
        Combines all text blocks from output.message.content in order.
        
        Args:
            converse_response: Response dict from Bedrock Converse API.
                Expected structure: {"output": {"message": {"content": [{"text": "..."}, ...]}}}
        
        Returns:
            Combined text from all text blocks, or empty string if response is empty.
        """
        output = converse_response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        
        text_parts = []
        for block in content_blocks:
            if "text" in block:
                text_parts.append(block["text"])
        
        return "".join(text_parts)
    def _clean_json_response(self, text: str) -> str:
        """
        Clean response text to extract pure JSON.
        
        Handles various AI response formats:
        - Pure JSON
        - JSON wrapped in ```json ... ``` blocks
        - JSON embedded in explanatory text with code blocks
        
        Args:
            text: Raw response text that may contain markdown formatting
            
        Returns:
            Cleaned text ready for JSON parsing
        """
        if not text:
            return text
        
        cleaned = text.strip()
        
        # Try to extract JSON from ```json ... ``` or ``` ... ``` blocks
        # This handles cases where AI adds explanatory text before/after
        json_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
        if json_block_match:
            cleaned = json_block_match.group(1).strip()
        elif cleaned.startswith("```"):
            # Fallback: Remove opening/closing markers if no match found
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        
        return cleaned.strip()
    
    async def _invoke_converse(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Call Bedrock Converse API with exponential backoff retry.
        
        Validates: Requirements 1.2, 1.4, 2.4, 9.2
        
        Args:
            messages: List of message dicts for the conversation.
                Format: [{"role": "user", "content": [{"text": "..."}]}]
            system_prompt: Optional system prompt text
            
        Returns:
            Generated text if successful, None otherwise
        """
        if not self.use_bedrock:
            logger.warning("Bedrock is disabled, _invoke_converse returning None")
            return None
        
        bedrock = self._get_bedrock_client()
        
        # Build converse parameters
        converse_params = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": self.max_tokens,
            },
        }
        
        # Add system prompt if provided
        if system_prompt:
            converse_params["system"] = [{"text": system_prompt}]
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    "Calling Bedrock Converse API",
                    attempt=attempt + 1,
                    model_id=self.model_id,
                )
                
                # Offload synchronous boto3 call to thread pool
                response = await asyncio.to_thread(
                    bedrock.converse,
                    **converse_params
                )
                
                # Extract text from response
                result_text = self._extract_text(response)
                
                logger.info(
                    "Bedrock Converse API call successful",
                    model_id=self.model_id,
                    response_length=len(result_text),
                )
                
                return result_text
                
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                error_message = e.response.get("Error", {}).get("Message", str(e))
                
                logger.warning(
                    "Bedrock Converse API error",
                    attempt=attempt + 1,
                    error_code=error_code,
                    error_message=error_message,
                )
                
                # Check if this is a retryable error
                if error_code in self.RETRYABLE_ERRORS and attempt < self.MAX_RETRIES - 1:
                    backoff_seconds = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    logger.info(
                        "Retrying Bedrock Converse API call",
                        backoff_seconds=backoff_seconds,
                        error_code=error_code,
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    # Non-retryable error or max retries reached
                    logger.error(
                        "Bedrock Converse API call failed",
                        error_code=error_code,
                        error_message=error_message,
                        is_retryable=error_code in self.RETRYABLE_ERRORS,
                    )
                    return None
                    
            except Exception as e:
                logger.error(
                    "Unexpected error calling Bedrock Converse API",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                return None
        
        logger.error(
            "Bedrock Converse API call failed after all retries",
            total_attempts=self.MAX_RETRIES,
        )
        return None
    
    async def analyze_photo(
        self,
        image_bytes: bytes,
        image_format: str,
        photo_title: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Analyze a photo and extract metadata using Bedrock Converse vision API.
        
        Validates: Requirements 3.1
        
        Generates:
        - Photo description
        - Location information (if visible)
        - Date/time information (if visible)
        - Category classification
        - Objects identified in the photo
        - Mood/atmosphere of the photo
        
        Args:
            image_bytes: Raw image bytes from S3
            image_format: Image format (jpeg, png, gif, webp)
            photo_title: Optional title provided by user
            
        Returns:
            Dict with analysis results if successful, None otherwise
        """
        if not self.use_bedrock:
            logger.warning("Bedrock is disabled, analyze_photo returning None")
            return None
        
        # Normalize image format to lowercase
        normalized_format = image_format.lower()
        # Map common extensions to Converse API format
        format_mapping = {
            "jpg": "jpeg",
            "jpeg": "jpeg",
            "png": "png",
            "gif": "gif",
            "webp": "webp",
        }
        converse_format = format_mapping.get(normalized_format, "jpeg")
        
        # System prompt with analysis instructions (Korean)
        system_prompt = """?ъ쭊??遺꾩꽍?섏뿬 ?ㅼ쓬 ?뺣낫瑜?JSON ?뺤떇?쇰줈 異붿텧?섏꽭??
- description: ?ъ쭊??????먯꽭???ㅻ챸 (2-3臾몄옣)
- location: ?ъ쭊??珥ъ쁺???μ냼 (?????놁쑝硫?null)
- date: ?ъ쭊 珥ъ쁺 異붿젙 ?쒓린 (?????놁쑝硫?null)
- category: ?ъ쭊 移댄뀒怨좊━ (food, travel, daily, nature, people, other 以??섎굹)
- objects: ?ъ쭊?먯꽌 ?앸퀎??二쇱슂 媛앹껜 紐⑸줉
- mood: ?ъ쭊??遺꾩쐞湲?(諛앹?, ?대몢?? ?곕쑜?? 李④?????

JSON留?諛섑솚?섍퀬 ?ㅻⅨ ?띿뒪?몃뒗 ?ы븿?섏? 留덉꽭??"""
        
        # User message with image and request text
        user_text = "???ъ쭊??遺꾩꽍?섍퀬 JSON?쇰줈 ?묐떟?댁＜?몄슂."
        if photo_title:
            user_text += f"\n\n?ъ쭊 ?쒕ぉ: {photo_title}"
        
        # Build Converse API messages with image block
        messages = [{
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": converse_format,
                        "source": {"bytes": image_bytes}
                    }
                },
                {"text": user_text}
            ]
        }]
        
        logger.info(
            "Analyzing photo via Bedrock Converse vision API",
            image_format=converse_format,
            image_size_bytes=len(image_bytes),
            has_title=photo_title is not None,
        )
        
        # Call Converse API
        response_text = await self._invoke_converse(messages, system_prompt)
        
        if response_text is None:
            logger.error("Photo analysis failed: no response from Converse API")
            return None
        
        # Parse response as JSON
        try:
            cleaned_response = self._clean_json_response(response_text)
            result = json.loads(cleaned_response)
            logger.info(
                "Photo analysis completed successfully",
                has_description="description" in result,
                has_location="location" in result,
                category=result.get("category"),
            )
            return result
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse photo analysis response as JSON",
                error=str(e),
                response_preview=response_text[:200] if response_text else None,
            )
            return None
    
    async def generate_blog_post(
        self,
        photo_metadata: dict,
        writing_style: Optional[dict] = None,
        blog_title: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Generate a blog post based on photo metadata and writing style.
        
        Uses Bedrock Converse API when use_bedrock=True, falls back to
        direct Anthropic API when use_bedrock=False.
        
        Args:
            photo_metadata: Dict with photo analysis results
            writing_style: Optional dict with writing style profile
            blog_title: Optional suggested blog post title
            
        Returns:
            Dict with 'title' and 'body' if successful, None otherwise
        """
        metadata_str = json.dumps(photo_metadata, indent=2, ensure_ascii=False)
        style_str = json.dumps(writing_style, indent=2, ensure_ascii=False) if writing_style else "吏?뺣맂 ?ㅽ????놁쓬"
        
        # System prompt for blog generation (Korean)
        system_prompt = """?뱀떊? ?꾨Ц ?쒓뎅??釉붾줈洹??묒꽦?먯엯?덈떎. 
?ъ쭊 硫뷀??곗씠?곗? ?묒꽦 ?ㅽ??쇱쓣 湲곕컲?쇰줈 ?먯뿰?ㅻ읇怨?留ㅻ젰?곸씤 ?쒓뎅??釉붾줈洹?湲???묒꽦?⑸땲??

?묐떟 ?뺤떇:
諛섎뱶???ㅼ쓬 JSON ?뺤떇?쇰줈留??묐떟?섏꽭??
{"title": "釉붾줈洹??쒕ぉ", "body": "蹂몃Ц ?댁슜"}

洹쒖튃:
- ?먯뿰?ㅻ윭???쒓뎅?대줈 ?묒꽦
- 3-5媛쒖쓽 臾몃떒 ?ы븿
- ?ъ쭊 硫뷀??곗씠?곗쓽 愿???뺣낫 諛섏쁺
- ?낆옄?먭쾶 ?좎슜?섍퀬 ?λ?濡쒖슫 ?댁슜 ?묒꽦"""
        
        user_prompt = f"""?ㅼ쓬 ?뺣낫瑜?湲곕컲?쇰줈 釉붾줈洹?湲???묒꽦?댁＜?몄슂.

?ъ쭊 硫뷀??곗씠??
{metadata_str}

?묒꽦 ?ㅽ???
{style_str}

?쒖븞???쒕ぉ: {blog_title or '?먮룞 ?앹꽦'}

JSON ?뺤떇?쇰줈留??묐떟?댁＜?몄슂."""

        logger.info(
            "Generating blog post",
            use_bedrock=self.use_bedrock,
            has_style=writing_style is not None,
            has_title=blog_title is not None,
        )

        # Use Bedrock Converse API when enabled
        if self.use_bedrock:
            messages = [{
                "role": "user",
                "content": [{"text": user_prompt}]
            }]
            
            result_text = await self._invoke_converse(messages, system_prompt)
            
            if result_text:
                try:
                    cleaned_text = self._clean_json_response(result_text)
                    result = json.loads(cleaned_text)
                    if "title" in result and "body" in result:
                        logger.info("Blog post generated successfully via Bedrock")
                        return result
                    else:
                        logger.error(
                            "Blog post response missing required fields",
                            has_title="title" in result,
                            has_body="body" in result,
                        )
                except json.JSONDecodeError as e:
                    logger.error(
                        "Failed to parse blog post response as JSON",
                        error=str(e),
                        response_preview=result_text[:200] if result_text else None,
                    )
            return None
        
        # Fallback to direct Anthropic API
        prompt = f"""Based on the following photo metadata and writing style preferences, generate a blog post.

Photo Metadata:
{metadata_str}

Writing Style Profile:
{style_str}

Suggested Title: {blog_title or 'Auto-generate'}

Requirements:
- Write in a natural, engaging tone
- Include 3-5 paragraphs
- Use the provided writing style if available
- Make it informative and useful for readers
- Include relevant details from the photo metadata

Generate the blog post with:
1. Title (if not provided, create a compelling one)
2. Main content (3-5 paragraphs)

Format:
TITLE: [Title here]
CONTENT:
[Blog post content here]"""

        result = await self._call_claude(prompt)
        
        if result:
            # Extract title and content from text format
            try:
                if isinstance(result, str):
                    lines = result.split("\n")
                    title = ""
                    content = ""
                    capturing_content = False
                    
                    for line in lines:
                        if line.startswith("TITLE:"):
                            capturing_content = False
                            title = line.replace("TITLE:", "").strip()
                        elif line.startswith("CONTENT:"):
                            capturing_content = True
                        elif capturing_content:
                            content += line + "\n"
                    
                    if title and content.strip():
                        logger.info("Blog post generated successfully via direct API")
                        return {
                            "title": title,
                            "body": content.strip(),
                        }
                elif isinstance(result, dict) and "title" in result and "body" in result:
                    logger.info("Blog post generated successfully via direct API")
                    return result
            except Exception as e:
                logger.error("Error parsing blog post response", error=str(e))
        
        return None
    
    async def analyze_writing_style(
        self,
        sample_posts: list[str],
    ) -> Optional[dict]:
        """
        Analyze writing style from sample blog posts.
        
        Uses Bedrock Converse API when use_bedrock=True, falls back to
        direct Anthropic API when use_bedrock=False.
        
        Extracts:
        - Vocabulary patterns
        - Sentence structure preferences
        - Tone and attitude
        - Formatting rules
        - Characteristic phrases
        - Average post length
        - Keyword frequencies
        
        Args:
            sample_posts: List of blog post samples to analyze
            
        Returns:
            Dict with style analysis if successful, None otherwise
        """
        if not sample_posts:
            return None
        
        posts_str = "\n\n---POST BOUNDARY---\n\n".join(sample_posts)
        
        # System prompt for style analysis (Korean)
        system_prompt = """?뱀떊? 湲?곌린 ?ㅽ???遺꾩꽍 ?꾨Ц媛?낅땲??
釉붾줈洹??ъ뒪?몃? 遺꾩꽍?섏뿬 ?묒꽦 ?ㅽ????뱀꽦??異붿텧?⑸땲??

?묐떟 ?뺤떇:
諛섎뱶???좏슚??JSON?쇰줈留??묐떟?섏꽭?? ?ㅻⅨ ?띿뒪?몃뒗 ?ы븿?섏? 留덉꽭??"""
        
        user_prompt = f"""?ㅼ쓬 釉붾줈洹??ъ뒪?몃뱾??遺꾩꽍?섍퀬 湲?곌린 ?ㅽ????뱀꽦??JSON?쇰줈 異붿텧?섏꽭??

?ъ뒪??
{posts_str}

?ㅼ쓬 援ъ“??JSON?쇰줈 ?묐떟?섏꽭??
{{
    "vocabulary_patterns": {{
        "common_words": ["?먯＜ ?ъ슜?섎뒗 10媛??⑥뼱"],
        "style": "formal/casual/technical/conversational"
    }},
    "sentence_structure": {{
        "avg_words_per_sentence": ?レ옄,
        "uses_short_sentences": true/false,
        "uses_complex_sentences": true/false,
        "passive_voice_frequency": "low/medium/high"
    }},
    "tone": {{
        "primary_tone": "descriptive/analytical/conversational/inspirational",
        "attitude": "objective/subjective/humorous/serious",
        "emotional_level": "low/medium/high"
    }},
    "formatting": {{
        "uses_lists": true/false,
        "uses_quotes": true/false,
        "uses_emojis": true/false,
        "heading_style": "minimal/moderate/extensive"
    }},
    "characteristic_phrases": ["???묒꽦??怨좎쑀??5-10媛??쒗쁽"],
    "avg_post_length_words": ?レ옄,
    "keyword_frequencies": {{"二쇱슂_?ㅼ썙??: 鍮덈룄, "...": "..."}},
    "overall_summary": "湲?곌린 ?ㅽ??쇱쓽 1-2臾몄옣 ?붿빟"
}}"""

        logger.info(
            "Analyzing writing style",
            use_bedrock=self.use_bedrock,
            sample_count=len(sample_posts),
        )

        # Use Bedrock Converse API when enabled
        if self.use_bedrock:
            messages = [{
                "role": "user",
                "content": [{"text": user_prompt}]
            }]
            
            result_text = await self._invoke_converse(messages, system_prompt)
            
            if result_text:
                try:
                    cleaned_text = self._clean_json_response(result_text)
                    result = json.loads(cleaned_text)
                    logger.info("Writing style analysis completed via Bedrock")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(
                        "Failed to parse writing style response as JSON",
                        error=str(e),
                        response_preview=result_text[:200] if result_text else None,
                    )
            return None
        
        # Fallback to direct Anthropic API
        prompt = f"""Analyze the following blog posts and extract writing style characteristics in JSON format:

Posts:
{posts_str}

Analyze and return JSON with:
{{
    "vocabulary_patterns": {{
        "common_words": ["list of 10 most frequent substantive words"],
        "style": "formal/casual/technical/conversational"
    }},
    "sentence_structure": {{
        "avg_words_per_sentence": number,
        "uses_short_sentences": true/false,
        "uses_complex_sentences": true/false,
        "passive_voice_frequency": "low/medium/high"
    }},
    "tone": {{
        "primary_tone": "descriptive/analytical/conversational/inspirational",
        "attitude": "objective/subjective/humorous/serious",
        "emotional_level": "low/medium/high"
    }},
    "formatting": {{
        "uses_lists": true/false,
        "uses_quotes": true/false,
        "uses_emojis": true/false,
        "heading_style": "minimal/moderate/extensive"
    }},
    "characteristic_phrases": ["5-10 phrases that are unique to this author"],
    "avg_post_length_words": number,
    "keyword_frequencies": {{"top_keyword": frequency, "...": "..."}},
    "overall_summary": "1-2 sentence summary of the writing style"
}}

Respond with ONLY valid JSON, no additional text."""

        result = await self._call_claude(prompt)
        
        if result:
            logger.info("Writing style analysis completed via direct API")
        
        return result
    
    async def call_claude(
        self,
        prompt: str,
        is_image: bool = False,
        image_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[dict | str]:
        """
        Public method to call Claude API with retry logic.
        
        Uses Bedrock Converse API when use_bedrock=True, falls back to
        direct Anthropic API when use_bedrock=False.
        
        Args:
            prompt: The prompt to send to Claude
            is_image: Whether this request includes image analysis (only for direct API)
            image_url: URL of image to analyze (only for direct API)
            system_prompt: Optional system prompt text
            
        Returns:
            Claude's response if successful, None otherwise
        """
        logger.info(
            "Calling Claude API (public method)",
            use_bedrock=self.use_bedrock,
            is_image=is_image,
            has_system_prompt=system_prompt is not None,
        )
        
        # Use Bedrock Converse API when enabled (no image URL support for Converse)
        if self.use_bedrock and not is_image:
            messages = [{
                "role": "user",
                "content": [{"text": prompt}]
            }]
            
            result_text = await self._invoke_converse(messages, system_prompt)
            
            if result_text:
                # Try to parse as JSON
                try:
                    
                    cleaned = self._clean_json_response(result_text)
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    return result_text
            return None
        
        # Fallback to direct Anthropic API
        return await self._call_claude(prompt, is_image, image_url)
    
    async def _call_claude(
        self,
        prompt: str,
        is_image: bool = False,
        image_url: Optional[str] = None,
    ) -> Optional[dict | str]:
        """
        Call Claude API with retry logic.
        
        Args:
            prompt: The prompt to send to Claude
            is_image: Whether this request includes image analysis
            image_url: URL of image to analyze
            
        Returns:
            Claude's response if successful, None otherwise
        """
        if not self.claude_api_key and not self.use_bedrock:
            logger.error("Claude API not configured")
            return None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    "Calling Claude API",
                    attempt=attempt + 1,
                    is_image=is_image,
                )
                
                # Build request
                headers = {
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                
                # Build message content
                content = []
                if is_image and image_url:
                    # Image content
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url,
                        },
                    })
                
                # Text content
                content.append({
                    "type": "text",
                    "text": prompt,
                })
                
                payload = {
                    "model": self.claude_model,
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": content,
                        }
                    ],
                }
                
                # Make request
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        f"{self.api_base_url}/messages",
                        json=payload,
                        headers=headers,
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract response text
                    if "content" in result and len(result["content"]) > 0:
                        response_text = result["content"][0].get("text", "")
                        
                        logger.info("Claude API call successful")
                        
                        # Try to parse as JSON if applicable
                        try:
                            return json.loads(response_text)
                        except json.JSONDecodeError:
                            return response_text
                    else:
                        logger.error("Unexpected response format from Claude", response=result)
                        return None
                
                else:
                    error_detail = response.text if response.text else "Unknown error"
                    logger.warning(
                        "Claude API error",
                        attempt=attempt + 1,
                        status=response.status_code,
                        error=error_detail,
                    )
                    
                    # Check if we should retry
                    if response.status_code >= 500 and attempt < self.MAX_RETRIES - 1:
                        backoff_seconds = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                        logger.info(
                            "Retrying Claude API call",
                            backoff_seconds=backoff_seconds,
                        )
                        await asyncio.sleep(backoff_seconds)
                    else:
                        return None
            
            except asyncio.TimeoutError:
                logger.warning(
                    "Claude API timeout",
                    attempt=attempt + 1,
                )
                if attempt < self.MAX_RETRIES - 1:
                    backoff_seconds = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    await asyncio.sleep(backoff_seconds)
                else:
                    return None
            
            except Exception as e:
                logger.error(
                    "Error calling Claude API",
                    attempt=attempt + 1,
                    error=str(e),
                )
                return None
        
        logger.error(
            "Claude API call failed after retries",
            total_attempts=self.MAX_RETRIES,
        )
        return None


# Global AI client instance
_ai_client: Optional[AIClient] = None


def get_ai_client(use_bedrock: bool | None = None) -> AIClient:
    """
    Get or create the global AI client instance.
    
    Args:
        use_bedrock: Whether to use AWS Bedrock. If None, reads from settings.
        
    Returns:
        AIClient instance
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient(use_bedrock=use_bedrock)
    return _ai_client






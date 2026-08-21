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
from typing import Optional

import httpx

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class AIClient:
    """
    AI client wrapper for Claude API integration.
    
    Supports:
    - Direct Anthropic Claude API
    - AWS Bedrock Claude integration
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1
    
    def __init__(self, use_bedrock: bool = False):
        """
        Initialize AI client.
        
        Args:
            use_bedrock: Whether to use AWS Bedrock (vs direct API)
        """
        self.use_bedrock = use_bedrock
        self.claude_api_key = settings.claude_api_key
        self.claude_model = settings.claude_model
        self.api_base_url = "https://api.anthropic.com/v1"
        
        if not self.claude_api_key and not use_bedrock:
            logger.warning("Claude API key not configured, some features will be unavailable")
    
    async def analyze_photo(
        self,
        image_url: str,
        photo_title: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Analyze a photo and extract metadata.
        
        Generates:
        - Photo description
        - Location information (if visible)
        - Price/cost information (if visible)
        - Date/time information (if visible)
        - Category classification
        - Confidence scores
        
        Args:
            image_url: URL or path to the image
            photo_title: Optional title provided by user
            
        Returns:
            Dict with analysis results if successful, None otherwise
        """
        prompt = f"""Analyze this photo and extract the following information in JSON format:

{{
    "description": "A 2-3 sentence description of what's in the photo",
    "location": {{
        "visible_location": "If location name is visible, include it; otherwise null",
        "location_type": "indoor/outdoor/unknown"
    }},
    "price": {{
        "price_visible": false or true,
        "currency": "if price visible, what currency",
        "amount": "if price visible, the amount"
    }},
    "date_time": {{
        "date_visible": false or true,
        "date": "if date visible, in YYYY-MM-DD format"
    }},
    "category": "Choose from: food, clothing, furniture, electronics, vehicle, real_estate, other",
    "confidence_scores": {{
        "description": 0.0-1.0,
        "location": 0.0-1.0,
        "price": 0.0-1.0,
        "date": 0.0-1.0,
        "category": 0.0-1.0
    }}
}}

Photo title (if provided): {photo_title or 'None'}

Respond with ONLY valid JSON, no additional text."""

        return await self._call_claude(prompt, is_image=True, image_url=image_url)
    
    async def generate_blog_post(
        self,
        photo_metadata: dict,
        writing_style: Optional[dict] = None,
        blog_title: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a blog post based on photo metadata and writing style.
        
        Args:
            photo_metadata: Dict with photo analysis results
            writing_style: Optional dict with writing style profile
            blog_title: Optional suggested blog post title
            
        Returns:
            Generated blog post content if successful, None otherwise
        """
        metadata_str = json.dumps(photo_metadata, indent=2, ensure_ascii=False)
        style_str = json.dumps(writing_style, indent=2, ensure_ascii=False) if writing_style else "No specific style provided"
        
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
            # Extract title and content
            try:
                lines = result.split("\n")
                title = ""
                content = ""
                capturing_title = False
                capturing_content = False
                
                for line in lines:
                    if line.startswith("TITLE:"):
                        capturing_title = True
                        capturing_content = False
                        title = line.replace("TITLE:", "").strip()
                    elif line.startswith("CONTENT:"):
                        capturing_title = False
                        capturing_content = True
                    elif capturing_content:
                        content += line + "\n"
                
                if title and content.strip():
                    return {
                        "title": title,
                        "body": content.strip(),
                    }
            except Exception as e:
                logger.error("Error parsing blog post response", error=str(e))
        
        return None
    
    async def analyze_writing_style(
        self,
        sample_posts: list[str],
    ) -> Optional[dict]:
        """
        Analyze writing style from sample blog posts.
        
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

        return await self._call_claude(prompt)
    
    async def call_claude(
        self,
        prompt: str,
        is_image: bool = False,
        image_url: Optional[str] = None,
    ) -> Optional[dict | str]:
        """
        Public method to call Claude API with retry logic.
        
        Args:
            prompt: The prompt to send to Claude
            is_image: Whether this request includes image analysis
            image_url: URL of image to analyze
            
        Returns:
            Claude's response if successful, None otherwise
        """
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


def get_ai_client(use_bedrock: bool = False) -> AIClient:
    """
    Get or create the global AI client instance.
    
    Args:
        use_bedrock: Whether to use AWS Bedrock
        
    Returns:
        AIClient instance
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient(use_bedrock=use_bedrock)
    return _ai_client



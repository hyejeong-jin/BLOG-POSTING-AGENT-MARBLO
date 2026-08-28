"""
Blog Post Generation Service.

This service handles generating blog posts based on photos, metadata, and writing style.
"""

import json
import re
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import (
    BlogPost,
    Photo,
    PhotoMetadata,
    WritingStyleProfile,
    GenerationHistory,
    BlogPostPhoto,
)
from app.utils.ai_client import AIClient
from app.logging_config import get_logger

logger = get_logger(__name__)


class GenerationService:
    """Service for generating blog posts."""
    
    # Generation constraints
    DEFAULT_MIN_LENGTH = 800
    DEFAULT_MAX_LENGTH = 3000
    DEFAULT_MODEL = "claude-3-sonnet"
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the generation service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.ai_client = AIClient()
    
    async def generate_blog_post(
        self,
        user_id: UUID,
        photo_ids: List[UUID],
        style_profile_id: Optional[UUID] = None,
        min_length: int = DEFAULT_MIN_LENGTH,
        posting_intent: Optional[Dict] = None,
        max_length: int = DEFAULT_MAX_LENGTH,
        **kwargs
    ) -> dict:
        """
        Generate a blog post from photos and metadata without saving.
        
        This is the core generation function that:
        1. Retrieves photos and their metadata
        2. Gets the writing style profile
        3. Builds comprehensive metadata context document
        4. Creates generation prompt with style instructions
        5. Calls Claude API for generation
        6. Parses generated title and body
        7. Returns post data (not yet saved to database)
        
        Args:
            user_id: ID of the user
            photo_ids: List of photo IDs to use for generation
            style_profile_id: Optional specific style profile ID (uses user's default if not provided)
            min_length: Minimum generated body length in characters
            max_length: Maximum generated body length in characters
            **kwargs: Additional parameters (e.g., category, tone preferences)
            
        Returns:
            Dictionary containing:
            - title: Generated post title
            - body: Generated post body
            - photo_ids: List of used photo IDs
            - metadata_snapshot: Snapshot of metadata used for generation
            - generation_params: Parameters used for this generation
            
        Raises:
            ValueError: If photos not found, invalid, or validation fails
            RuntimeError: If generation fails
        """
        logger.info(
            "Starting blog post generation",
            user_id=str(user_id),
            photo_count=len(photo_ids),
            style_profile_id=str(style_profile_id) if style_profile_id else "default",
        )
        
        try:
            # Step 1: Fetch photos and their metadata
            photos_data = await self._fetch_photos_with_metadata(user_id, photo_ids)
            if not photos_data:
                raise ValueError(f"No valid photos found for generation from photo_ids: {photo_ids}")
            
            logger.info(
                "Photos and metadata retrieved",
                user_id=str(user_id),
                valid_photos_count=len(photos_data),
            )
            
            # Step 2: Retrieve style profile
            style_profile = await self._get_style_profile(user_id, style_profile_id)
            if not style_profile:
                logger.info(
                    "No style profile found, using defaults",
                    user_id=str(user_id),
                )
                style_profile = self._get_default_style_profile()
            
            # Step 3: Build comprehensive metadata context document
            context_document = self._build_metadata_context_document(photos_data, style_profile)
            
            logger.debug(
                "Context document built",
                user_id=str(user_id),
                context_length=len(context_document),
            )
            
            # Step 4: Create generation prompt with style instructions
            generation_prompt = self._create_generation_prompt(
                context_document,
                style_profile,
                min_length,
                max_length,
                kwargs.get("category"),
                kwargs.get("tone"),
                posting_intent,
            )
            
            logger.debug(
                "Generation prompt created",
                user_id=str(user_id),
                prompt_length=len(generation_prompt),
            )
            
            # Step 5: Call Claude API (fallback to template if not configured)
            generated_content = await self._call_claude_for_generation(generation_prompt)
            if not generated_content:
                logger.warning(
                    "Claude API unavailable, using template-based draft generation",
                    user_id=str(user_id),
                )
                title, body = self._generate_template_draft(photos_data, kwargs.get("category"))
            else:
                # Step 6: Parse generated title and body
                title, body = self._parse_generated_content(generated_content)
            
            # Validate lengths (excluding markdown image syntax, since images
            # add visual content but don't count as "written" characters)
            text_only_length = self._text_length_excluding_images(body)
            
            if text_only_length < min_length:
                logger.warning(
                    "Generated body below minimum length",
                    user_id=str(user_id),
                    body_length=text_only_length,
                    min_length=min_length,
                )
            
            if text_only_length > max_length:
                logger.warning(
                    "Generated body exceeds maximum length, truncating",
                    user_id=str(user_id),
                    body_length=text_only_length,
                    max_length=max_length,
                )
                body = self._truncate_preserving_images(body, max_length)
            
            # Step 7: Build metadata snapshot for tracking
            metadata_snapshot = {
                "photo_ids": [str(p["photo_id"]) for p in photos_data],
                "metadata": [
                    {
                        "photo_id": str(p["photo_id"]),
                        "description": p.get("description"),
                        "location": p.get("location"),
                        "price": p.get("price"),
                        "category": p.get("category"),
                        "date": p.get("date").isoformat() if hasattr(p.get("date"), "isoformat") else p.get("date"),
                    }
                    for p in photos_data
                ],
                "style_profile_id": str(style_profile.get("profile_id")) if style_profile.get("profile_id") else None,
                "style_confidence": style_profile.get("confidence_score"),
            }
            
            # Return generated post data (not saved)
            result = {
                "title": title,
                "body": body,
                "photo_ids": photo_ids,
                "metadata_snapshot": metadata_snapshot,
                "generation_params": {
                    "model": self.DEFAULT_MODEL,
                    "min_length": min_length,
                    "max_length": max_length,
                    "category": kwargs.get("category"),
                    "tone": kwargs.get("tone"),
                },
            }
            
            logger.info(
                "Blog post generation completed successfully",
                user_id=str(user_id),
                title_length=len(title),
                body_length=len(body),
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "Blog post generation failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def _fetch_photos_with_metadata(
        self,
        user_id: UUID,
        photo_ids: List[UUID],
    ) -> List[dict]:
        """
        Fetch photos and their associated metadata from database.
        
        Args:
            user_id: ID of the user (for authorization check)
            photo_ids: List of photo IDs to retrieve
            
        Returns:
            List of photo data dictionaries with metadata, empty list if none found
        """
        photos_data = []
        
        for photo_id in photo_ids:
            try:
                # Get photo
                photo_stmt = select(Photo).where(
                    Photo.photo_id == photo_id,
                    Photo.user_id == user_id,
                )
                photo_result = await self.db.execute(photo_stmt)
                photo = photo_result.scalar_one_or_none()
                
                if not photo:
                    logger.warning(
                        "Photo not found or user not authorized",
                        user_id=str(user_id),
                        photo_id=str(photo_id),
                    )
                    continue
                
                # Get metadata
                metadata_stmt = select(PhotoMetadata).where(
                    PhotoMetadata.photo_id == photo_id
                )
                metadata_result = await self.db.execute(metadata_stmt)
                metadata = metadata_result.scalar_one_or_none()
                
                photos_data.append({
                    "photo_id": photo_id,
                    "s3_url": photo.s3_url,
                    "description": metadata.photo_description if metadata else None,
                    "location": (
                        metadata.location_information
                        if metadata and metadata.location_information
                        else None
                    ),
                    "price": (
                        metadata.price_information
                        if metadata and metadata.price_information
                        else None
                    ),
                    "category": metadata.category if metadata else None,
                    "date": metadata.date_and_time if metadata else None,
                })
            
            except Exception as e:
                logger.error(
                    "Error fetching photo metadata",
                    user_id=str(user_id),
                    photo_id=str(photo_id),
                    error=str(e),
                )
                continue
        
        return photos_data
    
    async def _get_style_profile(
        self,
        user_id: UUID,
        profile_id: Optional[UUID] = None,
    ) -> Optional[dict]:
        """
        Retrieve user's writing style profile from database.
        
        Args:
            user_id: ID of the user
            profile_id: Optional specific profile ID (uses default if not provided)
            
        Returns:
            Style profile dictionary or None if not found
        """
        try:
            if profile_id:
                stmt = select(WritingStyleProfile).where(
                    WritingStyleProfile.profile_id == profile_id,
                    WritingStyleProfile.blogger_id == user_id,
                )
            else:
                stmt = select(WritingStyleProfile).where(
                    WritingStyleProfile.blogger_id == user_id
                )
            
            result = await self.db.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                return None
            
            return {
                "profile_id": profile.profile_id,
                "vocabulary_patterns": profile.vocabulary_patterns,
                "sentence_structure": profile.sentence_structure,
                "tone_analysis": profile.tone_analysis,
                "formatting_rules": profile.formatting_rules,
                "characteristic_phrases": profile.characteristic_phrases,
                "avg_post_length": profile.avg_post_length,
                "keyword_frequency": profile.keyword_frequency,
                "confidence_score": profile.confidence_score,
            }
        
        except Exception as e:
            logger.error(
                "Error fetching style profile",
                user_id=str(user_id),
                error=str(e),
            )
            return None
    
    def _build_metadata_context_document(
        self,
        photos_data: List[dict],
        style_profile: dict,
    ) -> str:
        """
        Build comprehensive metadata context document for Claude prompt.
        
        Structures:
        - Photo descriptions and visual information
        - Location details (from metadata)
        - Price information (from metadata)
        - Category and date information
        - All metadata organized for easy reference
        
        Args:
            photos_data: List of photo data with metadata
            style_profile: User's writing style profile
            
        Returns:
            Formatted context document string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("BLOG POST GENERATION CONTEXT DOCUMENT")
        lines.append("=" * 80)
        lines.append("")
        
        # Section 1: Photos and Descriptions
        lines.append("SECTION 1: PHOTO INFORMATION")
        lines.append("-" * 80)
        for i, photo in enumerate(photos_data, 1):
            lines.append(f"\nPhoto {i}:")
            lines.append(f"  Description: {photo.get('description') or '[No description provided]'}")
            lines.append(f"  S3 URL: {photo.get('s3_url', 'N/A')}")
        
        # Section 2: Location Information
        lines.append("\n\n" + "=" * 80)
        lines.append("SECTION 2: LOCATION INFORMATION")
        lines.append("-" * 80)
        location_found = False
        for i, photo in enumerate(photos_data, 1):
            if photo.get("location"):
                location_found = True
                lines.append(f"\nPhoto {i} Location:")
                loc = photo["location"]
                if isinstance(loc, dict):
                    for key, value in loc.items():
                        lines.append(f"  {key}: {value}")
                else:
                    lines.append(f"  {loc}")
        
        if not location_found:
            lines.append("\n[No location information available]")
        
        # Section 3: Price Information
        lines.append("\n\n" + "=" * 80)
        lines.append("SECTION 3: PRICE INFORMATION")
        lines.append("-" * 80)
        price_found = False
        for i, photo in enumerate(photos_data, 1):
            if photo.get("price"):
                price_found = True
                lines.append(f"\nPhoto {i} Price:")
                price = photo["price"]
                if isinstance(price, dict):
                    for key, value in price.items():
                        lines.append(f"  {key}: {value}")
                else:
                    lines.append(f"  {price}")
        
        if not price_found:
            lines.append("\n[No price information available]")
        
        # Section 4: Categories and Metadata
        lines.append("\n\n" + "=" * 80)
        lines.append("SECTION 4: CATEGORIES AND DATES")
        lines.append("-" * 80)
        for i, photo in enumerate(photos_data, 1):
            lines.append(f"\nPhoto {i}:")
            lines.append(f"  Category: {photo.get('category') or '[Not specified]'}")
            lines.append(f"  Date: {photo.get('date') or '[Not specified]'}")
        
        # Section 5: Writing Style Profile
        lines.append("\n\n" + "=" * 80)
        lines.append("SECTION 5: WRITING STYLE PROFILE")
        lines.append("-" * 80)
        
        if style_profile.get("profile_id"):
            lines.append(f"\nConfidence Score: {style_profile.get('confidence_score', 0)}%")
            
            if style_profile.get("tone_analysis"):
                tone = style_profile["tone_analysis"]
                lines.append(f"\nTone: {', '.join(tone.get('tone_descriptors', ['neutral']))}")
                lines.append(f"Formal Level: {tone.get('formal_level', 0.5)}")
            
            if style_profile.get("vocabulary_patterns"):
                vocab = style_profile["vocabulary_patterns"]
                lines.append(f"\nVocabulary Complexity: {vocab.get('complexity', 'moderate')}")
            
            if style_profile.get("sentence_structure"):
                sent = style_profile["sentence_structure"]
                lines.append(f"Avg Sentence Length: {sent.get('avg_sentence_length', 15)} words")
            
            if style_profile.get("avg_post_length"):
                lines.append(f"Typical Post Length: {style_profile['avg_post_length']} characters")
            
            if style_profile.get("formatting_rules"):
                fmt = style_profile["formatting_rules"]
                if fmt.get("uses_bullet_points"):
                    lines.append("Uses bullet points: Yes")
                if fmt.get("section_headers"):
                    lines.append("Uses section headers: Yes")
            
            if style_profile.get("characteristic_phrases"):
                phrases = style_profile["characteristic_phrases"][:5]
                if phrases:
                    lines.append(f"\nCharacteristic phrases: {', '.join(phrases)}")
        else:
            lines.append("\n[Using default writing style]")
        
        lines.append("\n" + "=" * 80)
        lines.append("END OF CONTEXT DOCUMENT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _create_generation_prompt(
        self,
        context_document: str,
        style_profile: dict,
        min_length: int,
        max_length: int,
        category: Optional[str] = None,
        tone: Optional[str] = None,
        posting_intent: Optional[Dict] = None,
    ) -> str:
        """
        Create the generation prompt for Claude with context and instructions.
        
        Args:
            context_document: Metadata context document
            style_profile: Writing style profile
            min_length: Minimum body length
            max_length: Maximum body length
            category: Optional category hint
            tone: Optional tone hint
            posting_intent: Optional dict with user-provided topic/context that
                MUST be reflected in the generated content (not ignored)
            
        Returns:
            Formatted prompt for Claude
        """
        style_instructions = self._build_style_instructions(style_profile)
        
        # Build posting intent section - this is real user-provided context
        # and must take priority over guessing/inventing content
        intent_section = ""
        if posting_intent:
            intent_lines = ["\nSECTION 6: USER'S POSTING INTENT (HIGH PRIORITY)", "-" * 80]
            if posting_intent.get("topic"):
                intent_lines.append(f"Requested Topic: {posting_intent['topic']}")
            if posting_intent.get("additional_context"):
                intent_lines.append(f"Additional Context from User: {posting_intent['additional_context']}")
            intent_section = "\n".join(intent_lines)
        
        prompt = f"""You are an AI blog post generator. Your task is to generate a professional, 
informative blog post based ONLY on the provided context and metadata below.

{context_document}
{intent_section}

GENERATION INSTRUCTIONS:
{style_instructions}

CRITICAL ANTI-HALLUCINATION RULES:
1. Use ONLY the facts given in the context document and posting intent above.
2. If the user's posting intent (Section 6) is provided, the post MUST be about that
   topic and MUST use that context as the primary source of truth.
3. Do NOT invent details that are not present in the context (no fake prices, fake
   locations, fake dates, fake product names, or fake scenery descriptions).
4. If a piece of information (location, price, date) is marked as
   "[Not specified]" or "[No description provided]", do NOT make one up.
   Either omit that detail or write generically about it without inventing specifics.
5. If the photos are screenshots of an application/website (e.g. UI screens, tables,
   dashboards), describe them as what they actually show (feature, screen, data),
   not as a nature/travel/lifestyle photo.

IMAGE PLACEMENT REQUIREMENT:
- Each photo listed in SECTION 1 has an S3 URL. You MUST insert every photo directly
  into the body using markdown image syntax: ![short descriptive alt text](S3_URL)
- Distribute the images throughout the body near the paragraph that discusses that
  photo's content (not all at the top or all at the bottom).
- Use the exact S3 URL given in SECTION 1, unmodified.

REQUIREMENTS:
1. Post Length: Generate a blog post body between {min_length} and {max_length} characters
   (this count excludes the markdown image syntax itself)
2. Content Quality: Ensure the post is informative, well-structured, and engaging
3. Information Integration: Incorporate location, price, and description information
   where it is actually available; do not fabricate what is missing
4. Tone: Use the writing style specified above
5. Structure: Organize content with clear paragraphs and markdown headings
   (use ##, ### for section titles so structure is visually clear)
6. Title: Create a compelling, descriptive title (50-100 characters) that reflects
   the actual topic/posting intent, not a generic guess
7. Images: Follow the IMAGE PLACEMENT REQUIREMENT above

RESPONSE FORMAT:
Respond with ONLY valid JSON (no markdown code blocks around the JSON itself). Use this
exact structure:
{{
    "title": "Your Blog Post Title Here",
    "body": "Your full blog post body content here, including inline ![alt](url) images..."
}}

Notes:
- The body must be between {min_length} and {max_length} characters
- Ensure the JSON is valid and properly escaped (escape newlines as \\n, quotes as \\")
- Match the writing style from Section 5 of the context document
"""
        
        if category:
            prompt += f"\nCategory Focus: {category}\n"
        
        if tone:
            prompt += f"Specific Tone Preference: {tone}\n"
        
        prompt += "\nNow generate the blog post:"
        
        return prompt
    
    def _build_style_instructions(self, style_profile: dict) -> str:
        """
        Build style instructions from writing style profile.
        
        Args:
            style_profile: Style profile dictionary
            
        Returns:
            Style instructions string
        """
        if not style_profile or not style_profile.get("profile_id"):
            return "Use a professional, informative tone with clear structure and engaging language."
        
        instructions = []
        
        # Tone and attitude
        if style_profile.get("tone_analysis"):
            tone = style_profile["tone_analysis"]
            descriptors = tone.get("tone_descriptors", [])
            if descriptors:
                instructions.append(f"Tone: {', '.join(descriptors)}")
        
        # Vocabulary level
        if style_profile.get("vocabulary_patterns"):
            vocab = style_profile["vocabulary_patterns"]
            complexity = vocab.get("complexity", "moderate")
            if complexity == "simple":
                instructions.append("Use simple, accessible vocabulary")
            elif complexity == "complex":
                instructions.append("Use sophisticated vocabulary and technical terms where appropriate")
            else:
                instructions.append("Use moderate vocabulary appropriate for general audience")
        
        # Sentence structure
        if style_profile.get("sentence_structure"):
            sent = style_profile["sentence_structure"]
            avg_length = sent.get("avg_sentence_length", 15)
            if avg_length < 12:
                instructions.append("Use short, punchy sentences")
            elif avg_length > 20:
                instructions.append("Use longer, complex sentences with varied structure")
        
        # Formatting preferences
        if style_profile.get("formatting_rules"):
            fmt = style_profile["formatting_rules"]
            if fmt.get("uses_bullet_points"):
                instructions.append("Use bullet points for lists")
            if fmt.get("section_headers"):
                instructions.append("Organize content with clear section headers")
            if fmt.get("uses_numbered_lists"):
                instructions.append("Use numbered lists for ordered information")
        
        # Characteristic phrases
        if style_profile.get("characteristic_phrases"):
            phrases = style_profile["characteristic_phrases"][:3]
            if phrases:
                instructions.append(f"Incorporate style elements like: {', '.join(phrases)}")
        
        if not instructions:
            instructions.append("Use professional, informative tone with clear structure")
        
        return "\n".join(f"??{inst}" for inst in instructions)
    
    def _generate_template_draft(
        self,
        photos_data: List[dict],
        category: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Generate a simple template-based draft when Claude API is not configured.
        
        This produces a basic structured draft using photo metadata directly,
        intended for the user to copy and manually refine before publishing.
        
        Args:
            photos_data: List of photo metadata dictionaries
            category: Optional category label
            
        Returns:
            Tuple of (title, body)
        """
        topic_label = category or "사진 이야기"
        title = f"[초안] {topic_label} - 직접 작성해주세요"
        
        lines = []
        lines.append(f"# {topic_label}")
        lines.append("")
        lines.append(
            "이 글은 AI가 자동으로 생성한 것이 아니라, "
            "업로드된 사진 정보를 바탕으로 작성된 초안입니다. "
            "내용을 확인하고 직접 다듬어 주세요."
        )
        lines.append("")
        
        for idx, photo in enumerate(photos_data, 1):
            lines.append(f"## 사진 {idx}")
            if photo.get("description"):
                lines.append(f"- 설명: {photo['description']}")
            if photo.get("location"):
                lines.append(f"- 위치: {photo['location']}")
            if photo.get("price"):
                lines.append(f"- 가격/정보: {photo['price']}")
            if photo.get("category"):
                lines.append(f"- 추천 분류: {photo['category']}")
            if photo.get("date"):
                lines.append(f"- 날짜/시각: {photo['date']}")
            if not any(photo.get(k) for k in ("description", "location", "price", "category", "date")):
                lines.append("- (사진 분석 데이터가 없습니다. 직접 내용을 추가해주세요.)")
            lines.append("")
        
        lines.append("---")
        lines.append(
            "TIP: AI 기반 문장 생성을 사용하려면 CLAUDE_API_KEY를 "
            "환경 변수에 설정하세요."
        )
        
        body = "\n".join(lines)
        return title, body
    
    async def _call_claude_for_generation(self, prompt: str) -> Optional[str]:
        """
        Call Claude API to generate blog post.
        
        Args:
            prompt: The generation prompt
            
        Returns:
            Claude's response string or None if failed
        """
        try:
            response = await self.ai_client.call_claude(prompt)
            
            if response is None:
                logger.error("Claude API returned None")
                return None
            
            # If response is a dict (parsed JSON), convert back to string for parsing
            if isinstance(response, dict):
                return json.dumps(response, ensure_ascii=False)
            return str(response)
        
        except Exception as e:
            logger.error(
                "Error calling Claude API",
                error=str(e),
            )
            return None
    
    def _text_length_excluding_images(self, body: str) -> int:
        """
        Calculate body length excluding markdown image syntax.
        
        Markdown images (![alt](url)) add visual content to the post but
        contain a lot of characters (URLs) that shouldn\'t count toward the
        written-text length requirements.
        
        Args:
            body: The post body, potentially containing markdown images
            
        Returns:
            Character count of the body with image markdown removed
        """
        text_only = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
        return len(text_only)
    
    def _truncate_preserving_images(self, body: str, max_length: int) -> str:
        """
        Truncate body to max_length (measured in non-image text) without
        cutting a markdown image tag in half.
        
        Walks through the body, keeping track of the text-only character
        count, and stops at the last complete unit (word or full image tag)
        before exceeding max_length.
        
        Args:
            body: The post body to truncate
            max_length: Maximum allowed text-only length
            
        Returns:
            Truncated body with all remaining image tags intact
        """
        image_pattern = re.compile(r"!\[[^\]]*\]\([^)]*\)")
        
        result_parts = []
        text_count = 0
        pos = 0
        
        for match in image_pattern.finditer(body):
            # Handle the text segment before this image
            segment = body[pos:match.start()]
            if text_count + len(segment) > max_length:
                remaining = max_length - text_count
                truncated_segment = segment[:remaining].rsplit(" ", 1)[0]
                result_parts.append(truncated_segment)
                result_parts.append("...")
                return "".join(result_parts)
            result_parts.append(segment)
            text_count += len(segment)
            
            # Keep the full image tag (doesn\'t count toward text length)
            result_parts.append(match.group(0))
            pos = match.end()
        
        # Handle any remaining text after the last image
        segment = body[pos:]
        if text_count + len(segment) > max_length:
            remaining = max_length - text_count
            truncated_segment = segment[:remaining].rsplit(" ", 1)[0]
            result_parts.append(truncated_segment)
            result_parts.append("...")
        else:
            result_parts.append(segment)
        
        return "".join(result_parts)
    
    def _parse_generated_content(self, content: str) -> tuple[str, str]:
        """
        Parse generated content from Claude response.
        
        Expects JSON with "title" and "body" fields. Handles various formatting
        including markdown code blocks, extra whitespace, etc.
        
        Args:
            content: Raw response from Claude
            
        Returns:
            Tuple of (title, body)
            
        Raises:
            ValueError: If parsing fails
        """
        try:
            # Clean up the response
            cleaned = content.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith("```"):
                cleaned = re.sub(r"```json\s*", "", cleaned)
                cleaned = re.sub(r"```\s*", "", cleaned)
            
            # Parse JSON
            parsed = json.loads(cleaned)
            
            title = parsed.get("title", "").strip()
            body = parsed.get("body", "").strip()
            
            if not title or not body:
                raise ValueError("Missing title or body in parsed response")
            
            return title, body
        
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Claude response as JSON",
                error=str(e),
                content_preview=content[:200],
            )
            raise ValueError(f"Invalid JSON in Claude response: {e}")
        
        except Exception as e:
            logger.error(
                "Error parsing generated content",
                error=str(e),
            )
            raise ValueError(f"Failed to parse generated content: {e}")
    
    async def save_post(
        self,
        user_id: UUID,
        generated_data: dict,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> dict:
        """
        Save generated post to database.
        
        This method:
        1. Creates BlogPost record with status="draft"
        2. Creates blog_post_photos associations for each photo
        3. Stores metadata_snapshot with generation context
        4. Creates GenerationHistory entry for tracking
        5. Commits all data to database
        6. Returns post data for response
        
        Args:
            user_id: ID of the user
            generated_data: Dictionary from generate_blog_post() containing:
                - title: Generated post title
                - body: Generated post body
                - photo_ids: List of photo IDs used
                - metadata_snapshot: Snapshot of metadata used
                - generation_params: Parameters used for generation
            tags: Optional list of tags for the post
            category: Optional post category (can also be in generated_data)
            
        Returns:
            Dictionary containing:
            - post_id: UUID of created post
            - title: Post title
            - body: Post body
            - status: "draft"
            - tags: Associated tags
            - category: Post category
            - photo_ids: List of associated photo IDs
            - metadata_snapshot: Snapshot of metadata used
            - created_at: Creation timestamp
            - updated_at: Update timestamp
            
        Raises:
            ValueError: If generated_data missing required fields
            RuntimeError: If database operation fails
            
        Requirements:
            - Requirement 3.4, 3.5, 3.6: Blog post creation with metadata tracking
            - Requirement 5.1: Save draft posts with photo associations
            - Requirement 5.7: Store metadata snapshot for later analysis
        """
        logger.info(
            "Saving generated post to database",
            user_id=str(user_id),
            photo_count=len(generated_data.get("photo_ids", [])),
        )
        
        try:
            # Validate generated_data has required fields
            if not generated_data.get("title"):
                raise ValueError("Generated data missing title")
            if not generated_data.get("body"):
                raise ValueError("Generated data missing body")
            if not generated_data.get("photo_ids"):
                raise ValueError("Generated data missing photo_ids")
            
            # Create BlogPost record
            post_id = uuid4()
            now = datetime.utcnow()
            
            blog_post = BlogPost(
                post_id=post_id,
                user_id=user_id,
                title=generated_data["title"],
                body=generated_data["body"],
                tags=tags or [],
                category=category,
                status="draft",
                created_at=now,
                updated_at=now,
            )
            
            self.db.add(blog_post)
            await self.db.flush()  # Flush to ensure post is saved before adding relationships
            
            logger.info(
                "BlogPost record created",
                user_id=str(user_id),
                post_id=str(post_id),
            )
            
            # Create blog_post_photos associations
            photo_ids = generated_data.get("photo_ids", [])
            for display_order, photo_id in enumerate(photo_ids, start=1):
                blog_post_photo = BlogPostPhoto(
                    post_photo_id=uuid4(),
                    post_id=post_id,
                    photo_id=photo_id,
                    display_order=display_order,
                    created_at=now,
                )
                self.db.add(blog_post_photo)
            
            await self.db.flush()
            
            logger.info(
                "BlogPostPhoto associations created",
                user_id=str(user_id),
                post_id=str(post_id),
                photo_count=len(photo_ids),
            )
            
            # Create GenerationHistory entry for tracking
            raw_photo_ids = generated_data.get("photo_ids") or []
            generation_history = GenerationHistory(
                history_id=uuid4(),
                user_id=user_id,
                post_id=post_id,
                generation_date=now,
                source_photos=[str(pid) for pid in raw_photo_ids],
                source_metadata=generated_data.get("metadata_snapshot", {}).get("metadata"),
                generation_details=generated_data.get("generation_params"),
                generated_title=generated_data["title"],
                generated_body=generated_data["body"],
                status="draft",
                publication_status="not_published",
                created_at=now,
            )
            
            self.db.add(generation_history)
            await self.db.flush()
            
            logger.info(
                "GenerationHistory entry created",
                user_id=str(user_id),
                history_id=str(generation_history.history_id),
            )
            
            # Commit all changes
            await self.db.commit()
            
            logger.info(
                "Post saved successfully to database",
                user_id=str(user_id),
                post_id=str(post_id),
                title_length=len(generated_data["title"]),
                body_length=len(generated_data["body"]),
            )
            
            # Return post data for response
            return {
                "post_id": str(post_id),
                "title": generated_data["title"],
                "body": generated_data["body"],
                "status": "draft",
                "tags": tags or [],
                "category": category,
                "photo_ids": [str(p) for p in photo_ids],
                "metadata_snapshot": generated_data.get("metadata_snapshot"),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        
        except ValueError as e:
            logger.warning(
                "Invalid generated data for saving",
                user_id=str(user_id),
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to save post to database",
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            await self.db.rollback()
            raise RuntimeError(f"Failed to save post: {e}")
    
    async def generate_post(
        self,
        user_id: UUID,
        photo_ids: List[UUID],
        style_profile_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Generate and save a blog post in one operation.
        
        This is a convenience method that combines generate_blog_post and save_post.
        
        Args:
            user_id: ID of the user
            photo_ids: List of photo IDs to use
            style_profile_id: Optional style profile ID
            tags: Optional tags for the post
            category: Optional category for the post
            **kwargs: Additional parameters to pass to generate_blog_post
            
        Returns:
            Saved post data (same as save_post return value)
        """
        # Generate the post content
        generated_data = await self.generate_blog_post(
            user_id=user_id,
            photo_ids=photo_ids,
            style_profile_id=style_profile_id,
            **kwargs
        )
        
        # Save to database
        return await self.save_post(
            user_id=user_id,
            generated_data=generated_data,
            tags=tags,
            category=category,
        )
    
    def _get_default_style_profile(self) -> dict:
        """
        Return default style profile when none exists.
        
        Returns:
            Default style profile dictionary
        """
        return {
            "profile_id": None,
            "vocabulary_patterns": {
                "complexity": "moderate",
                "technical_terms": [],
                "avg_word_length": 5.0,
            },
            "sentence_structure": {
                "avg_sentence_length": 15,
                "sentence_types": ["simple", "complex"],
                "punctuation_style": "standard",
            },
            "tone_analysis": {
                "formal_level": 0.6,
                "friendly": True,
                "authoritative": False,
                "tone_descriptors": ["professional", "informative"],
            },
            "formatting_rules": {
                "uses_bullet_points": True,
                "uses_numbered_lists": False,
                "paragraph_avg_length": 100,
                "section_headers": True,
            },
            "characteristic_phrases": [],
            "avg_post_length": 1000,
            "keyword_frequency": {},
            "confidence_score": 30,
        }





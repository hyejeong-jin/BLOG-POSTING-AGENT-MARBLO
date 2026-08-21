"""
Writing Style Learning and Profile Management Service.

This service handles learning and managing blogger writing styles from uploaded posts.
It combines blog post samples, analyzes them with Claude API, and creates compressed
writing style profiles stored in the database.
"""

import json
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import WritingStyleProfile
from app.utils.ai_client import AIClient
from app.logging_config import get_logger

logger = get_logger(__name__)


class StyleService:
    """Service for managing writing style profiles."""
    
    # Minimum samples required for meaningful analysis
    MIN_SAMPLES_FOR_ANALYSIS = 1
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the style service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.ai_client = AIClient()
    
    async def learn_writing_style(
        self,
        blogger_id: UUID,
        blog_post_samples: list[str],
    ) -> dict:
        """
        Learn writing style from blog post samples.
        
        This is the core function that:
        1. Combines uploaded blog post samples
        2. Calls Claude API with style analysis prompt
        3. Extracts writing characteristics (vocabulary level, sentence structure, 
           tone, common phrases, formatting preferences)
        4. Creates compressed profile data
        5. Stores WritingStyleProfile in database
        
        Args:
            blogger_id: ID of the blogger
            blog_post_samples: List of blog post text samples for analysis
            
        Returns:
            Dictionary with profile_id, confidence_score, and sample_posts_count
            
        Raises:
            ValueError: If samples are empty or invalid
        """
        if not blog_post_samples or len(blog_post_samples) == 0:
            raise ValueError("At least one blog post sample is required for style learning")
        
        # Filter out empty or very short samples
        valid_samples = [
            sample for sample in blog_post_samples
            if sample and len(sample.strip()) > 50
        ]
        
        if not valid_samples:
            raise ValueError("Blog post samples must contain meaningful content (at least 50 characters each)")
        
        logger.info(
            "Starting writing style learning",
            blogger_id=str(blogger_id),
            sample_count=len(valid_samples),
            total_length=sum(len(s) for s in valid_samples),
        )
        
        try:
            # Combine samples
            combined_text = self._combine_samples(valid_samples)
            
            # Call Claude API for style analysis
            style_analysis = await self._analyze_style_with_claude(combined_text, len(valid_samples))
            
            # Get or create profile
            profile = await self._get_or_create_profile(blogger_id)
            
            # Update profile with analysis results
            self._update_profile_with_analysis(profile, style_analysis, len(valid_samples))
            
            # Save to database
            self.db.add(profile)
            await self.db.flush()
            
            logger.info(
                "Writing style learning completed",
                blogger_id=str(blogger_id),
                profile_id=str(profile.profile_id),
                confidence_score=profile.confidence_score,
            )
            
            return {
                "profile_id": str(profile.profile_id),
                "confidence_score": profile.confidence_score,
                "sample_posts_count": profile.sample_posts_count,
            }
        
        except Exception as e:
            logger.error(
                "Writing style learning failed",
                blogger_id=str(blogger_id),
                error=str(e),
            )
            raise
    
    async def upload_and_analyze_samples(
        self,
        blogger_id: UUID,
        samples_text: str,
    ) -> dict:
        """
        Upload blog post samples and perform style analysis.
        
        Legacy method that accepts combined text and splits it into samples.
        
        Args:
            blogger_id: ID of the blogger
            samples_text: Combined text of blog posts for analysis
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            ValueError: If samples are empty or invalid
        """
        if not samples_text or len(samples_text.strip()) == 0:
            raise ValueError("Blog post samples cannot be empty")
        
        # Split combined text into samples by common separators
        samples = self._split_combined_text(samples_text)
        
        # Delegate to learn_writing_style
        return await self.learn_writing_style(blogger_id, samples)
    
    def _combine_samples(self, samples: list[str]) -> str:
        """
        Combine multiple blog post samples into a single text for analysis.
        
        Args:
            samples: List of blog post samples
            
        Returns:
            Combined text with clear separators
        """
        separator = "\n\n" + ("=" * 80) + "\n\n"
        return separator.join(samples)
    
    def _split_combined_text(self, combined_text: str) -> list[str]:
        """
        Split combined text into individual samples.
        
        Supports multiple separators like blank lines with dashes/equals.
        
        Args:
            combined_text: Combined blog post text
            
        Returns:
            List of individual samples
        """
        # Try to split by common separators first
        separators = [
            r"\n\s*={3,}\s*\n",  # === separator
            r"\n\s*-{3,}\s*\n",   # --- separator
            r"\n\s*\*{3,}\s*\n",  # *** separator
            r"\n\n{2,}",          # Multiple blank lines
        ]
        
        samples = [combined_text]
        
        for separator in separators:
            new_samples = []
            for sample in samples:
                parts = re.split(separator, sample)
                new_samples.extend([p.strip() for p in parts if p.strip()])
            samples = new_samples
            
            if len(samples) > 1:
                break
        
        # If still just one sample, try splitting by common blog markers
        if len(samples) <= 1:
            # Split by "Post X", "Blog X", etc.
            samples = re.split(r"\n(?:Post|Blog|Article|Entry)\s*[\d:]+\n", combined_text)
        
        # Filter to valid samples
        samples = [s.strip() for s in samples if s.strip() and len(s.strip()) > 50]
        
        return samples if samples else [combined_text.strip()]
    
    async def _analyze_style_with_claude(
        self,
        combined_text: str,
        sample_count: int,
    ) -> dict:
        """
        Use Claude API to analyze writing style from samples.
        
        Extracts:
        - Vocabulary level and patterns
        - Sentence structure
        - Tone and attitude
        - Common phrases
        - Formatting preferences
        
        Args:
            combined_text: Combined blog post samples
            sample_count: Number of individual samples
            
        Returns:
            Dictionary with extracted style characteristics
        """
        prompt = f"""Analyze the following {sample_count} blog post samples and extract writing style characteristics.
        
Blog Post Samples:
{combined_text[:5000]}

Please analyze and return ONLY a valid JSON object (no markdown formatting) with exactly these fields:
{{
    "vocabulary_patterns": {{
        "complexity": "simple/moderate/complex",
        "technical_terms": ["term1", "term2"],
        "avg_word_length": 5.5
    }},
    "sentence_structure": {{
        "avg_sentence_length": 15,
        "sentence_types": ["simple", "complex"],
        "punctuation_style": "description"
    }},
    "tone_analysis": {{
        "formal_level": 0.7,
        "friendly": true,
        "authoritative": true,
        "tone_descriptors": ["professional", "informative"]
    }},
    "formatting_rules": {{
        "uses_bullet_points": true,
        "uses_numbered_lists": true,
        "paragraph_avg_length": 100,
        "section_headers": true
    }},
    "characteristic_phrases": ["phrase1", "phrase2"],
    "avg_post_length": 1500,
    "keyword_frequency": {{"keyword1": 5, "keyword2": 3}},
    "sample_posts_count": {sample_count},
    "confidence_score": 75
}}

Requirements:
- All numeric values must be reasonable (0-100 for scores, positive for lengths)
- confidence_score reflects confidence in analysis (0-100)
- Return ONLY the JSON object, no other text or markdown
- Ensure valid JSON that can be parsed"""
        
        response = await self.ai_client.call_claude(prompt)
        
        if response is None:
            logger.warning("Claude API returned None, using default analysis")
            return self._get_default_style_analysis(sample_count)
        
        try:
            # Handle both string and dict responses
            if isinstance(response, dict):
                result = response
            else:
                # Extract JSON from response (handle cases where Claude adds markdown)
                json_str = str(response).strip()
                
                # Remove markdown code blocks if present
                if json_str.startswith("```"):
                    json_str = re.sub(r"```json\s*", "", json_str)
                    json_str = re.sub(r"```\s*", "", json_str)
                
                result = json.loads(json_str)
            
            # Validate required fields
            result.setdefault("sample_posts_count", sample_count)
            result.setdefault("confidence_score", 50)
            
            # Ensure confidence score is in valid range
            if not isinstance(result.get("confidence_score"), (int, float)):
                result["confidence_score"] = 50
            else:
                result["confidence_score"] = min(100, max(0, int(result["confidence_score"])))
            
            # Ensure sample count matches
            result["sample_posts_count"] = sample_count
            
            logger.info("Claude style analysis completed successfully")
            return result
        
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse Claude response as JSON, using defaults",
                error=str(e),
            )
            return self._get_default_style_analysis(sample_count)
    
    def _update_profile_with_analysis(
        self,
        profile: WritingStyleProfile,
        analysis: dict,
        sample_count: int,
    ) -> None:
        """
        Update a WritingStyleProfile with analysis results.
        
        Args:
            profile: WritingStyleProfile instance to update
            analysis: Analysis results from Claude
            sample_count: Number of samples analyzed
        """
        profile.vocabulary_patterns = analysis.get("vocabulary_patterns")
        profile.sentence_structure = analysis.get("sentence_structure")
        profile.tone_analysis = analysis.get("tone_analysis")
        profile.formatting_rules = analysis.get("formatting_rules")
        profile.characteristic_phrases = analysis.get("characteristic_phrases")
        profile.avg_post_length = analysis.get("avg_post_length")
        profile.keyword_frequency = analysis.get("keyword_frequency")
        profile.sample_posts_count = sample_count
        profile.confidence_score = int(analysis.get("confidence_score", 50))
        profile.updated_at = datetime.utcnow()
        profile.last_refined_at = datetime.utcnow()
    
    async def _get_or_create_profile(self, blogger_id: UUID) -> WritingStyleProfile:
        """
        Get existing profile or create a new one.
        
        Args:
            blogger_id: ID of the blogger
            
        Returns:
            WritingStyleProfile instance
        """
        stmt = select(WritingStyleProfile).where(
            WritingStyleProfile.blogger_id == blogger_id
        )
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = WritingStyleProfile(
                blogger_id=blogger_id,
                sample_posts_count=0,
                confidence_score=0,
            )
        
        return profile
    
    async def get_profile(self, blogger_id: UUID) -> Optional[dict]:
        """
        Retrieve writing style profile for a blogger.
        
        Args:
            blogger_id: ID of the blogger
            
        Returns:
            Profile dictionary or None if not found
        """
        stmt = select(WritingStyleProfile).where(
            WritingStyleProfile.blogger_id == blogger_id
        )
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        return {
            "profile_id": str(profile.profile_id),
            "blogger_id": str(profile.blogger_id),
            "vocabulary_patterns": profile.vocabulary_patterns,
            "sentence_structure": profile.sentence_structure,
            "tone_analysis": profile.tone_analysis,
            "formatting_rules": profile.formatting_rules,
            "characteristic_phrases": profile.characteristic_phrases,
            "avg_post_length": profile.avg_post_length,
            "keyword_frequency": profile.keyword_frequency,
            "sample_posts_count": profile.sample_posts_count,
            "confidence_score": profile.confidence_score,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "last_refined_at": profile.last_refined_at,
        }
    
    async def update_profile(
        self,
        blogger_id: UUID,
        updates: dict,
    ) -> dict:
        """
        Update writing style profile with manual adjustments.
        
        Args:
            blogger_id: ID of the blogger
            updates: Dictionary with fields to update
            
        Returns:
            Updated profile dictionary
        """
        profile = await self._get_or_create_profile(blogger_id)
        
        # Update allowed fields
        allowed_fields = {
            "vocabulary_patterns",
            "sentence_structure",
            "tone_analysis",
            "formatting_rules",
            "characteristic_phrases",
            "avg_post_length",
        }
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        self.db.add(profile)
        await self.db.flush()
        
        logger.info(
            "Style profile updated",
            blogger_id=str(blogger_id),
        )
        
        return await self.get_profile(blogger_id)
    
    def _get_default_style_analysis(self, sample_count: int = 1) -> dict:
        """
        Return default style analysis when parsing fails.
        
        Args:
            sample_count: Number of samples (for consistency)
        
        Returns:
            Default analysis dictionary
        """
        return {
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
                "formal_level": 0.5,
                "friendly": True,
                "authoritative": False,
                "tone_descriptors": ["neutral", "informative"],
            },
            "formatting_rules": {
                "uses_bullet_points": False,
                "uses_numbered_lists": False,
                "paragraph_avg_length": 100,
                "section_headers": True,
            },
            "characteristic_phrases": [],
            "avg_post_length": 1000,
            "keyword_frequency": {},
            "sample_posts_count": sample_count,
            "confidence_score": 30,
        }



"""
Blog Post Export and Publishing Service.

This service handles exporting posts to various formats and publishing to external platforms.
Supports Markdown, HTML, and plain text export formats with metadata preservation.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import UUID
import json
import html

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import BlogPost, BlogPostPhoto, Photo, PhotoMetadata, GenerationHistory
from app.logging_config import get_logger

logger = get_logger(__name__)


class ExportService:
    """Service for exporting and publishing blog posts."""
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the export service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    async def export_to_markdown(self, post_id: UUID, user_id: UUID) -> str:
        """
        Export post to Markdown format with metadata as frontmatter.
        
        Preserves metadata including location, price, and description information
        extracted from associated photos.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user
            
        Returns:
            Markdown formatted content with YAML frontmatter
            
        Raises:
            ValueError: If post not found
            
        Requirements:
            - Requirement 8.1: Export to Markdown format
            - Requirement 8.3: Include metadata in appropriate format
        """
        post = await self._get_post(post_id, user_id)
        
        # Get associated photos and metadata
        photos_metadata = await self._get_photos_metadata(post_id)
        
        # Build metadata frontmatter
        tags_str = ', '.join(post.tags) if post.tags else 'None'
        frontmatter_lines = [
            "---",
            f"title: {post.title}",
            f"date: {post.created_at.isoformat()}",
            f"category: {post.category or 'General'}",
            f"tags: {tags_str}",
        ]
        
        # Add metadata if present
        if photos_metadata:
            frontmatter_lines.append("metadata:")
            
            # Add location information
            locations = []
            prices = []
            for metadata in photos_metadata:
                if metadata.get("location_information"):
                    loc = metadata["location_information"]
                    if isinstance(loc, dict):
                        visible_loc = loc.get("visible_location")
                        if visible_loc:
                            locations.append(visible_loc)
                    elif isinstance(loc, str):
                        locations.append(loc)
                
                if metadata.get("price_information"):
                    price = metadata["price_information"]
                    if isinstance(price, dict):
                        amount = price.get("amount")
                        currency = price.get("currency", "KRW")
                        if amount:
                            prices.append(f"{amount} {currency}")
                    elif isinstance(price, str):
                        prices.append(price)
            
            if locations:
                frontmatter_lines.append(f"  locations: [{', '.join(set(locations))}]")
            if prices:
                frontmatter_lines.append(f"  prices: [{', '.join(set(prices))}]")
            
            # Add photo descriptions
            descriptions = [m.get("photo_description") for m in photos_metadata if m.get("photo_description")]
            if descriptions:
                frontmatter_lines.append(f"  photos: {len(descriptions)}")
        
        frontmatter_lines.append("---")
        frontmatter = "\n".join(frontmatter_lines) + "\n\n"
        
        # Add photos section if available
        photos_section = ""
        if photos_metadata:
            photos_section = "## Photos\n\n"
            for i, metadata in enumerate(photos_metadata, 1):
                if metadata.get("s3_url"):
                    photos_section += f"![Photo {i}]({metadata['s3_url']})\n"
                if metadata.get("photo_description"):
                    photos_section += f"*{metadata['photo_description']}*\n\n"
            photos_section += "\n"
        
        # Add body
        markdown = frontmatter + photos_section + post.body
        
        logger.info(
            "Post exported to Markdown",
            post_id=str(post_id),
            user_id=str(user_id),
            content_length=len(markdown),
            has_metadata=bool(photos_metadata),
        )
        
        return markdown
    
    async def export_to_html(self, post_id: UUID, user_id: UUID) -> str:
        """
        Export post to HTML format.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user
            
        Returns:
            HTML formatted content
            
        Raises:
            ValueError: If post not found
        """
        post = await self._get_post(post_id, user_id)
        
        # Get associated photos
        photos_html = await self._get_photos_html(post_id)
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ margin-bottom: 30px; }}
        .title {{ font-size: 2em; margin-bottom: 10px; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        .content {{ line-height: 1.8; }}
        .photos {{ margin: 20px 0; }}
        .photo {{ margin: 10px 0; }}
        .photo img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">{post.title}</h1>
            <div class="meta">
                <p>?�성?? {post.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p>카테고리: {post.category or 'General'}</p>
                {f'<p>?�그: {", ".join(post.tags)}</p>' if post.tags else ''}
            </div>
        </div>
        
        {photos_html}
        
        <div class="content">
            {post.body.replace(chr(10), '<br/>')}
        </div>
    </div>
</body>
</html>"""
        
        logger.info(
            "Post exported to HTML",
            post_id=str(post_id),
            user_id=str(user_id),
            content_length=len(html),
        )
        
        return html
    
    async def export_to_plaintext(self, post_id: UUID, user_id: UUID) -> str:
        """
        Export post to plain text format.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user
            
        Returns:
            Plain text formatted content
            
        Raises:
            ValueError: If post not found
        """
        post = await self._get_post(post_id, user_id)
        
        # Build text
        text = f"""{post.title}

?�성?? {post.created_at.strftime('%Y-%m-%d %H:%M')}
카테고리: {post.category or 'General'}
{f'?�그: {", ".join(post.tags)}' if post.tags else ''}

?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━?�━

{post.body}

"""
        
        logger.info(
            "Post exported to plain text",
            post_id=str(post_id),
            user_id=str(user_id),
            content_length=len(text),
        )
        
        return text
    
    async def publish_to_naver(
        self,
        post_id: UUID,
        user_id: UUID,
        naver_config: dict,
    ) -> dict:
        """
        Publish post to Naver Blog.
        
        For simplified implementation, this just updates the post status.
        In production, would call Naver Blog API.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user
            naver_config: Naver configuration (blog_id, oauth_token, etc.)
            
        Returns:
            Publication result
            
        Raises:
            ValueError: If post not found or publication fails
        """
        post = await self._get_post(post_id, user_id)
        
        # In simplified version, just update status
        post.status = "published"
        post.publication_platform = "naver_blog"
        post.published_at = datetime.utcnow()
        
        # Generate mock published URL
        post.published_url = f"https://blog.naver.com/[blog_id]/{post_id}"
        
        self.db.add(post)
        await self.db.flush()
        
        logger.info(
            "Post published to Naver",
            post_id=str(post_id),
            user_id=str(user_id),
            platform="naver_blog",
        )
        
        return {
            "post_id": str(post.post_id),
            "status": "published",
            "platform": "naver_blog",
            "published_url": post.published_url,
            "published_at": post.published_at,
        }
    
    async def _get_post(self, post_id: UUID, user_id: UUID) -> BlogPost:
        """
        Get post by ID with authorization check.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user
            
        Returns:
            BlogPost instance
            
        Raises:
            ValueError: If post not found or unauthorized
        """
        stmt = select(BlogPost).where(
            BlogPost.post_id == post_id,
            BlogPost.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            raise ValueError("Post not found or unauthorized")
        
        return post
    
    async def _get_photos_html(self, post_id: UUID) -> str:
        """
        Generate HTML for post's photos.
        
        Args:
            post_id: ID of the post
            
        Returns:
            HTML string with photos
        """
        stmt = select(BlogPostPhoto).where(
            BlogPostPhoto.post_id == post_id
        ).order_by(BlogPostPhoto.display_order)
        
        result = await self.db.execute(stmt)
        post_photos = result.scalars().all()
        
        if not post_photos:
            return ""
        
        html_parts = ['<div class="photos">']
        
        for post_photo in post_photos:
            # Get photo
            photo_stmt = select(Photo).where(Photo.photo_id == post_photo.photo_id)
            photo_result = await self.db.execute(photo_stmt)
            photo = photo_result.scalar_one_or_none()
            
            if not photo:
                continue
            
            # Get metadata
            metadata_stmt = select(PhotoMetadata).where(
                PhotoMetadata.photo_id == post_photo.photo_id
            )
            metadata_result = await self.db.execute(metadata_stmt)
            metadata = metadata_result.scalar_one_or_none()
            
            # Build photo HTML
            description = metadata.photo_description if metadata else ""
            html_parts.append(f'<div class="photo">')
            html_parts.append(f'<img src="{photo.s3_url}" alt="{description}">')
            if description:
                html_parts.append(f'<p><em>{description}</em></p>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return "\n".join(html_parts)



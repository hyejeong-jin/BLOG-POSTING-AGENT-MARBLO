"""
Blog scraper for learning writing style from external blogs.

Supports scraping posts from Naver blogs using the RSS feed to discover
recent posts, and the mobile blog view to extract post content without
needing to deal with the iframe-based desktop layout.
"""

import re
from typing import Optional
from datetime import datetime
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup

from app.logging_config import get_logger

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class BlogScraper:
    """Naver blog scraper for writing style learning."""

    @staticmethod
    def _extract_blog_id(blog_url: str) -> Optional[str]:
        """
        Extract the Naver blog ID from a blog URL.

        Supports formats like:
        - https://blog.naver.com/{blogId}
        - https://m.blog.naver.com/{blogId}
        - blog.naver.com/{blogId}/{logNo}

        Args:
            blog_url: The blog URL provided by the user

        Returns:
            The blog ID string, or None if it could not be parsed
        """
        match = re.search(r"blog\.naver\.com/([a-zA-Z0-9_-]+)", blog_url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    async def _fetch_recent_log_numbers(blog_id: str, post_count: int) -> list[str]:
        """
        Fetch recent post identifiers (logNo) for a blog via its RSS feed.

        Args:
            blog_id: Naver blog ID
            post_count: Maximum number of posts to retrieve

        Returns:
            List of logNo strings, most recent first
        """
        rss_url = f"https://rss.blog.naver.com/{blog_id}.xml"
        log_numbers: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": USER_AGENT}) as client:
                response = await client.get(rss_url)

            if response.status_code != 200 or not response.text.strip():
                logger.warning(
                    "Naver RSS feed unavailable or empty",
                    blog_id=blog_id,
                    status=response.status_code,
                )
                return []

            root = ElementTree.fromstring(response.text)
            for item in root.iter("item"):
                link_elem = item.find("link")
                if link_elem is None or not link_elem.text:
                    continue
                match = re.search(r"blog\.naver\.com/[^/]+/(\d+)", link_elem.text) or re.search(r"logNo=(\d+)", link_elem.text)
                if match:
                    log_numbers.append(match.group(1))
                if len(log_numbers) >= post_count:
                    break

        except Exception as e:
            logger.error("Failed to fetch or parse Naver RSS feed", blog_id=blog_id, error=str(e))
            return []

        return log_numbers

    @staticmethod
    async def _fetch_post_text(blog_id: str, log_no: str) -> Optional[str]:
        """
        Fetch and extract the plain text content of a single Naver blog post.

        Uses the mobile blog view, which renders post content directly in the
        page (no iframe), making it straightforward to parse.

        Args:
            blog_id: Naver blog ID
            log_no: Post identifier

        Returns:
            Extracted plain text content, or None if extraction failed
        """
        mobile_url = f"https://m.blog.naver.com/{blog_id}/{log_no}"

        try:
            async with httpx.AsyncClient(
                timeout=15, headers={"User-Agent": USER_AGENT}, follow_redirects=True
            ) as client:
                response = await client.get(mobile_url)

            if response.status_code != 200:
                logger.warning(
                    "Failed to fetch Naver mobile post",
                    blog_id=blog_id,
                    log_no=log_no,
                    status=response.status_code,
                )
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Try known Naver blog content container selectors, from newest
            # editor format to oldest, with a generic fallback last.
            selectors = [
                "div.se-main-container",
                "div#postViewArea",
                "div.post_ct",
                "div#viewTypeSelector",
                "article",
            ]
            content_div = None
            for selector in selectors:
                content_div = soup.select_one(selector)
                if content_div is not None:
                    break

            if content_div is None:
                logger.warning(
                    "Could not locate post content container",
                    blog_id=blog_id,
                    log_no=log_no,
                )
                return None

            text = content_div.get_text(separator="\n", strip=True)
            return text if text else None

        except Exception as e:
            logger.error(
                "Error fetching Naver blog post",
                blog_id=blog_id,
                log_no=log_no,
                error=str(e),
            )
            return None

    @staticmethod
    async def scrape_naver_blog(blog_url: str, post_count: int = 5) -> dict:
        """
        Scrape recent posts from a Naver blog for writing style analysis.

        Discovers recent posts via the blog's RSS feed, then fetches and
        extracts text content from each post's mobile view.

        Args:
            blog_url: Blog URL (e.g., https://blog.naver.com/username)
            post_count: Number of posts to scrape

        Returns:
            Dictionary with scraped posts. If scraping fails entirely,
            posts_scraped will be 0 and combined_text will be empty.
        """
        logger.info(f"Scraping Naver blog: {blog_url}", post_count=post_count)

        blog_id = BlogScraper._extract_blog_id(blog_url)
        if not blog_id:
            logger.warning("Could not extract blog ID from URL", blog_url=blog_url)
            return {
                "blog_url": blog_url,
                "posts_scraped": 0,
                "combined_text": "",
                "scrape_date": datetime.utcnow().isoformat(),
            }

        log_numbers = await BlogScraper._fetch_recent_log_numbers(blog_id, post_count)

        collected_posts: list[str] = []
        for log_no in log_numbers:
            post_text = await BlogScraper._fetch_post_text(blog_id, log_no)
            if post_text:
                collected_posts.append(post_text)
            if len(collected_posts) >= post_count:
                break

        combined_text = "\n\n---\n\n".join(collected_posts)

        logger.info(
            "Naver blog scraping completed",
            blog_id=blog_id,
            requested=post_count,
            found=len(collected_posts),
        )

        return {
            "blog_url": blog_url,
            "posts_scraped": len(collected_posts),
            "combined_text": combined_text,
            "scrape_date": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def scrape_blog(blog_url: str, post_count: int = 5) -> dict:
        """
        Generic blog scraper that detects blog type.

        Args:
            blog_url: Blog URL
            post_count: Number of posts to scrape

        Returns:
            Dictionary with scraped posts
        """
        if "naver" in blog_url.lower():
            return await BlogScraper.scrape_naver_blog(blog_url, post_count)
        else:
            # Default to Naver for now (MVP)
            return await BlogScraper.scrape_naver_blog(blog_url, post_count)

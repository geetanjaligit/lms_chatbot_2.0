"""
Web Crawler for Sharda University Website
Uses crawl4ai for dynamic, JavaScript-enabled crawling
"""

import asyncio
import os
from typing import List, Tuple, Set
from urllib.parse import urlparse, urljoin
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class ShardaWebCrawler:
    def __init__(self, start_url: str = "https://www.sharda.ac.in/", max_pages: int = 150):
        self.start_url = start_url
        self.max_pages = max_pages
        self.domain = urlparse(start_url).netloc
        self.visited_urls: Set[str] = set()

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to Sharda domain and is valid"""
        try:
            parsed = urlparse(url)
            if parsed.netloc != self.domain:
                return False
            # Skip certain file types but keep PDFs if we want depth (optional)
            skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.zip', '.exe']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            return True
        except:
            return False

    async def crawl_recursive(self) -> List[Tuple[str, str]]:
        """
        Crawl the website using crawl4ai
        """
        pages_data = []
        to_visit = [self.start_url]
        
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            # Removed wait_for since it was being misinterpreted
            # Default behavior generally handles load event
            remove_overlay_elements=True
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            while to_visit and len(self.visited_urls) < self.max_pages:
                url = to_visit.pop(0)
                if url in self.visited_urls or not self.is_valid_url(url):
                    continue
                
                self.visited_urls.add(url)
                print(f"Crawling ({len(self.visited_urls)}/{self.max_pages}): {url}")
                
                try:
                    result = await crawler.arun(url=url, config=run_config)
                    if result.success:
                        # Use markdown or text content
                        content = result.markdown or result.extracted_content or ""
                        if len(content) > 50:
                            pages_data.append((url, content))
                            print(f"  OK Extracted {len(content)} characters")
                        
                            # Extract links for recursive crawling
                            # Note: crawl4ai result has links in various formats
                            # For simplicity, we can use the links provided by crawl4ai if available
                            # or just use result.internal_links if implemented
                            if hasattr(result, 'links') and 'internal' in result.links:
                                for link in result.links['internal']:
                                    new_url = link['href']
                                    if new_url not in self.visited_urls and new_url not in to_visit:
                                        if self.is_valid_url(new_url):
                                            to_visit.append(new_url)
                    else:
                        print(f"  FAIL: {result.error_message}")
                except Exception as e:
                    print(f"  FAIL: {e}")
                
                # Small delay to be respectful
                await asyncio.sleep(0.5)

        return pages_data

def crawl_sharda_website(max_pages: int = 150) -> List[Tuple[str, str]]:
    """
    Synchronous wrapper for the async crawler
    """
    crawler = ShardaWebCrawler(max_pages=max_pages)
    return asyncio.run(crawler.crawl_recursive())

if __name__ == "__main__":
    # Test with 5 pages
    data = crawl_sharda_website(max_pages=5)
    print(f"\nCrawled {len(data)} pages.")
    for url, content in data:
        print(f"URL: {url} | Content length: {len(content)}")

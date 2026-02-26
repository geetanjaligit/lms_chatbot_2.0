"""
Web Crawler for Sharda University Website
Uses BeautifulSoup and requests for lightweight crawling
"""

import requests
import time
from typing import List, Tuple, Set
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

class ShardaWebCrawler:
    def __init__(self, start_url: str = "https://www.sharda.ac.in/", max_pages: int = 150):
        self.start_url = start_url
        self.max_pages = max_pages
        self.domain = urlparse(start_url).netloc
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to Sharda domain and is valid"""
        try:
            parsed = urlparse(url)
            if parsed.netloc != self.domain:
                return False
            # Skip certain file types
            skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.zip', '.exe', '.pdf']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            return True
        except:
            return False

    def extract_text_from_page(self, html: str) -> str:
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        # Get text
        text = soup.get_text(separator=' ')
        # Break into lines and remove leading/trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text

    def crawl(self) -> List[Tuple[str, str]]:
        """
        Crawl the website using requests and BeautifulSoup
        """
        to_visit = [self.start_url]
        pages_data = []
        
        print(f"Starting crawl of {self.domain}...")
        print(f"Max pages to crawl: {self.max_pages}\n")
        
        while to_visit and len(self.visited_urls) < self.max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited_urls or not self.is_valid_url(url):
                continue
                
            self.visited_urls.add(url)
            
            try:
                print(f"Crawling ({len(self.visited_urls)}/{self.max_pages}): {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                text = self.extract_text_from_page(response.text)
                
                if text and len(text) > 50:
                    pages_data.append((url, text))
                    print(f"  OK Extracted {len(text)} characters")
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        new_url = urljoin(url, link['href'])
                        new_url = new_url.split('#')[0]
                        
                        if new_url not in self.visited_urls and new_url not in to_visit:
                            if self.is_valid_url(new_url):
                                to_visit.append(new_url)
                else:
                    print(f"  - Skipped (insufficient content)")
                
                time.sleep(0.5) # Be respectful
                
            except Exception as e:
                print(f"  FAIL Error: {e}")
                self.failed_urls.add(url)
                
        return pages_data

def crawl_sharda_website(max_pages: int = 150) -> List[Tuple[str, str]]:
    """
    Synchronous wrapper for the crawler
    """
    crawler = ShardaWebCrawler(max_pages=max_pages)
    return crawler.crawl()

if __name__ == "__main__":
    data = crawl_sharda_website(max_pages=5)
    print(f"\nCrawled {len(data)} pages.")

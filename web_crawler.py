"""
Web Crawler for Sharda University Website
Crawls the Sharda University website and extracts text content
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Set, List, Tuple

class ShardaWebCrawler:
    def __init__(self, start_url: str = "https://www.sharda.ac.in/", max_pages: int = 100):
        """
        Initialize the web crawler
        
        Args:
            start_url: Starting URL for crawling
            max_pages: Maximum number of pages to crawl
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.domain = urlparse(start_url).netloc
        
        # Headers to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to Sharda domain and is valid"""
        try:
            parsed = urlparse(url)
            # Only crawl URLs from the same domain
            if parsed.netloc != self.domain:
                return False
            # Skip certain file types
            skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.exe']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            return True
        except:
            return False
    
    def extract_text_from_page(self, html: str) -> str:
        """Extract readable text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def crawl(self) -> List[Tuple[str, str]]:
        """
        Crawl the website and return list of (url, content) tuples
        
        Returns:
            List of tuples containing (url, extracted_text)
        """
        to_visit = [self.start_url]
        pages_data = []
        
        print(f"Starting crawl of {self.domain}...")
        print(f"Max pages to crawl: {self.max_pages}\n")
        
        while to_visit and len(self.visited_urls) < self.max_pages:
            url = to_visit.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Skip if not valid
            if not self.is_valid_url(url):
                continue
            
            self.visited_urls.add(url)
            
            try:
                print(f"Crawling ({len(self.visited_urls)}/{self.max_pages}): {url}")
                
                # Fetch the page
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                # Extract text
                text = self.extract_text_from_page(response.text)
                
                if text and len(text) > 50:  # Only save if there's meaningful content
                    pages_data.append((url, text))
                    print(f"  OK Extracted {len(text)} characters")
                    
                    # Find new URLs to visit
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        new_url = urljoin(url, link['href'])
                        # Remove URL fragments
                        new_url = new_url.split('#')[0]
                        
                        if new_url not in self.visited_urls and new_url not in to_visit:
                            if self.is_valid_url(new_url):
                                to_visit.append(new_url)
                else:
                    print(f"  - Skipped (insufficient content)")
                
                # Be respectful - add delay between requests
                time.sleep(1)
                
            except requests.RequestException as e:
                print(f"  FAIL Error: {e}")
                self.failed_urls.add(url)
            except Exception as e:
                print(f"  FAIL Unexpected error: {e}")
                self.failed_urls.add(url)
        
        print(f"\nOK Crawl complete!")
        print(f"  Pages crawled: {len(pages_data)}")
        print(f"  Pages failed: {len(self.failed_urls)}")
        
        return pages_data


def crawl_sharda_website(max_pages: int = 100) -> List[Tuple[str, str]]:
    """
    Convenience function to crawl Sharda University website
    
    Args:
        max_pages: Maximum number of pages to crawl
    
    Returns:
        List of tuples containing (url, extracted_text)
    """
    crawler = ShardaWebCrawler(max_pages=max_pages)
    return crawler.crawl()


if __name__ == "__main__":
    # Example usage
    pages = crawl_sharda_website(max_pages=20)
    print(f"\nTotal pages extracted: {len(pages)}")
    for url, text in pages[:3]:
        print(f"\n--- {url} ---")
        print(text[:500])  # Print first 500 chars

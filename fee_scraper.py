"""
Course Fee Scraper for Sharda University
Uses crawl4ai to handle dynamic content and JS-rendered tabs (Semester/Yearly fees)
"""

import asyncio
import re
from typing import List, Dict, Tuple
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class CourseFeeScraper:
    def __init__(self):
        self.base_url = "https://www.sharda.ac.in/course-fee"

    async def scrape_async(self) -> Tuple[List[str], List[Dict]]:
        """
        Scrape course fee page using crawl4ai with JS execution to handle tabs
        """
        print(f"Starting dynamic scrape of: {self.base_url}")
        
        browser_config = BrowserConfig(headless=True)
        
        # JS to click tabs and extract content for each
        # We'll extract the main content and any specific fee tables
        js_code = """
        (async () => {
            const results = {};
            const tabs = Array.from(document.querySelectorAll('.nav-tabs a, [data-toggle="tab"]'));
            
            // Initial state (usually Yearly Fee)
            results['Default'] = document.body.innerText;
            
            for (const tab of tabs) {
                const tabText = tab.innerText.trim();
                if (tabText.toLowerCase().includes('fee')) {
                    tab.click();
                    await new Promise(r => setTimeout(r, 800)); // Wait for transition
                    results[tabText] = document.body.innerText;
                }
            }
            return results;
        })();
        """

        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=js_code
        )

        documents = []
        metadatas = []

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=self.base_url, config=run_config)
                
                if result.success and result.js_execution_result:
                    tab_contents = result.js_execution_result
                    for tab_name, content in tab_contents.items():
                        # Clean up content using simple regex or split
                        # Focus on lines containing 'Fee', 'Course', or numbers
                        relevant_lines = [
                            line.strip() for line in content.split('\n') 
                            if any(k in line.lower() for k in ['fee', 'course', 'rs.', 'total', 'semester', 'yearly'])
                            and len(line.strip()) > 5
                        ]
                        
                        cleaned_content = "\n".join(relevant_lines)
                        if len(cleaned_content) > 100:
                            # Split into chunks of ~2000 chars if too large
                            chunk_size = 2000
                            for i in range(0, len(cleaned_content), chunk_size):
                                chunk = cleaned_content[i:i+chunk_size]
                                documents.append(f"Source: {self.base_url} (Tab: {tab_name})\n{chunk}")
                                metadatas.append({
                                    "source": self.base_url,
                                    "type": "fee_data",
                                    "tab": tab_name
                                })
                    print(f"  OK Extracted {len(documents)} documents from fee tabs")
                else:
                    print(f"  FAIL: JS execution failed or no results. Error: {result.error_message}")
        except Exception as e:
            print(f"  FAIL: Unexpected error during fee scraping: {e}")

        return documents, metadatas

def scrape_course_fees() -> Tuple[List[str], List[Dict]]:
    """Synchronous wrapper for async scraper"""
    scraper = CourseFeeScraper()
    return asyncio.run(scraper.scrape_async())

if __name__ == "__main__":
    docs, metas = scrape_course_fees()
    print(f"Total documents: {len(docs)}")
    if docs:
        print(f"Example doc: {docs[0][:500]}")

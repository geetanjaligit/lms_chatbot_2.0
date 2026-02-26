import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

class CourseFeeScraper:
    def __init__(self):
        self.base_url = "https://www.sharda.ac.in/course-fee"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_course_fees(self) -> Tuple[List[str], List[Dict]]:
        """
        Scrape course fee page using BeautifulSoup
        """
        print(f"Starting scrape of: {self.base_url}")
        documents = []
        metadatas = []

        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all program blocks
            # Based on common Sharda University selectors
            cards = soup.select('.course-fee-box, .n-programe-fees, .course-details')
            
            if not cards:
                # Try a broader selector if specific ones fail
                cards = soup.select('.col-md-4, .col-sm-6')

            for card in cards:
                title_elem = card.select_one('h2, h3, h4, .course-title')
                if title_elem:
                    program_name = title_elem.get_text(strip=True)
                    # Extract text content from the card
                    content = card.get_text(separator="\n", strip=True)
                    
                    if len(content) > 50 and any(k in content.lower() for k in ['fee', 'rs.', 'total']):
                        documents.append(f"Source: {self.base_url}\nProgram: {program_name}\n{content}")
                        metadatas.append({
                            "source": self.base_url,
                            "type": "fee_data",
                            "program": program_name
                        })
            
            print(f"  OK Extracted {len(documents)} records via BeautifulSoup")
            
            # Simple fallback: if no cards found, take all text from main content area
            if not documents:
                main_content = soup.find('main') or soup.body
                if main_content:
                    text = main_content.get_text(separator="\n", strip=True)
                    if "Fee" in text:
                        documents.append(f"Source: {self.base_url}\n{text[:8000]}")
                        metadatas.append({"source": self.base_url, "type": "fee_data", "method": "page_text"})
        
        except Exception as e:
            print(f"  FAIL: Error during scraping: {e}")

        return documents, metadatas

def scrape_course_fees() -> Tuple[List[str], List[Dict]]:
    """Standalone function to be called by ingest_data.py"""
    scraper = CourseFeeScraper()
    return scraper.scrape_course_fees()

if __name__ == "__main__":
    docs, metas = scrape_course_fees()
    print(f"Total documents: {len(docs)}")
    if docs:
        print(f"Example doc: {docs[0][:500]}")


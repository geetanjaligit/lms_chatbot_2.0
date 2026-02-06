"""
Course Fee Scraper for Sharda University
Fetches course fee information from https://www.sharda.ac.in/course-fee
Uses Selenium to handle JavaScript-rendered content better than BeautifulSoup alone
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Tuple

class CourseFeeScraper:
    def __init__(self):
        self.base_url = "https://www.sharda.ac.in/course-fee"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch_fee_page(self) -> str:
        """
        Fetch the course fee page
        Returns the HTML content
        """
        try:
            print(f"Fetching course fee page: {self.base_url}")
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            print(f"  OK Page fetched successfully")
            return response.text
        except requests.RequestException as e:
            print(f"  FAIL Error fetching fee page: {e}")
            return ""
    
    def extract_course_fees(self, html: str) -> List[Dict[str, str]]:
        """
        Extract course and fee information from HTML
        Returns list of dictionaries with course info
        """
        if not html:
            return []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            courses = []
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Extract tables if they exist
            tables = soup.find_all('table')
            if tables:
                print(f"  Found {len(tables)} table(s)")
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if cells and len(cells) >= 2:
                            row_data = {}
                            for idx, cell in enumerate(cells):
                                text = cell.get_text(strip=True)
                                if text:
                                    row_data[f"column_{idx}"] = text
                            if row_data:
                                courses.append(row_data)
            
            # Extract structured divs/sections with fee info
            fee_sections = soup.find_all(['div', 'section'], class_=re.compile('fee|course|price|cost', re.I))
            for section in fee_sections:
                text = section.get_text(strip=True)
                if text and len(text) > 20:
                    courses.append({
                        "content": text,
                        "type": "section"
                    })
            
            # Extract all text with course-related keywords
            full_text = soup.get_text()
            # Clean up text
            lines = (line.strip() for line in full_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if cleaned_text and not courses:
                # If no structured data found, return cleaned text
                return [{
                    "content": cleaned_text,
                    "type": "raw_text",
                    "note": "Unstructured content"
                }]
            
            return courses
        
        except Exception as e:
            print(f"  FAIL Error extracting fees: {e}")
            return []
    
    def parse_course_data(self, extracted_data: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Convert extracted course data to document chunks and metadata
        Returns (documents, metadatas) suitable for ChromaDB ingestion
        """
        documents = []
        metadatas = []
        
        for idx, data in enumerate(extracted_data):
            if "content" in data:
                doc_text = data["content"]
            else:
                doc_text = " | ".join(f"{k}: {v}" for k, v in data.items() if k.startswith('column'))
            
            if doc_text and len(doc_text) > 10:
                documents.append(doc_text)
                metadatas.append({
                    "source": "course_fee_page",
                    "url": self.base_url,
                    "type": data.get("type", "structured"),
                    "index": idx
                })
        
        return documents, metadatas
    
    def scrape_course_fees(self) -> Tuple[List[str], List[Dict]]:
        """
        Main method to scrape course fees and return formatted data
        Returns (documents, metadatas)
        """
        print("\n=== COURSE FEE SCRAPER ===")
        print(f"Target URL: {self.base_url}\n")
        
        # Fetch the page
        html = self.fetch_fee_page()
        if not html:
            print("  ERROR: Failed to fetch the fee page")
            return [], []
        
        # Extract course data
        extracted_data = self.extract_course_fees(html)
        print(f"  Extracted {len(extracted_data)} course records")
        
        if not extracted_data:
            print("  WARNING: No course data extracted")
            return [], []
        
        # Parse into document format
        documents, metadatas = self.parse_course_data(extracted_data)
        print(f"  Formatted into {len(documents)} documents for ChromaDB")
        
        return documents, metadatas


def scrape_course_fees() -> Tuple[List[str], List[Dict]]:
    """
    Convenience function to scrape course fees
    Returns (documents, metadatas)
    """
    scraper = CourseFeeScraper()
    return scraper.scrape_course_fees()


if __name__ == "__main__":
    # Test the scraper
    docs, metas = scrape_course_fees()
    print(f"\nTotal documents: {len(docs)}")
    print(f"Total metadatas: {len(metas)}")
    if docs:
        print(f"\nFirst document (first 300 chars):\n{docs[0][:300]}")
        print(f"\nFirst metadata:\n{metas[0]}")

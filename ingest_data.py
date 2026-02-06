#!/usr/bin/env python
"""
Robust Data Ingestion Script
Integrates: Excel Logic + Web Crawler + Fee Scraper
"""

import os
import chromadb
import requests
from dotenv import load_dotenv
from pypdf import PdfReader
import pandas as pd
import time
import shutil

# Import your existing helper modules
from web_crawler import crawl_sharda_website
from fee_scraper import scrape_course_fees

load_dotenv()

JINA_API_KEY = os.getenv('JINA_API_KEY')
DB_PATH = "chroma_db"
COLLECTION_NAME = "lms_docs_enhanced"

if not JINA_API_KEY:
    print("⚠️  WARNING: JINA_API_KEY not found. Embeddings will fail.")

def JinaEmbeddingFunction(input_texts: list[str]) -> list[list[float]]:
    """Robust Embedding function with batching and error handling"""
    embeddings = []
    batch_size = 20
    for i in range(0, len(input_texts), batch_size):
        batch = input_texts[i:i+batch_size]
        try:
            response = requests.post(
                "https://api.jina.ai/v1/embeddings",
                headers={"Authorization": f"Bearer {JINA_API_KEY}"},
                json={"model": "jina-embeddings-v2-base-en", "input": batch},
                timeout=30
            )
            if response.status_code == 200:
                # Fix: Use data[j] instead of data[i]
                data = response.json()['data']
                embeddings.extend(data[j]['embedding'] for j in range(len(batch)))
            else:
                print(f"   ⚠️ Jina API Error: {response.status_code}")
                embeddings.extend([[0.0] * 768] * len(batch))
        except Exception as e:
            print(f"   ⚠️ Connection Error: {e}")
            embeddings.extend([[0.0] * 768] * len(batch))
        time.sleep(1.0)
    return embeddings

def process_excel_file(filepath: str, filename: str):
    """Reads ALL sheets and converts rows to context strings"""
    documents, metadatas, ids = [], [], []
    try:
        xls = pd.read_excel(filepath, sheet_name=None)
        for sheet_name, df in xls.items():
            df = df.fillna("")
            for index, row in df.iterrows():
                # Convert row to string
                row_parts = [f"{col}: {str(row[col]).strip()}" for col in df.columns if str(row[col]).strip()]
                if row_parts:
                    content = f"Source: {filename} (Sheet: {sheet_name})\nData: " + ", ".join(row_parts)
                    documents.append(content)
                    metadatas.append({"source": filename, "sheet": sheet_name, "type": "excel_row"})
                    ids.append(f"{filename}_{sheet_name}_{index}")
    except Exception as e:
        print(f"   ❌ Error processing {filename}: {e}")
    return documents, metadatas, ids

def main():
    print("🚀 STARTING ROBUST INGESTION...")
    
    # 1. Reset Database
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.create_collection(name=COLLECTION_NAME)

    all_docs, all_metas, all_ids = [], [], []

    # 2. Process Local Excel/PDF Files
    data_dir = "data"
    if os.path.exists(data_dir):
        print(f"\n📂 Processing files in '{data_dir}'...")
        for f in os.listdir(data_dir):
            fp = os.path.join(data_dir, f)
            if f.endswith(('.xlsx', '.xls')):
                d, m, i = process_excel_file(fp, f)
                all_docs.extend(d)
                all_metas.extend(m)
                all_ids.extend(i)
                print(f"   ✅ Loaded {len(d)} rows from {f}")
    
    # 3. Process Web Crawler (Using your web_crawler.py)
    # print("\n🕷️  Running Web Crawler (Lite Mode)...")
    # try:
    #     # Crawling fewer pages (15) to keep it fast for testing
    #     web_pages = crawl_sharda_website(max_pages=111)
    #     for i, (url, content) in enumerate(web_pages):
    #         all_docs.append(f"Source: {url}\nContent: {content[:4000]}") # Limit text length
    #         all_metas.append({"source": url, "type": "web_page"})
    #         all_ids.append(f"web_{i}")
    #     print(f"   ✅ Crawled {len(web_pages)} pages")
    # except Exception as e:
    #     print(f"   ⚠️ Crawler failed: {e}")

    # 4. Process Fees (Using your fee_scraper.py)
    # print("\n💰 Running Fee Scraper...")
    # try:
    #     fee_docs, fee_metas = scrape_course_fees()
    #     # Parse fee scraper output to match our lists
    #     for i, doc in enumerate(fee_docs):
    #         all_docs.append(doc)
    #         all_metas.append(fee_metas[i])
    #         all_ids.append(f"fee_{i}")
    #     print(f"   ✅ Scraped {len(fee_docs)} fee records")
    # except Exception as e:
    #     print(f"   ⚠️ Fee Scraper failed: {e}")

    # 5. Embed and Store
    print(f"\n💾 Saving {len(all_docs)} total chunks to database...")
    if all_docs:
        batch_size = 50
        for i in range(0, len(all_docs), batch_size):
            end = min(i+batch_size, len(all_docs))
            embeddings = JinaEmbeddingFunction(all_docs[i:end])
            collection.add(
                documents=all_docs[i:end],
                embeddings=embeddings,
                metadatas=all_metas[i:end],
                ids=all_ids[i:end]
            )
            print(f"   ...Indexed batch {i} to {end}")
    else:
        print("   ⚠️ No data found to index!")

    print("\n✨ INGESTION COMPLETE. Run 'python app_rag.py' to start chatbot.")

if __name__ == "__main__":
    main()
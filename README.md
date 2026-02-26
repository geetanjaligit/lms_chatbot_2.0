# LMS Chatbot (RAG-System)

This project is a **Retrieval-Augmented Generation (RAG) based LMS chatbot** built with Python. Follow the steps below carefully to set up and run the system locally.

---

## Prerequisites

### 1. Python Version (Very Important)

* You **MUST** use **Python 3.11.x** (Mine is Python 3.11.9)
* ❌ Do **NOT** use Python 3.14 (it breaks AI libraries)

Check your Python version:

```powershell
python --version
```

If Python 3.11 is not installed, install it either from thre official website or on terminal.

---

### 2. API Keys

Create a file named `.env` in the **root folder** of the project and add the following:

```env
GEMINI_API_KEY=your_google_gemini_key
JINA_API_KEY=your_jina_ai_key
```

Make sure there are **no extra spaces** around `=`.

---

## Setup Instructions

### 1. Clean Start (Recommended)

To avoid version conflicts:

* Delete any existing `venv` or `venv-lms` folders in the project directory.

---

### 2. Create Virtual Environment (Python 3.11)

Open a terminal in the project folder and run:

```powershell
# Force creation with Python 3.11
py -3.11 -m venv venv-lms
```

---

### 3. Activate Virtual Environment

```powershell
.\venv-lms\Scripts\activate
```

You should now see `(venv-lms)` in your terminal.

---

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## How to Run

### Step 1: Build the Vector Database

Run this **once**, or whenever Excel files or web content change:

```powershell
python ingest_data.py
```

Wait until all Excel files are processed and web crawling is complete.

---

### Step 2: Start the Backend Server

```powershell
python app_rag.py
```

---

### Step 3: Start the Frontend

* Open `index.html` directly in your browser
* **OR** use the **Live Server** extension in VS Code

---

---

## Deployment (Render)

To deploy this project to Render:

1. **Connect your GitHub repository** to a new Render Web Service.
2. **Environment Variables**: Add these three in the Render dashboard:
   - `GEMINI_API_KEY`
   - `JINA_API_KEY`
   - `PYTHON_VERSION` = `3.11.9` (This is **CRITICAL** to prevent version conflicts)
3. **Build Command**: 
   ```bash
   pip install -r requirements.txt && python ingest_data.py
   ```
4. **Start Command**:
   ```bash
   python app_rag.py
   ```


---


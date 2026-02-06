import os
import chromadb
import requests
import sqlite3
import jwt
import datetime
import functools
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from google.genai import Client
from duckduckgo_search import DDGS # Requires: pip install duckduckgo-search
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
JINA_API_KEY = os.getenv('JINA_API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_change_me_in_prod') # Add to .env in real app
genai_client = Client(api_key=GEMINI_API_KEY)

# Database Setup
client = chromadb.PersistentClient(path="chroma_db")
try:
    collection = client.get_collection(name="lms_docs_enhanced")
except:
    print("Database not found. Run ingest_data.py first.")

# --- User Database Setup (SQLite) ---
def init_user_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

init_user_db()

# --- Auth Decorator ---
def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)
    return decorated

# --- Auth Endpoints ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
        
    hashed_password = generate_password_hash(password, method='scrypt')
    
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 409
    except Exception as e:
         return jsonify({'message': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    username = auth.get('username')
    password = auth.get('password')

    if not username or not password:
         return jsonify({'message': 'Could not verify', 'token': None}), 401

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone() # user is tuple: (id, username, password)
    conn.close()

    if user and check_password_hash(user[2], password):
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({'token': token})

    return jsonify({'message': 'Could not verify', 'token': None}), 401


def get_jina_embeddings(text):
    """Single text embedding"""
    try:
        response = requests.post(
            "https://api.jina.ai/v1/embeddings",
            headers={"Authorization": f"Bearer {JINA_API_KEY}"},
            json={"model": "jina-embeddings-v2-base-en", "input": [text]},
            timeout=10
        )
        return response.json()['data'][0]['embedding']
    except:
        return [0.0] * 768

def search_internet(query):
    """Fallback: Searches the web if local data is insufficient"""
    print("🌎 Searching Internet for:", query)
    try:
        with DDGS() as ddgs:
            # Search specifically for Sharda University related context if not present
            search_query = query if "Sharda" in query else f"Sharda University {query}"
            results = list(ddgs.text(search_query, max_results=3))
            
            summary = "\n".join([f"Web Source ({r['title']}): {r['body']} - Link: {r['href']}" for r in results])
            return summary
    except Exception as e:
        print(f"Web search failed: {e}")
        return ""

@app.route('/chat', methods=['POST'])
@token_required
def chat():
    data = request.json
    user_query = data.get('query')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    print(f"\nUser Query: {user_query}")

    # 1. Search Local Vector DB
    query_vec = get_jina_embeddings(user_query)
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=5
    )
    
    # 2. Analyze Local Results
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]
    
    local_context = ""
    # Only use results if they are relevant (distance threshold)
    # Lower distance = better match. Threshold e.g., < 1.0 (depends on embedding model)
    relevant_docs = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        # Format the context to show the source CLEARLY
        source_label = f"[{meta.get('source', 'Unknown File')} - Sheet: {meta.get('sheet', 'N/A')}]"
        local_context += f"{source_label}\n{doc}\n\n"
        relevant_docs.append(source_label)

    # 3. Decision Logic: Need Web Search?
    web_context = ""
    # Extract role from request
    user_role = data.get('role', 'student')
    
    if len(local_context) < 50 or "news" in user_query.lower() or "latest" in user_query.lower():
         web_context = search_internet(user_query)

    # 4. Construct System Prompt
    role_instruction = ""
    if user_role == 'faculty':
        role_instruction = """
        You are interacting with a Faculty Member. 
        - Provide detailed, academic, and administrative information.
        - You may include internal codes or specific policy details relevant to faculty.
        - Maintain a highly professional and collegial tone.
        """
    else:
        role_instruction = """
        You are interacting with a Student.
        - Provide clear, supportive, and guidance-focused information.
        - Avoid overly complex administrative jargon unless necessary.
        - Maintain a helpful and encouraging tone.
        """

    system_prompt = f"""
    You are an advanced AI assistant for Sharda University.
    
    {role_instruction}

    Query: {user_query}

    STRICT INSTRUCTIONS:
    1. Use the "Local Internal Data" first. This contains Excel files with student/mentor lists.
    2. If the user asks for a specific student, mentor, or ID found in the Local Data, quote the details exactly.
    3. If the Local Data is empty or irrelevant, use the "Web Search Results".
    4. If the data comes from an Excel file, mention which file/sheet it came from.
    5. Be concise and professional.

    --- LOCAL INTERNAL DATA (Excel/PDFs) ---
    {local_context}

    --- WEB SEARCH RESULTS (Live Internet) ---
    {web_context}
    """

    # 5. Generate Answer
    response = genai_client.models.generate_content(
    model="gemini-2.5-flash",
    contents=system_prompt
    )

    final_answer = response.text
    
    # Clean up formatting for frontend
    return jsonify({
        "answer": final_answer,
        "sources_retrieved": len(relevant_docs),
        "data_sources": list(set(relevant_docs)) # Unique sources
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

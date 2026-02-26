import os
import chromadb
import requests
import sqlite3
import jwt
import datetime
import functools
from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from google.genai import Client
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# Set static folder to 'frontend'
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
JINA_API_KEY = os.getenv('JINA_API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_change_me_in_prod')
genai_client = Client(api_key=GEMINI_API_KEY)

# Database Setup
client = chromadb.PersistentClient(path="chroma_db")
try:
    collection = client.get_collection(name="lms_docs_enhanced")
except:
    print("Database not found. Run ingest_data.py first.")

def init_user_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

init_user_db()

# --- Static File Serving ---
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/chat_page')
def chat_page():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

# --- Authentication Logic ---
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
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({'message': 'Could not verify', 'token': None}), 401

def get_jina_embeddings(text):
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
    results = collection.query(query_embeddings=[query_vec], n_results=15)
    
    # 2. Analyze Local Results
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]
    
    local_context = ""
    relevant_docs = []
    RELEVANCE_THRESHOLD = 0.6 
    
    for doc, meta, dist in zip(documents, metadatas, distances):
        if dist < RELEVANCE_THRESHOLD:
            source_label = f"[{meta.get('source', 'Unknown File')}]"
            local_context += f"{source_label}\n{doc}\n\n"
            relevant_docs.append(source_label)

    # 3. Construct System Prompt
    system_prompt = f"""
    You are an AI assistant for Sharda University.
    
    You have access to the "University Knowledge Base" which includes:
    - Lists of students, mentors, and sections from internal Excel files.
    - Official website content crawled from 150 pages of sharda.ac.in.

    ### KNOWLEDGE BASE:
    {local_context}

    ### INSTRUCTIONS:
    1. If the information is in the Knowledge Base, answer directly and professionally.
    2. If the user asks for students or faculty, look for them in the provided Knowledge Base.
    3. If specific information (like an establishment date or latest news) is NOT found in the Knowledge Base, do NOT make it up.
    4. Instead of searching the live web, politely inform the user that the information isn't in your current records and suggest they check the "About Us" section or the official university brochure on sharda.ac.in.
    5. Be concise and helpful.

    Query: {user_query}
    """
    
    # 4. Generate Answer
    response = genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=system_prompt
    )
    
    return jsonify({
        "answer": response.text,
        "sources_retrieved": len(relevant_docs),
        "data_sources": list(set(relevant_docs))
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

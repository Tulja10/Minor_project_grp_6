# app.py  
import os
import mysql.connector
import bcrypt
import requests
import json 
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import render_template
from pathlib import Path 

FAQS_FILE_PATH = Path("./faqs.json") 


# ---------------
# Configuration 
# ---------------
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '@Morpankh123'),
    'database': os.getenv('MYSQL_DB', 'user_db')
}
CHROMA_PERSIST_PATH = os.getenv('CHROMA_PATH', './chroma_store')
CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION', 'student_faqs')

# ------------------------
# App init
# ------------------------
app = Flask(__name__)
CORS(app)

# ------------------------
# Database connection (safe)
# ------------------------
try:
    userDB = mysql.connector.connect(**MYSQL_CONFIG)
except mysql.connector.Error as e:
    print("ERROR: Could not connect to MySQL. Check MYSQL_CONFIG and whether MySQL is running.")
    print("mysql.connector error:", e)
    userDB = None  # endpoints will return helpful errors if DB missing

# Try to initialize ChromaDB (vector DB) if available
try:
    from chromadb import PersistentClient
    CHROMADB_AVAILABLE = True
except Exception:
    PersistentClient = None
    CHROMADB_AVAILABLE = False

collection = None
if CHROMADB_AVAILABLE:
    try:
        client = PersistentClient(path=CHROMA_PERSIST_PATH)
        # prefer get_or_create_collection (defensive)
        try:
            collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        except Exception:
            # some versions expose get_collection
            collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
    except Exception as e:
        print("Chromadb init failed:", e)
        collection = None

# ------------------------
# Helper: LLM integration placeholder
# Returns: (answer_text, context_str)
# ------------------------
def call_your_llm(prompt: str):
    api_url = os.getenv('LLM_API_URL', "http://127.0.0.1:5001/api/v1/generate")
    payload = {
    "prompt": prompt,
    "max_length": 64,
    "max_new_tokens": 64,
    "temperature": 0.6,
    "top_k": 50,
    "top_p": 0.9,
    "stream": True,
    "stop": ["Question:", "User:", "Context:"]
}

    try:
        response = requests.post(api_url, json=payload, timeout=45)
        if response.status_code == 200:
            data = response.json()
            # adapt to the response format of your chosen local LLM
            # trying multiple defensive extraction paths
            text = ""
            if isinstance(data, dict):
                if "results" in data and isinstance(data["results"], list):
                    text = data["results"][0].get("text", "")
                elif "text" in data:
                    text = data.get("text", "")
                else:
                    # fallback stringify entire body
                    text = str(data)
            else:
                text = str(data)
            # For now we don't have a separate context field from the LLM — return empty context
            return text, ""
        else:
            return f"LLM error: status {response.status_code}", ""
    except Exception as e:
        return f"LLM call exception: {str(e)}", ""

def is_admin(email: str) -> bool:
    cursor = userDB.cursor(dictionary=True)
    try:
        cursor.execute("SELECT role FROM User WHERE email=%s", (email,))
        row = cursor.fetchone()
        return row and row["role"] == "admin"
    finally:
        cursor.close()


# ------------------------
# User / Auth endpoints
# ------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def register():
    if userDB is None:
        return jsonify({"message": "Server DB not configured"}), 500

    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password_raw = data.get('password', '')

    if not (name and email and password_raw):
        return jsonify({'message': 'name, email and password required'}), 400

    password = password_raw.encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

    cursor = userDB.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM User WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            return jsonify({'message': 'User already exists!'}), 400
        cursor.execute("INSERT INTO User (name, email, hashed_psswd, role) VALUES (%s, %s, %s, %s)",
        (name, email, hashed, "student")
        )

        userDB.commit()
        # return created user's id (optional readback)
        return jsonify({'message': 'User registered successfully.'}), 201
    finally:
        cursor.close()

@app.route('/login', methods=['POST'])
def login():
    if userDB is None:
        return jsonify({"message": "Server DB not configured"}), 500

    data = request.get_json() or {}
    email = data.get("email")
    password_raw = data.get("password", "")

    if not email or not password_raw:
        return jsonify({'message': 'email and password required'}), 400

    cursor = userDB.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_id, name, email, hashed_psswd, role FROM User WHERE email=%s",
            (email,)
        )
        user = cursor.fetchone()
    finally:
        cursor.close()

    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401

    # IMPORTANT — check against hashed_psswd
    if not bcrypt.checkpw(password_raw.encode('utf-8'), user['hashed_psswd'].encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401

    return jsonify({
        "message": "Login successful",
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "student")
    }), 200

@app.route("/admin/upload_faqs", methods=["POST"])
def admin_upload_faqs():
    if collection is None:
        return jsonify({"error": "VectorDB not configured on server"}), 500

    data = request.get_json() or {}
    admin_email = data.get("admin_email")
    new_faqs = data.get("faqs")

    if not admin_email:
        return jsonify({"error": "admin_email required"}), 400
    if not is_admin(admin_email):
        return jsonify({"error": "Only admin users can upload FAQs"}), 403
    if not new_faqs or not isinstance(new_faqs, list):
        return jsonify({"error": "faqs must be a non-empty list"}), 400

    # -----------------------------
    # 1️⃣ Load existing FAQs
    # -----------------------------
    existing = []
    if FAQS_FILE_PATH.exists():
        try:
            existing = json.loads(FAQS_FILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    # convert to dict for fast lookup
    existing_by_id = {f["id"]: f for f in existing}
    existing_questions = {f["question"].strip().lower(): f["id"] for f in existing}

    # -----------------------------
    # 2️⃣ Merge new FAQs (append only if not duplicate)
    # -----------------------------
    added_count = 0
    for faq in new_faqs:
        fid = str(faq.get("id")).strip()
        q = (faq.get("question") or "").strip()
        a = (faq.get("answer") or "").strip()

        if not fid or not q or not a:
            return jsonify({"error": "Each FAQ must have id, question, answer"}), 400

        # Skip duplicate IDs
        if fid in existing_by_id:
            continue

        # Skip duplicate questions
        if q.lower() in existing_questions:
            continue

        existing_by_id[fid] = {"id": fid, "question": q, "answer": a}
        added_count += 1

    # Final merged list
    final_faqs = list(existing_by_id.values())

    # -----------------------------
    # 3️⃣ Write merged FAQs back to file
    # -----------------------------
    try:
        FAQS_FILE_PATH.write_text(json.dumps(final_faqs, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"Failed writing faqs.json: {e}"}), 500

    # -----------------------------
    # 4️⃣ Rebuild the VectorDB Index
    # -----------------------------
    try:
        try:
            collection.delete(where={})
        except Exception:
            pass

        docs = [f["question"] for f in final_faqs]
        metas = [{"answer": f["answer"]} for f in final_faqs]
        ids = [f["id"] for f in final_faqs]

        collection.add(documents=docs, metadatas=metas, ids=ids)
    except Exception as e:
        return jsonify({"error": f"Failed rebuilding vector index: {e}"}), 500

    return jsonify({
        "message": "FAQs merged successfully.",
        "total_faqs": len(final_faqs),
        "new_faqs_added": added_count
    }), 200


@app.route("/admin/get_faqs", methods=["GET"])
def admin_get_faqs():
    if not FAQS_FILE_PATH.exists():
        return jsonify({"faqs": []})

    try:
        data = json.loads(FAQS_FILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = []

    return jsonify({"faqs": data})


@app.route('/logout', methods=['POST'])
def logout():
    # stateless backend; frontend should clear local user info
    return jsonify({"message": "Logout successful"}), 200

@app.route('/history', methods=['GET'])
def chat_history():
    if userDB is None:
        return jsonify({"message": "Server DB not configured"}), 500

    email = request.args.get('email')
    if not email:
        return jsonify({'message': 'email required'}), 400

    cursor = userDB.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM User WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        cursor.execute(
            "SELECT ques, ans, context, timestamp FROM chat_history WHERE user_id=%s ORDER BY timestamp DESC",
            (user['user_id'],)
        )
        chats = cursor.fetchall()
    finally:
        cursor.close()

    result = []
    for c in chats:
        ts = c['timestamp']
        ts = ts.strftime("%Y-%m-%d %H:%M:%S")
        result.append({
            "question": c["ques"],
            "answer": c["ans"],
            "context": c["context"],
            "timestamp": ts
        })

    return jsonify({"chats": result})


# ------------------------
# Domain helpers (personalized data)
# ------------------------
def get_user_attendance(email):
    if userDB is None:
        return "Server DB not configured."
    cursor = userDB.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM User WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            return "User not found."
        cursor.execute("SELECT sem, total_classes, attended_classes, percentage FROM attendance WHERE user_id=%s", (user['user_id'],))
        records = cursor.fetchall()
    finally:
        cursor.close()

    if records:
        return "\n".join([f"Semester {r['sem']}: {r['percentage']}% attendance" for r in records])
    return "No attendance records found."

def get_user_result(email):
    if userDB is None:
        return "Server DB not configured."
    cursor = userDB.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM User WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            return "User not found."
        cursor.execute("SELECT sem, sgpa, cgpa FROM results WHERE user_id=%s", (user['user_id'],))
        records = cursor.fetchall()
    finally:
        cursor.close()

    if records:
        return "\n".join([f"Semester {r['sem']}: SGPA {r['sgpa']}, CGPA {r['cgpa']}" for r in records])
    return "No result records found."

# ------------------------
# Chat endpoint (vector search + LLM fallback)
# Flow:
#  - if question appears personal (attendance/result) -> require email/login, fetch from DB -> LLM (optional)
#  - else -> vector search (Chroma) then LLM with context
# ------------------------
@app.route('/chat', methods=['POST'])
def chat():
    if userDB is None:
        return jsonify({"error": "Server DB not configured"}), 500

    data = request.get_json() or {}
    question = (data.get('question') or data.get('query') or '').strip()
    email = data.get('email')

    if not question:
        return jsonify({'error': 'question required'}), 400

    q_lower = question.lower()

    # ============= PERSONAL QUERIES =============
    if any(k in q_lower for k in ["attendance", "present", "absent"]):
        if not email:
            return jsonify({'error': 'This is a personalized query; please provide your email (login).'}), 401
        answer = get_user_attendance(email)
        context = "Queried attendance"

    elif any(k in q_lower for k in ["result", "grade", "marks", "sgpa", "cgpa"]):
        if not email:
            return jsonify({'error': 'This is a personalized query; please provide your email (login).'}), 401
        answer = get_user_result(email)
        context = "Queried result"

    else:
        # ============= GENERAL QUERY =============
        context_passage = ""

        if collection is not None:
            try:
                vector_results = collection.query(query_texts=[question], n_results=1)

                try:
                    raw_context = vector_results['metadatas'][0][0].get('answer', '')
                except Exception:
                    raw_context = ""
            except Exception:
                raw_context = ""

        else:
            raw_context = ""

        # 1️⃣ CLEAN CONTEXT (remove Q/A patterns)
        import re

        def clean_context(text):
            if not text:
                return ""
            text = re.sub(r"Question:.*?Answer:", "", text, flags=re.DOTALL)
            text = text.replace("Q:", "").replace("A:", "")
            return text.strip()

        context_passage = clean_context(raw_context)

        # 2️⃣ FORMAT PROMPT (strict)
        llm_input = (
        "You are a helpful assistant. "
        "Always answer in clear ENGLISH only, even if the question is asked in Hindi or any other language. "
        "Translate internally if required but never show translation. "
        "Answer ONLY the final user question in 2–3 sentences. "
        "Do NOT repeat the question. "
        "Do NOT ask new questions. "
        "Do NOT include multiple answers. "
        "Do NOT output Q/A format. "
        "Do NOT explain what words mean. "
        "Do NOT add notes like '(konsa means bus)'. "
        "Do NOT include parentheses unless absolutely necessary. "
        "Keep the answer short, direct, and factual.\n\n"
        f"Context (summarized): {context_passage}\n\n"
        f"User question: {question}\n\n"
        "Final answer in English only:"
        )


        # 3️⃣ CALL LLM
        answer, context = call_your_llm(llm_input)

        # 4️⃣ CLEAN ANY REMAINING JUNK GENERATED
        for stop in ["Context:", "User question:", "Question:", "Answer:"]:
            if stop in answer:
                answer = answer.split(stop)[0].strip()

    # ============= SAVE TO HISTORY =============
    user_id = None
    if email:
        cursor = userDB.cursor(dictionary=True)
        try:
            cursor.execute("SELECT user_id FROM User WHERE email=%s", (email,))
            user = cursor.fetchone()
            user_id = user['user_id'] if user else None
        finally:
            cursor.close()

    try:
        cursor = userDB.cursor()
        try:
            if user_id is not None:
                cursor.execute("INSERT INTO chat_history (user_id, ques, ans, context) VALUES (%s, %s, %s, %s)",
                (user_id, question, answer, context)
                )

            userDB.commit()
        finally:
            cursor.close()
    except Exception as e:
        print("Warning: failed to store chat history:", e)

    return jsonify({
        'question': question,
        'answer': answer,
        'context': context
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


from flask import Flask, request, jsonify
from flask_cors import CORS
from chromadb import PersistentClient

# ✅ Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# ✅ Connect to persistent ChromaDB
client = PersistentClient(path="./chroma_store")
collection = client.get_collection(name="student_faqs")

# ✅ Define FAQ endpoint
@app.route("/faq", methods=["POST"])
def faq():
    data = request.get_json()
    query = data.get("question", "")
    results = collection.query(query_texts=[query], n_results=1)

    try:
        answer = results["metadatas"][0][0]["answer"]
    except (IndexError, KeyError, TypeError):
        answer = "No matching FAQ found."

    return jsonify({"answer": answer})

# ✅ Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

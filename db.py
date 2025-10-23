import json
from pathlib import Path
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# ✅ Initialize persistent ChromaDB client
client = PersistentClient(path="./chroma_store")

# ✅ Use local sentence transformer model (no API key required)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ✅ Create or get collection
collection = client.get_or_create_collection(
    name="student_faqs",
    embedding_function=embed_fn
)

# ✅ Load FAQ data
script_dir = Path(__file__).parent
faqs_path = script_dir / "faqs.json"

try:
    with open(faqs_path, "r", encoding='utf-8') as f:
        faqs = json.load(f)
except FileNotFoundError:
    print(f"❌ Error: faqs.json not found at {faqs_path}")
    exit(1)
except json.JSONDecodeError:
    print("❌ Error: faqs.json contains invalid JSON")
    exit(1)

# ✅ Embed and store FAQs
for faq in faqs:
    collection.add(
        documents=[faq["question"]],
        metadatas=[{"answer": faq["answer"]}],
        ids=[faq["id"]]
    )

print("✅ FAQ data embedded and stored in ChromaDB")

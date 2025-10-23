import json
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# ✅ Use the same model as in search.py
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)

# ✅ Connect to ChromaDB and delete old collection
client = PersistentClient(path="./chroma_store")
try:
    client.delete_collection(name="student_faqs")
except:
    pass  # Ignore if collection doesn't exist

# ✅ Recreate collection with correct embedding dimensions
collection = client.create_collection(name="student_faqs", embedding_function=embed_fn)

# ✅ Load and ingest FAQs
with open("faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

for faq in faqs:
    collection.add(
        documents=[faq["question"]],
        metadatas=[{"answer": faq["answer"]}],
        ids=[faq["id"]]
    )

print("✅ Collection re-ingested with 768-dim embeddings.")
def search_faq(query):
    query = query.lower().strip()
    results = collection.query(query_texts=[query], n_results=1)

    try:
        answer = results["metadatas"][0][0]["answer"]
        if answer:
            return answer
    except (IndexError, KeyError, TypeError):
        pass

    # Fallback keyword match
    for faq in faqs:
        if query in faq["question"].lower() or any(word in faq["question"].lower() for word in query.split()):
            return faq["answer"]

    return "No matching FAQ found."

if __name__ == "__main__":
    while True:
        user_query = input("🔍 Ask a question (or type 'exit' to quit): ")
        if user_query.lower() == "exit":
            break
        answer = search_faq(user_query)
        print(f"✅ Answer: {answer}\n")

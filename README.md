𝗠𝗶𝗻𝗼𝗿_𝗽𝗿𝗼𝗷𝗲𝗰𝘁_𝗴𝗿𝗽_𝟲
AI powered student assistance chatbot featuring 24/7 assistance to student queries.

## 🔧 Setup Instructions

1. Clone the repository:
git clone https://github.com/Tulja10/Minor_project_grp_6.git
cd Minor_project_grp_6

2. Create a virtual environment:
python -m venv venv
venv\Scripts\activate # Windows

3. Install dependencies:  pip install -r requirements.txt

4. Ingest FAQs: python db.py

5. Run the flask api : python app.py

6. Test in broswer :
   i. Open 'test.html'
   ii. Ask any question from FAQ


🧩𝗠𝗼𝗱𝘂𝗹𝗲 𝗕𝗿𝗲𝗮𝗸𝗱𝗼𝘄𝗻

 🔹𝗬𝘂𝘃anshi – 𝗕𝗮𝗰𝗸𝗲𝗻𝗱 𝗟𝗲𝗮𝗱 & 𝗦𝗲𝗺𝗮𝗻𝘁𝗶𝗰 𝗦𝗲𝗮𝗿𝗰𝗵 𝗦𝘁𝗿𝗮𝘁𝗲𝗴𝗶𝘀𝘁

- Built Flask API (`app.py`) with CORS support
- Designed semantic search logic (`search.py`) using `all-mpnet-base-v2`
- Embedded FAQs with ChromaDB (`db.py`)
- Added fallback logic for unmatched queries
- Created browser testing interface (`test.html`)
- Structured repo for team onboarding

> ✅ Status: Fully functional semantic search with fallback

---
   



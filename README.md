## Student FAQ Chatbot

A smart campus chatbot that answers queries using vector search (ChromaDB), MySQL (for user data), and LLM fallback (Mistral 7B).
Supports personalized answers, admin FAQ upload, and image-based responses (timetables).

## Features
Semantic FAQ search using ChromaDB <br>
Personalized data (attendance, results) via MySQL <br> 
LLM fallback for unknown queries <br>
Image responses (timetables) <br>
Admin panel to upload/update FAQs <br>
Feedback system 

## Setup Instructions
1. Clone the Repository
git clone <your-repo-link>
cd project

2. Create Virtual Environment
python -m venv venv
venv\Scripts\activate

3. Install Dependencies
pip install flask flask-cors mysql-connector-python bcrypt chromadb sentence-transformers requests

4. Setup MySQL Database
Open MySQL and create a database named:
user_db
Import the schema file:
userdb.sql
Make sure MySQL server is running before starting the project

6. Load FAQs into Vector Database
python db.py

Note:
This step creates embeddings and stores them in ChromaDB
Run this command every time you update faqs.json

6. Setup Local LLM (Mistral 7B)
Download and install LM Studio:
https://lmstudio.ai
Open LM Studio and download:
“Mistral 7B Instruct” model
Start the local API server on port 5001

Note:
The project uses this API by default:
http://127.0.0.1:5001/api/v1/generate
(You can change this in app.py if needed)

8. Run the Backend Server
python app.py

8. Open the Application
Open your browser and go to:
http://localhost:5000

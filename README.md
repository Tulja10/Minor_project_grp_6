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
1. Clone the Repository <br>
git clone https://github.com/Tulja10/Minor_project_grp_6.git <br>
cd project

2. Create Virtual Environment<br>
python -m venv venv<br>
venv\Scripts\activate

3. Install Dependencies<br>
pip install flask flask-cors mysql-connector-python bcrypt chromadb sentence-transformers requests

4. Setup MySQL Database<br>
Open MySQL and create a database named:<br>
user_db<br>
Import the schema file:<br>
userdb.sql<br>
Make sure MySQL server is running before starting the project

6. Load FAQs into Vector Database<br>
python db.py<br>

Note:<br>
This step creates embeddings and stores them in ChromaDB<br>
Run this command every time you update faqs.json

6. Setup Local LLM (Mistral 7B)<br>
Download and install LM Studio:<br>
https://lmstudio.ai<br>
Open LM Studio and download:<br>
“Mistral 7B Instruct” model<br>
Start the local API server on port 5001

Note:<br>
The project uses this API by default:<br>
http://127.0.0.1:5001/api/v1/generate<br>
(You can change this in app.py if needed)

8. Run the Backend Server<br>
python app.py

8. Open the Application<br>
Open your browser and go to:<br>
http://localhost:5000

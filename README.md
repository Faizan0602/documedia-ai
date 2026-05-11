DocuMedia AI – AI-Powered Document Intelligence System

DocuMedia AI is a full-stack AI-powered application that enables users to upload documents and media files (PDF, audio, video), generate summaries, and ask context-aware questions using a Retrieval-Augmented Generation (RAG) pipeline integrated with Gemini LLM APIs.

Features

Upload PDF, audio, and video files
AI-generated document summarization
Context-aware document Q&A
RAG-based retrieval for improved response relevance
Timestamp-based media interaction
Responsive React frontend
REST APIs built with FastAPI
Dockerized deployment support

Tech Stack

Frontend

React.js
JavaScript
Axios

Backend

FastAPI
Python
REST APIs

AI & Retrieval

Gemini API (LLM)
Retrieval-Augmented Generation (RAG)

Database

MongoDB

DevOps & Deployment

Frontend (React.js)
        ↓
 FastAPI Backend
        ↓
 Vector Retrieval (RAG)
        ↓
 Gemini LLM API
        ↓
 AI-generated Response

API Endpoints
Endpoint	          Method	    Description
/api/v1/upload	    POST	      Upload document/media
/api/v1/summary	    POST	      Generate AI summary
/api/v1/chat	      POST	      Ask questions from document
/api/v1/timestamps	POST	  Fetch media timestamps

Installation & Setup

Clone Repository
git clone <your-github-repo-url>
cd documedia-ai
Backend Setup
Create Virtual Environment
python -m venv venv
Activate Virtual Environment
Windows
venv\Scripts\activate
Linux / Mac
source venv/bin/activate
Install Dependencies
pip install -r requirements.txt
Configure Environment Variables

Create a .env file:

GEMINI_API_KEY=your_api_key
MONGO_URI=your_mongodb_uri
Run Backend
uvicorn app.main:app --reload

Backend runs at:

http://localhost:9000

Swagger Docs:

http://localhost:9000/docs
Frontend Setup
cd frontend
npm install
npm start

Frontend runs at:

http://localhost:3000
Docker Setup
Build Docker Image
docker build -t documedia .
Run Container
docker run -p 9000:9000 --env-file .env documedia
Deployment
Frontend
Deployed using Vercel
Backend
Deployed using Render

Project Highlights

Reduced manual document lookup effort through AI-powered querying
Implemented document-level isolation to prevent cross-document data leakage
Improved answer relevance using RAG-based retrieval
Enabled seamless interaction with uploaded media using timestamp navigation
Future Improvements
Semantic vector embeddings for improved retrieval accuracy
Multi-user authentication and user-specific document storage
Cloud storage integration for uploaded files
Real-time streaming AI responses
Enhanced document parsing for complex PDFs and media files
Advanced search and filtering capabilities

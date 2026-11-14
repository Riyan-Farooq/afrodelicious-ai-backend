\# Afrodelicious AI Backend



\## Project Overview



Afrodelicious AI Backend is a Python-based API built with FastAPI, CrewAI, and Groq. It provides AI agent functionality and recipe extraction capabilities.



\## AI Agents



\### 1. Recipe Collector

\- Extracts recipe information from supported recipe URLs.

\- Structures recipe details such as ingredients, instructions, preparation time, and servings.

\- Supports human review before recipes are published.

\- Intended for integration with the Afrodelicious website.



\### 2. Brendy

\- Standalone marketing and communications AI agent.

\- Supports marketing content and brand communication tasks.

\- Not integrated into the Afrodelicious website.



\### 3. SAM

\- Standalone product development and engineering AI agent.

\- Supports product planning and technical development tasks.

\- Not integrated into the Afrodelicious website.



\## Technologies Used



\- Python

\- FastAPI

\- CrewAI

\- Groq API



\## Requirements



\- Python 3.10 or newer

\- Groq API key



\## Installation



1\. Clone or download the repository.

2\. Open the project directory in your terminal.

3\. Create a virtual environment:



&#x20;  `python -m venv venv`



4\. Activate the environment (Windows):



&#x20;  `.\\venv\\Scripts\\Activate.ps1`



5\. Install dependencies:



&#x20;  `pip install -r requirements.txt`



6\. Create your environment file:



&#x20;  `Copy-Item .env.example .env`



7\. Add your own Groq API key to `.env`:



&#x20;  `GROQ\_API\_KEY=your\_groq\_api\_key\_here`



\## Run the Backend



`python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`



\## API Documentation



After starting the backend, open:



\- API documentation: http://127.0.0.1:8000/docs

\- Health check: http://127.0.0.1:8000/health



\## API Endpoint



`POST /api/agent`



Supported agent types:



\- `recipe`

\- `marketing`

\- `development`



\## Security



\- Never upload your `.env` file to GitHub.

\- Never share API keys publicly.

\- Use client-owned API credentials for production deployment.

\- Configure production environment variables on the hosting platform.



\## Important Note



Only the Recipe Collector is intended for integration with the Afrodelicious website. Brendy and SAM are provided as separate standalone agents.


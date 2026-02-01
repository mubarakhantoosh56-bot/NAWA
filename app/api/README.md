# AIMX 🚀
AI-powered Virtual Employee Platform

## Overview
AIMX is a modular AI SaaS platform designed to act as a *virtual employee* inside companies.
It provides intelligent chat, long-term memory, document generation, and scalable AI services
built with a clean and production-ready architecture.

This repository contains the *core backend system* of AIMX.

---

## Tech Stack
- *Backend:* FastAPI (Python)
- *AI Engine:* OpenAI API
- *Server:* Uvicorn
- *Architecture:* Modular / Service-Oriented
- *Memory:* Session-based conversational memory
- *Docs:* Swagger (OpenAPI)

---

## Project Status
✅ Core architecture implemented  
✅ AI Chat endpoint working  
✅ Memory system active  
✅ Billing & API key connected  
✅ Swagger UI operational  

This project is currently in *active development*.
Setup & Run (Windows)

1) Create & activate virtual environment

python -m venv .venv
..venv\Scripts\activate

2) Install dependencies

pip install -r requirements.txt

3) Create .env file

Create a file named .env in the project root and add the following line:

OPENAI_API_KEY=your_openai_api_key_here

4) Run the server

uvicorn app.main:app –reload

5) Open Swagger UI

http://127.0.0.1:8000/docs
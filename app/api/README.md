# NAWA
AI Workforce Platform

## Overview

NAWA (نواة) is an Arabic-first enterprise AI workforce platform designed to operate inside companies.
It provides intelligent chat, long-term memory, document-aware retrieval, and scalable AI services built with a clean backend architecture.

This repository contains the core backend system for NAWA.

## Tech Stack

- Backend: FastAPI (Python)
- AI Engine: OpenAI API
- Server: Uvicorn
- Architecture: Modular / Service-Oriented
- Memory: Session and institutional memory
- Docs: Swagger (OpenAPI)

## Project Status

- Core architecture implemented
- AI chat endpoint working
- Memory system active
- RAG file ingestion active
- Swagger UI operational

This project is currently in active development.

## Setup & Run (Windows)

1. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

3. Create `.env` in the project root and add local-only settings.

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Run the server.

   ```powershell
   uvicorn app.main:app --reload
   ```

5. Open Swagger UI.

   ```text
   http://127.0.0.1:8000/docs
   ```

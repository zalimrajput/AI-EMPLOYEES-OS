# IMPLEMENTATION_ORDER.md

This document outlines the strict chronological order in which the backend must be built. Attempting to build out of order will result in circular dependencies or architectural failures.

## 1. Environment & Configuration
**Reason:** The application cannot start without dependencies, and nothing can connect to the database or APIs without configuration.
- Install packages (FastAPI, SQLAlchemy, Pydantic, python-jose).
- Secure `config.py` and `database.py`.

## 2. Authentication (JWT Verification)
**Reason:** Every endpoint requires identity. RLS policies in the database will fail if the backend cannot correctly identify the `organization_id` of the user making the request.
- Implement `get_current_user` using the Supabase JWT.
- Remove old password-hashing code.

## 3. Database Models (Core)
**Reason:** You cannot write APIs or Services without the SQLAlchemy models that map to the database schema.
- Write models for `User`, `Organization`, `AI_Conversation`, `AI_Message`.

## 4. API Endpoints (Core)
**Reason:** The frontend requires these endpoints to prove end-to-end connectivity before building complex AI features.
- Implement `GET /api/v1/auth/me`.
- Implement `POST /api/v1/organizations` (for signups).

## 5. AI Engine & Chat API
**Reason:** The primary value proposition of the app is the AI Employees. We must prove the AI can stream a response to the UI before investing weeks in the CRUD APIs.
- Implement `model_router.py` (OpenRouter API calls).
- Implement `engine.py` (Prompt construction).
- Implement `POST /api/v1/ai-chat/messages`.

## 6. Domain Data Models & APIs (CRM, Finance, HR)
**Reason:** Once the AI can chat, it needs data to interact with. Building the domain logic allows the AI to use tools to fetch real data.
- Write models and routers for Leads, Customers, Invoices.

## 7. AI Tools
**Reason:** Now that the Domain APIs exist, we can give the AI agents Python functions (`tools`) that call those same services.
- Implement `search_crm`, `read_invoice`.

## 8. Background Workers (Celery)
**Reason:** With the core functionality working, we can offload slow operations (RAG embedding, email sending) to background workers to optimize API performance.

## 9. Production Hardening & Deployment
**Reason:** Only after the features are complete should time be spent on Dockerizing, rate limiting, and extensive error handling.

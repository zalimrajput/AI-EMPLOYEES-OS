# API_SPEC.md

This document specifies the required REST API endpoints for the AI Employee OS backend. These endpoints are strictly derived from the requirements of the frontend components and the existing database schema.

## Core & Identity

### `GET /api/v1/auth/me`
**Purpose:** Fetch the currently authenticated user's profile, roles, and organization context.
**Authentication:** Required (Supabase JWT).
**Request:** None.
**Response:** `{"id": "uuid", "email": "str", "organization_id": "uuid", "roles": ["str"]}`
**Validation:** JWT signature and expiration against `SUPABASE_JWT_SECRET`.
**Errors:** 401 Unauthorized (Invalid JWT).
**Database tables:** `users`, `user_roles`.
**Frontend Pages:** Global (Session Provider, `/login`).
**Priority:** Critical

### `POST /api/v1/organizations`
**Purpose:** Create a new organization during the self-serve signup flow.
**Authentication:** Required (Supabase JWT - user may not have an org yet).
**Request:** `{"name": "str", "industry": "str"}`
**Response:** `{"id": "uuid", "name": "str", "created_at": "timestamp"}`
**Validation:** `name` is required.
**Errors:** 400 Bad Request.
**Database tables:** `organizations`.
**Frontend Pages:** `/register`.
**Priority:** Critical

## AI Engine

### `POST /api/v1/ai-chat/conversations`
**Purpose:** Initialize a new chat session with a specific AI Agent.
**Authentication:** Required.
**Request:** `{"agent_id": "uuid", "title": "str"}`
**Response:** `{"id": "uuid", "agent_id": "uuid", "title": "str", "created_at": "timestamp"}`
**Validation:** `agent_id` must exist in `ai_employees` for the current org.
**Errors:** 404 Agent Not Found.
**Database tables:** `ai_conversations`, `ai_employees`.
**Frontend Pages:** `/dashboard/chat`.
**Priority:** Critical

### `POST /api/v1/ai-chat/messages`
**Purpose:** Send a message to an AI Agent and stream the response.
**Authentication:** Required.
**Request:** `{"conversation_id": "uuid", "content": "str"}`
**Response:** HTTP Chunked Transfer Encoding (Streaming text).
**Validation:** User must own the `conversation_id`.
**Errors:** 403 Forbidden.
**Database tables:** `ai_messages`.
**Frontend Pages:** `/dashboard/chat`.
**Priority:** Critical

## CRM Domain

### `GET /api/v1/crm/customers`
**Purpose:** List customers for the current organization.
**Authentication:** Required.
**Request:** Query Params: `?limit=10&offset=0`.
**Response:** `{"items": [{"id": "uuid", "name": "str", "email": "str", "status": "str"}], "total": int}`
**Validation:** None.
**Errors:** None.
**Database tables:** `customers`.
**Frontend Pages:** `/dashboard/crm`.
**Priority:** High

### `GET /api/v1/crm/leads`
**Purpose:** List leads for the current organization.
**Authentication:** Required.
**Request:** Query Params: `?status=new`.
**Response:** `{"items": [{"id": "uuid", "name": "str", "score": int}], "total": int}`
**Validation:** None.
**Errors:** None.
**Database tables:** `leads`.
**Frontend Pages:** `/dashboard/crm`.
**Priority:** High

## Settings

### `GET /api/v1/users`
**Purpose:** List all members of the current organization.
**Authentication:** Required (Org Admin role).
**Request:** None.
**Response:** `{"items": [{"id": "uuid", "email": "str", "role": "str"}]}`
**Validation:** Caller must have admin privileges in the organization.
**Errors:** 403 Forbidden.
**Database tables:** `users`, `user_roles`.
**Frontend Pages:** `/dashboard/settings`.
**Priority:** Medium

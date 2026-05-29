### 1. Monorepo Structure

- Root: `AI_in_HRM/`
- `backend/` — FastAPI app
- `frontend/` — Next.js 15
- `infrastructure/` — Docker, Nginx, scripts
- `docs/` — all spec and memory files

---

### 2. Tech Stack

- Backend: FastAPI, SQLAlchemy 2.x async, asyncpg, Alembic, Pydantic v2, python-jose, passlib[argon2], httpx, pdfplumber, python-docx, spaCy, scikit-learn, openai
- Frontend: Next.js 15, TypeScript, Tailwind, shadcn/ui, TanStack Query, react-hook-form, zod, axios, recharts
- DB: PostgreSQL 16
- Runtime: Python 3.12, Node 20

---

### 3. Clean Architecture Rules

- Controller: HTTP only — parse request, call service, return response. Zero business logic.
- Service: All business logic. Calls repository only. No direct DB. No HTTP objects.
- Repository: All DB interaction. Async SQLAlchemy only. No `SELECT *`. Parameterized queries only.
- AI layer (`app/ai/`): Standalone. Feature modules call AI via its public interface only.

---

### 4. SQLAlchemy Conventions

- All models inherit from shared `Base` in `app/core/database.py`
- Use SQLAlchemy 2.x `Mapped` / `mapped_column` syntax
- UUID PKs: `server_default=text("gen_random_uuid()")`
- Timestamps: `DateTime(timezone=True)`
- Soft delete: filter `deleted_at IS NULL` on all default queries where model has `deleted_at`
- Relationships: always define `back_populates` on both sides
- Never hardcode `DATABASE_URL` — always from `get_settings()`

Additional guidance (non-exhaustive, consistent with the above rules):

- Prefer explicit column selection in queries (no implicit entity expansion).
- Use `select()` + `.where()` + `.join()` + `.group_by()` for aggregates and reports.
- Favor DB-level aggregation (`COUNT`, `SUM`, `AVG`) over Python loops across large row sets.
- Keep queries deterministic where possible (important for caching and test stability).
- Prefer `scalar_one_or_none()` / `scalar_one()` where shape is known; avoid ambiguous result handling.

---

### 5. Pydantic v2 Conventions

- All inter-layer DTOs are Pydantic v2 models
- Use `model_config = ConfigDict(from_attributes=True)` on response models
- Never expose `password_hash`, raw tokens, or secrets in response schemas
- Use `EmailStr` for email fields; `min_length` / `max_length` on string fields

Additional guidance (non-exhaustive, consistent with the above rules):

- Keep request models strict: validate types and bounds at the boundary.
- Keep response models explicit: include only fields required by API contract.
- Use `Field(...)` for constraints and documentation when relevant.
- Nullable fields must be explicitly annotated (e.g. `str | None`).

---

### 6. Response Envelope Standards

Success: `{"success": true, "message": str, "data": T}`

Error: `{"success": false, "message": str, "errors": [{"field": str, "message": str}]}`

Paginated: `{"success": true, "message": str, "data": {"items": [...], "page": int, "page_size": int, "total_items": int, "total_pages": int}}`

All defined in `app/core/schemas.py`: `SuccessResponse[T]`, `ErrorResponse`, `PaginatedResponse[T]`

Additional guidance (non-exhaustive, consistent with the above rules):

- Every endpoint returns a `SuccessResponse[T]` on success, even for read-only routes.
- For `data=None` responses, keep the envelope consistent and explicit.
- For lists, use `PaginatedResponse[T]` unless the spec explicitly says “no pagination”.

---

### 7. Error Handling

- Each module has its own `errors.py` with typed exceptions
- Each module has its own `http.py` mapping exceptions → HTTP status codes
- Global handlers in `app/core/exceptions.py` catch unhandled exceptions
- Never expose stack traces or internal details in responses
- Standard status codes: 400 validation, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict, 422 schema, 500 server

Additional guidance (non-exhaustive, consistent with the above rules):

- Raise module-level exceptions inside services (not inside controllers).
- Repositories should not raise HTTP exceptions; they should return data/None or raise DB errors upward.
- Convert module errors to HTTP shape only in controllers (via the module `http.py` mapper).
- Keep error messages stable and user-safe (no secrets, no SQL, no stack traces).

---

### 8. RBAC Conventions

- Role slugs (canonical): `system_administrator`, `hr_manager`, `recruiter`, `department_manager`, `employee`
- All defined in `app/core/constants.py`
- `require_roles(*roles)` dependency factory in `app/core/security.py`
- Apply `require_roles` at route level; additional row-level checks in service
- `get_current_user()` raises 401 on missing/invalid/expired token
- Inactive users (`is_active=False`) → 401

Additional guidance (non-exhaustive, consistent with the above rules):

- Route-level RBAC is mandatory for protected endpoints.
- Service-level row scoping is mandatory where the endpoint accepts or implies resource identifiers.
- Prefer explicit “403 Insufficient permissions” over silent filtering when a request targets a specific resource.

---

### 9. Audit Logging

- `create_audit_log(action, resource_type, resource_id, actor_id, before_state, after_state, ip_address)` in each module's repository
- Called from service on every state-changing operation
- `before_state` / `after_state` are `dict | None` (JSONB)
- `resource_type` matches the table name (e.g. `"leave_requests"`, `"employees"`)

Additional guidance (non-exhaustive, consistent with the above rules):

- Log only after validation and before commit completes, capturing meaningful before/after snapshots.
- Avoid logging secrets (password hashes, tokens, raw resumes, or API keys).
- Keep `action` values consistent across the system; treat them as API-stable identifiers.

---

### 10. Soft Delete Convention

- Models with `deleted_at: Mapped[datetime | None]` use soft delete
- All default queries filter `deleted_at IS NULL`
- Hard delete only where schema has no `deleted_at` column
- Check `docs/schema.sql` to determine which applies per model

Additional guidance (non-exhaustive, consistent with the above rules):

- For soft-deleted entities, treat “not found” as 404 unless a specific endpoint is “include deleted”.
- Enforce uniqueness constraints carefully; where needed, ensure queries exclude deleted rows.

---

### 11. Pagination Standard

- All list endpoints accept `page` (default 1) and `page_size` (default 20, max 100)
- Return `PaginatedResponse[T]` inside `SuccessResponse`
- DB-level: use `.offset((page-1)*page_size).limit(page_size)` with a separate COUNT query

Additional guidance (non-exhaustive, consistent with the above rules):

- Sorting must be deterministic to avoid duplicates between pages.
- COUNT queries must match the same filters as the data query.

---

### 12. Security / Auth Conventions

- Passwords: Argon2 via `passlib[argon2]` exclusively
- Access token: 15 min TTL, signed with `JWT_SECRET_KEY`
- Refresh token: 7 days TTL, signed with `JWT_REFRESH_SECRET_KEY`, stored hashed
- Refresh rotation: every refresh invalidates old token and issues new one
- Reuse detection: revoked token presented → revoke ALL tokens for that user
- Password reset tokens: SHA-256 hashed, single-use, 24h expiry
- All TTLs from `config.py` — never hardcoded

Additional guidance (non-exhaustive, consistent with the above rules):

- Never return refresh tokens in logs, audit entries, or exception messages.
- Enforce consistent token parsing: `Authorization: Bearer <access_token>`.
- Treat all auth-related errors as user-safe and non-revealing.

---

### 13. Testing Conventions

- Unit tests: mock all repositories via `unittest.mock.AsyncMock`
- Integration tests: use `httpx.AsyncClient` with `ASGITransport`
- Mirror source paths under `backend/tests/`
- `pytest-asyncio` with `asyncio_mode = "auto"`
- Each test independent — no shared mutable state
- Coverage target: 80% (`pytest --cov=app --cov-fail-under=80`)

Additional guidance (non-exhaustive, consistent with the above rules):

- Service tests should focus on business rules and error cases.
- Route tests should focus on RBAC, request/response shapes, and controller wiring.
- Mock boundaries consistently: repository mocked in service tests; controller mocked in route tests.

---

### 14. Naming Conventions

- Python: `snake_case` variables/functions, `PascalCase` classes, `UPPER_SNAKE` constants
- DB columns: `snake_case` (match `schema.sql` exactly)
- Routes: `kebab-case` URL segments
- Files: `snake_case.py`
- No magic strings — use constants/enums for status values, roles, action names

Additional guidance (non-exhaustive, consistent with the above rules):

- Keep route paths stable; avoid breaking changes without explicit migration.
- Prefer module-local constants for status strings when not already standardized.

---

### 15. File Upload Conventions

- Validate MIME type by reading file magic bytes — never trust file extension
- Resume files: PDF/DOCX only, 10MB max, path from `RESUME_UPLOAD_DIR` config
- Profile photos: JPEG/PNG only, 5MB max

Additional guidance (non-exhaustive, consistent with the above rules):

- Enforce size limits before writing to disk.
- Use safe, non-colliding file names/paths; do not store untrusted names directly.
- Keep upload endpoints side-effect-safe: validate first, then persist.


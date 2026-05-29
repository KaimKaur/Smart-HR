# Smart HR — Implementation Plan

> **Source of Truth**: PRD.md · Architecture.md · schema.sql · API.md
> **Stack**: FastAPI · PostgreSQL · Next.js 15 · TypeScript · JWT · RBAC
> **Pattern**: Modular Monolith · Layered Clean Architecture · Feature-Based Frontend

---

## Complexity Legend

| Symbol | Meaning | Typical Effort |
|--------|---------|---------------|
| XS | Trivial — config or boilerplate | < 1 hour |
| S | Small — single unit of work | 1–3 hours |
| M | Medium — multiple units, some judgment | 3–6 hours |
| L | Large — cross-cutting, careful design | 6–12 hours |
| XL | Extra-large — multi-session, risky | 12–20 hours |

---

## Epic Index

| # | Epic | Tasks |
|---|------|-------|
| E1 | Project Scaffolding & Infrastructure | T-001 – T-012 |
| E2 | Database & Migrations | T-013 – T-018 |
| E3 | Core Backend: Auth Module | T-019 – T-030 |
| E4 | Core Backend: User & RBAC Module | T-031 – T-039 |
| E5 | Core Backend: Employee Module | T-040 – T-053 |
| E6 | Core Backend: Department & Designation | T-054 – T-061 |
| E7 | Core Backend: Attendance Module | T-062 – T-073 |
| E8 | Core Backend: Leave Module | T-074 – T-085 |
| E9 | Core Backend: Recruitment Module | T-086 – T-105 |
| E10 | Core Backend: AI Screening Engine | T-106 – T-115 |
| E11 | Core Backend: Performance Module | T-116 – T-128 |
| E12 | Core Backend: Notifications Module | T-129 – T-135 |
| E13 | Core Backend: Dashboard APIs | T-136 – T-141 |
| E14 | Core Backend: Reporting & Export | T-142 – T-150 |
| E15 | Core Backend: Audit Log Module | T-151 – T-156 |
| E16 | Frontend: Project Setup | T-157 – T-165 |
| E17 | Frontend: Auth Pages | T-166 – T-172 |
| E18 | Frontend: Employee Management | T-173 – T-182 |
| E19 | Frontend: Recruitment | T-183 – T-196 |
| E20 | Frontend: Attendance | T-197 – T-204 |
| E21 | Frontend: Leave Management | T-205 – T-212 |
| E22 | Frontend: Performance | T-213 – T-221 |
| E23 | Frontend: Dashboards | T-222 – T-228 |
| E24 | Frontend: Notifications | T-229 – T-233 |
| E25 | Frontend: Admin (Users & Audit) | T-234 – T-240 |
| E26 | Testing | T-241 – T-255 |
| E27 | DevOps & Deployment | T-256 – T-264 |

---

## E1 — Project Scaffolding & Infrastructure

### T-001
**Task**: Initialize monorepo root structure
**Description**: Create `smart-hr/` root directory. Add `frontend/`, `backend/`, `infrastructure/`, `docs/` folders. Add root `.gitignore`, `README.md`, and `docker-compose.yml` stub.
**Dependencies**: None
**Complexity**: XS
**Done Criteria**:
- Folder structure matches `architecture.md` exactly
- `.gitignore` covers Python, Node, env files
- `README.md` documents setup steps
- `docker-compose.yml` has service stubs for `frontend`, `backend`, `db`

---

### T-002
**Task**: Initialize FastAPI backend project
**Description**: Create `backend/` Python project with `pyproject.toml` (or `requirements.txt`). Install: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic`, `python-jose`, `passlib[argon2]`, `alembic`, `python-multipart`, `httpx`.
**Dependencies**: T-001
**Complexity**: XS
**Done Criteria**:
- `backend/requirements.txt` contains all required packages
- `uvicorn backend.app.main:app --reload` starts without error
- FastAPI OpenAPI UI available at `/docs`

---

### T-003
**Task**: Create backend module skeleton
**Description**: Create empty module folders under `backend/app/modules/`: `auth/`, `employee/`, `recruitment/`, `attendance/`, `leave/`, `performance/`, `reporting/`, `notifications/`. Each folder gets: `__init__.py`, `controller.py`, `service.py`, `repository.py`, `schema.py`, `model.py`, `routes.py`.
**Dependencies**: T-002
**Complexity**: XS
**Done Criteria**:
- All module folders exist with all 7 files
- No import errors on startup

---

### T-004
**Task**: Configure FastAPI application entry point
**Description**: Implement `backend/app/main.py`. Register all module routers under `/api/v1`. Configure CORS for frontend origin. Add global exception handlers for 400, 401, 403, 404, 422, 500. Implement standard response envelope `{"success": bool, "message": str, "data": {}}`.
**Dependencies**: T-003
**Complexity**: S
**Done Criteria**:
- All routers mounted at `/api/v1`
- CORS accepts `http://localhost:3000`
- Error responses follow the error envelope from API.md
- `GET /api/v1/health` returns `200 {"success": true, "message": "OK"}`

---

### T-005
**Task**: Configure database connection (SQLAlchemy async)
**Description**: Create `backend/app/core/database.py`. Configure async SQLAlchemy engine using `asyncpg`. Create `AsyncSession` factory. Implement `get_db()` dependency for FastAPI. Read `DATABASE_URL` from environment.
**Dependencies**: T-002
**Complexity**: S
**Done Criteria**:
- `get_db()` yields a valid `AsyncSession`
- Connection pool opens/closes cleanly on startup/shutdown
- `DATABASE_URL` is never hardcoded

---

### T-006
**Task**: Configure environment variable management
**Description**: Create `.env.example` at project root with all required variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, `CORS_ORIGINS`. Implement `backend/app/core/config.py` using Pydantic `BaseSettings`.
**Dependencies**: T-002
**Complexity**: XS
**Done Criteria**:
- `.env.example` documents every variable with a comment
- `config.py` raises a clear error on missing required variables
- No secrets appear in source code

---

### T-007
**Task**: Implement global response schemas (Pydantic)
**Description**: Create `backend/app/core/schemas.py`. Define: `SuccessResponse[T]`, `ErrorDetail`, `ErrorResponse`, `PaginatedResponse[T]` following API.md envelope and pagination standards.
**Dependencies**: T-002
**Complexity**: S
**Done Criteria**:
- `SuccessResponse`, `ErrorResponse`, `PaginatedResponse` are importable from `core.schemas`
- Generic type parameter works for any data type
- Pagination includes `page`, `page_size`, `total_items`, `total_pages`

---

### T-008
**Task**: Implement RBAC dependency middleware
**Description**: Create `backend/app/core/security.py`. Implement: JWT decode, `get_current_user()` dependency, `require_roles(*roles)` dependency factory. Roles: `system_administrator`, `hr_manager`, `recruiter`, `department_manager`, `employee`.
**Dependencies**: T-006
**Complexity**: M
**Done Criteria**:
- `get_current_user()` raises `401` on missing/invalid token
- `require_roles("hr_manager")` raises `403` if user lacks that role
- Roles loaded from `user_roles` + `roles` tables
- Unit-testable with mock tokens

---

### T-009
**Task**: Configure Alembic migrations
**Description**: Run `alembic init` inside `backend/`. Configure `alembic.ini` and `env.py` to use `DATABASE_URL` from environment. Point to `backend/app/database/` for migration scripts.
**Dependencies**: T-005
**Complexity**: S
**Done Criteria**:
- `alembic upgrade head` runs without error against a blank database
- `alembic downgrade base` reverses cleanly
- Migration files are committed to version control

---

### T-010
**Task**: Create initial Alembic migration from schema.sql
**Description**: Translate the complete `schema.sql` into Alembic migration `0001_initial_schema.py`. All tables, constraints, indexes, and extensions must be included.
**Dependencies**: T-009
**Complexity**: M
**Done Criteria**:
- `alembic upgrade head` creates all 30+ tables
- All constraints and indexes from `schema.sql` are present
- `alembic downgrade base` drops all tables cleanly
- Validated against schema.sql table-by-table

---

### T-011
**Task**: Create seed data script
**Description**: Implement `backend/scripts/seed.py`. Seed: 5 roles (`system_administrator`, `hr_manager`, `recruiter`, `department_manager`, `employee`), sample departments, designations, employment statuses (`active`, `inactive`, `on_leave`), attendance statuses (`present`, `absent`, `late`, `half_day`, `holiday`), leave types.
**Dependencies**: T-010
**Complexity**: S
**Done Criteria**:
- Script is idempotent (re-runnable without duplicates)
- All enum-like reference tables are populated
- At least one admin user is created with a known password
- Script documented in README

---

### T-012
**Task**: Initialize Next.js 15 frontend project
**Description**: Bootstrap `frontend/` with `create-next-app` using TypeScript, Tailwind CSS, App Router. Install: `axios`, `react-hook-form`, `zod`, `@hookform/resolvers`, `@tanstack/react-query`, `recharts`, `shadcn/ui`. Configure `src/` directory layout matching architecture.md.
**Dependencies**: T-001
**Complexity**: S
**Done Criteria**:
- `npm run dev` starts without error at `localhost:3000`
- Folder structure matches `architecture.md`: `app/`, `components/`, `features/`, `hooks/`, `services/`, `lib/`, `types/`, `providers/`, `constants/`
- Tailwind and shadcn/ui render a test component correctly

---

---

## E2 — Database & Migrations

### T-013
**Task**: Define SQLAlchemy ORM models — Auth & RBAC
**Description**: Create `backend/app/modules/auth/model.py` and `backend/app/modules/user/model.py`. Define ORM models for: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`. Use `mapped_column` with UUID primary keys.
**Dependencies**: T-005, T-010
**Complexity**: S
**Done Criteria**:
- All 5 models defined with correct column types matching schema.sql
- Relationships defined (user → roles, role → permissions)
- Models importable without errors

---

### T-014
**Task**: Define SQLAlchemy ORM models — Organization & Employees
**Description**: Define ORM models for: `departments`, `designations`, `employment_statuses`, `employees`. Include self-referential `manager_id` FK on `employees`.
**Dependencies**: T-013
**Complexity**: S
**Done Criteria**:
- All 4 models defined
- `employees.manager_id` self-reference configured correctly
- All FK relationships navigable via ORM

---

### T-015
**Task**: Define SQLAlchemy ORM models — Recruitment
**Description**: Define ORM models for: `jobs`, `job_skills`, `candidates`, `candidate_applications`, `candidate_status_history`, `resume_files`, `resume_analysis`, `candidate_notes`, `interviews`.
**Dependencies**: T-014
**Complexity**: M
**Done Criteria**:
- All 9 models defined with JSONB columns typed as `dict`
- `candidate_applications.ai_score` CHECK constraint reflected
- `jobs.status` CHECK constraint reflected

---

### T-016
**Task**: Define SQLAlchemy ORM models — Attendance & Leave
**Description**: Define ORM models for: `attendance_statuses`, `attendance_records`, `attendance_corrections`, `leave_types`, `leave_balances`, `leave_requests`, `leave_approvals`.
**Dependencies**: T-014
**Complexity**: S
**Done Criteria**:
- All 7 models defined
- Unique constraint on `attendance_records(employee_id, attendance_date)` reflected
- Unique constraint on `leave_balances(employee_id, leave_type_id)` reflected

---

### T-017
**Task**: Define SQLAlchemy ORM models — Performance
**Description**: Define ORM models for: `performance_cycles`, `performance_reviews`, `performance_metrics`, `employee_metric_scores`, `performance_feedback`.
**Dependencies**: T-014
**Complexity**: S
**Done Criteria**:
- All 5 models defined
- `performance_reviews.rating` CHECK (1–5) reflected
- `employee_metric_scores.score` CHECK (0–100) reflected

---

### T-018
**Task**: Define SQLAlchemy ORM models — Notifications & Audit
**Description**: Define ORM models for: `notifications`, `notification_preferences`, `audit_logs`.
**Dependencies**: T-013
**Complexity**: XS
**Done Criteria**:
- All 3 models defined
- `audit_logs.before_state` and `after_state` typed as `dict` (JSONB)
- `audit_logs.ip_address` typed as `str` (INET mapped via String)

---

---

## E3 — Core Backend: Auth Module

### T-019
**Task**: Implement password hashing utility
**Description**: In `backend/app/core/security.py`, implement `hash_password(plain: str) -> str` and `verify_password(plain: str, hashed: str) -> bool` using `passlib` with Argon2 algorithm.
**Dependencies**: T-008
**Complexity**: XS
**Done Criteria**:
- Argon2 is the active hashing scheme
- `verify_password` returns `False` for wrong passwords, `True` for correct
- Unit tests pass

---

### T-020
**Task**: Implement JWT token generation and validation
**Description**: Implement `create_access_token(data: dict) -> str`, `create_refresh_token(data: dict) -> str`, `decode_token(token: str) -> dict` in `core/security.py`. Access token TTL: 15 min. Refresh token TTL: 7 days.
**Dependencies**: T-006
**Complexity**: S
**Done Criteria**:
- Expired tokens raise `401`
- Tampered tokens raise `401`
- Token payload includes `sub` (user_id), `roles`, `exp`

---

### T-021
**Task**: Implement auth repository
**Description**: In `modules/auth/repository.py`, implement: `get_user_by_email(email)`, `get_user_by_id(id)`, `get_user_roles(user_id)`.
**Dependencies**: T-013
**Complexity**: S
**Done Criteria**:
- Queries use async SQLAlchemy
- Soft-deleted users (`deleted_at IS NOT NULL`) are excluded
- Returns `None` when not found (no exceptions)

---

### T-022
**Task**: Implement auth service — login
**Description**: In `modules/auth/service.py`, implement `login(email, password)`. Validate credentials, verify active user, return access + refresh tokens. Raise structured errors for invalid credentials or inactive account.
**Dependencies**: T-019, T-020, T-021
**Complexity**: S
**Done Criteria**:
- Returns `{"access_token": ..., "refresh_token": ..., "token_type": "bearer"}`
- Wrong password returns `401` with message "Invalid credentials"
- Inactive user returns `401` with message "Account is inactive"

---

### T-023
**Task**: Implement auth service — token refresh
**Description**: Implement `refresh_tokens(refresh_token: str)`. Validate refresh token, load user, issue new access + refresh token pair.
**Dependencies**: T-020, T-021
**Complexity**: S
**Done Criteria**:
- Invalid/expired refresh token returns `401`
- Returns new token pair on success

---

### T-024
**Task**: Implement auth service — logout
**Description**: Implement `logout(user_id)`. For MVP, return success (stateless JWT; token invalidation deferred to future blocklist feature). Log the logout event to `audit_logs`.
**Dependencies**: T-022
**Complexity**: XS
**Done Criteria**:
- Returns `204` on success
- Audit log entry created with action `"logout"`

---

### T-025
**Task**: Implement auth service — forgot password
**Description**: Implement `forgot_password(email)`. Generate a time-limited reset token (store hash in a transient mechanism or `users` table extension). For MVP: return the token in the response (email delivery is future scope).
**Dependencies**: T-021
**Complexity**: S
**Done Criteria**:
- Always returns `200` (prevents email enumeration)
- Reset token is valid for 1 hour
- Token is hashed before storage

---

### T-026
**Task**: Implement auth service — reset password
**Description**: Implement `reset_password(token, new_password)`. Validate reset token, update `password_hash`, invalidate token.
**Dependencies**: T-025
**Complexity**: S
**Done Criteria**:
- Invalid/expired token returns `400`
- Password updated and token invalidated atomically
- New password is Argon2-hashed before storage

---

### T-027
**Task**: Implement GET /auth/me
**Description**: Implement `get_me(current_user)` returning the authenticated user's profile: `id`, `email`, `is_active`, `roles`, `created_at`.
**Dependencies**: T-008, T-021
**Complexity**: XS
**Done Criteria**:
- Unauthenticated request returns `401`
- Returns user object with roles array
- Soft-deleted users cannot authenticate

---

### T-028
**Task**: Implement auth Pydantic schemas
**Description**: In `modules/auth/schema.py`, define: `LoginRequest`, `LoginResponse`, `RefreshRequest`, `RefreshResponse`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `MeResponse`.
**Dependencies**: T-007
**Complexity**: XS
**Done Criteria**:
- All fields match API.md request/response specs
- Email validated with Pydantic `EmailStr`
- Password min length 8 enforced

---

### T-029
**Task**: Wire auth routes
**Description**: In `modules/auth/routes.py`, register: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `GET /auth/me`. Mount router in `main.py`.
**Dependencies**: T-022 – T-027, T-028
**Complexity**: S
**Done Criteria**:
- All 6 endpoints return correct status codes
- OpenAPI docs show all endpoints with correct schemas
- `GET /auth/me` requires `Authorization: Bearer <token>`

---

### T-030
**Task**: Implement auth audit logging
**Description**: After every login and logout, write a record to `audit_logs` with: `actor_user_id`, `action` (`"login"` / `"logout"`), `resource_type` = `"auth"`, `ip_address` from request.
**Dependencies**: T-018, T-029
**Complexity**: S
**Done Criteria**:
- Login creates audit log row
- Logout creates audit log row
- `ip_address` is populated from `request.client.host`

---

---

## E4 — Core Backend: User & RBAC Module

### T-031
**Task**: Implement user repository
**Description**: In `modules/user/repository.py`, implement: `create_user`, `get_user_by_id`, `get_user_by_email`, `list_users` (paginated), `update_user`, `soft_delete_user`, `assign_role`, `remove_role`, `get_user_permissions`.
**Dependencies**: T-013
**Complexity**: M
**Done Criteria**:
- All queries are async
- `list_users` supports `search`, `page`, `page_size`
- Soft-deleted users excluded from list unless `include_deleted=True`

---

### T-032
**Task**: Implement user service
**Description**: In `modules/user/service.py`, implement business logic wrapping the repository. Enforce: email uniqueness on create, prevent deactivating self, prevent removing own admin role.
**Dependencies**: T-031
**Complexity**: M
**Done Criteria**:
- Duplicate email returns `409`
- Business rule violations return `400` with descriptive message
- All state changes write audit log entries

---

### T-033
**Task**: Implement user Pydantic schemas
**Description**: Define: `CreateUserRequest`, `UpdateUserRequest`, `UserResponse`, `AssignRoleRequest`, `UserListResponse`, `PermissionResponse`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- Password excluded from all response schemas
- `roles` returned as array of role name strings
- `is_active`, `created_at`, `updated_at` included in responses

---

### T-034
**Task**: Implement POST /users (Create User)
**Description**: Admin-only endpoint. Hash password, create user, assign default role if provided.
**Dependencies**: T-032, T-033, T-008
**Complexity**: S
**Done Criteria**:
- Returns `201` with created user (no password_hash)
- Only `system_administrator` can call this endpoint
- Duplicate email returns `409`

---

### T-035
**Task**: Implement GET /users and GET /users/{user_id}
**Description**: List users (paginated, searchable) and get single user. HR Manager and Admin access.
**Dependencies**: T-032, T-033
**Complexity**: S
**Done Criteria**:
- List supports `?search=`, `?page=`, `?page_size=`
- Returns pagination envelope
- Non-existent user returns `404`

---

### T-036
**Task**: Implement PATCH /users/{user_id} and DELETE /users/{user_id}
**Description**: Update user fields (email, is_active). Deactivate (soft-delete) user.
**Dependencies**: T-032, T-033
**Complexity**: S
**Done Criteria**:
- PATCH returns updated user
- DELETE sets `deleted_at`, returns `204`
- Cannot deactivate own account

---

### T-037
**Task**: Implement role assignment endpoints
**Description**: `POST /users/{user_id}/roles` and `DELETE /users/{user_id}/roles/{role_id}`. Admin only.
**Dependencies**: T-032
**Complexity**: S
**Done Criteria**:
- Assigning duplicate role returns `409`
- Removing non-assigned role returns `404`
- Changes written to `user_roles` table

---

### T-038
**Task**: Implement GET /users/{user_id}/permissions
**Description**: Returns all permissions for a user (via role → role_permissions join).
**Dependencies**: T-031
**Complexity**: S
**Done Criteria**:
- Returns flat list of permission names
- Aggregates across all assigned roles
- Admin-only access

---

### T-039
**Task**: Wire user/RBAC routes
**Description**: Register all user routes in `modules/user/routes.py` and mount in `main.py` under `/api/v1/users`.
**Dependencies**: T-034 – T-038
**Complexity**: XS
**Done Criteria**:
- All endpoints appear in OpenAPI docs
- RBAC enforced on every route
- Integration test: non-admin cannot create users

---

---

## E5 — Core Backend: Employee Module

### T-040
**Task**: Implement employee repository
**Description**: In `modules/employee/repository.py`, implement: `create_employee`, `get_employee_by_id`, `get_employee_by_code`, `list_employees` (with filters), `update_employee`, `soft_delete_employee`, `get_employee_by_user_id`, `get_direct_reports`.
**Dependencies**: T-014
**Complexity**: M
**Done Criteria**:
- `list_employees` supports: `search` (name/email/code), `department_id`, `designation_id`, `employment_status_id`, `sort_by`, `sort_order`, `page`, `page_size`
- Uses `idx_employee_department`, `idx_employee_code` indexes
- Soft-deleted employees excluded by default

---

### T-041
**Task**: Implement employee service
**Description**: Business logic: validate unique `employee_code`, validate FK references (department, designation, status exist), validate `manager_id` is an active employee, compute `full_name` as virtual field.
**Dependencies**: T-040
**Complexity**: M
**Done Criteria**:
- Duplicate `employee_code` → `409`
- Invalid `department_id` → `400`
- Self-referential `manager_id = employee.id` → `400`
- All mutations write audit logs

---

### T-042
**Task**: Implement employee Pydantic schemas
**Description**: Define: `CreateEmployeeRequest`, `UpdateEmployeeRequest`, `EmployeeResponse`, `EmployeeListResponse`, `EmployeeProfileResponse`, `EmployeeSearchResponse`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- `salary` excluded from Employee-role responses
- `department_name`, `designation_title`, `manager_name` included as nested objects
- `employee_code` pattern validated (non-empty, ≤50 chars)

---

### T-043
**Task**: Implement POST /employees
**Description**: HR Manager creates employee record. Optionally links to an existing `user_id`.
**Dependencies**: T-041, T-042, T-008
**Complexity**: S
**Done Criteria**:
- Returns `201` with full employee object
- Only `hr_manager` or `system_administrator` can call
- `join_date` must not be in the future

---

### T-044
**Task**: Implement GET /employees (list with filters)
**Description**: Paginated employee list. Support: `search`, `department_id`, `designation_id`, `status`, `sort_by`, `sort_order`.
**Dependencies**: T-041, T-042
**Complexity**: S
**Done Criteria**:
- Returns pagination envelope
- All filter parameters documented and functional
- Employees see only their own record (enforced in service)

---

### T-045
**Task**: Implement GET /employees/{employee_id}
**Description**: Get single employee. Includes department, designation, manager info.
**Dependencies**: T-041, T-042
**Complexity**: S
**Done Criteria**:
- Returns `404` for non-existent or soft-deleted employee
- Employee can fetch own record
- HR Manager can fetch any record

---

### T-046
**Task**: Implement PATCH /employees/{employee_id}
**Description**: Update employee. HR Manager can update any field. Employee can update limited fields (phone only for MVP).
**Dependencies**: T-041, T-042
**Complexity**: S
**Done Criteria**:
- Returns updated employee on success
- Employee cannot update salary, department, designation
- Audit log written on every update

---

### T-047
**Task**: Implement DELETE /employees/{employee_id} (deactivate)
**Description**: Soft-delete by setting `deleted_at`. Does not delete the linked user account.
**Dependencies**: T-041
**Complexity**: XS
**Done Criteria**:
- Returns `204`
- `deleted_at` is set, `updated_at` is updated
- Admin-only operation

---

### T-048
**Task**: Implement GET /employees/{employee_id}/profile
**Description**: Returns extended profile including department, designation, manager, employment status. Accessible to the employee themselves and HR Managers.
**Dependencies**: T-041, T-042
**Complexity**: S
**Done Criteria**:
- Returns all profile fields
- Salary visible only to HR/Admin roles
- `404` for unknown employee

---

### T-049
**Task**: Implement GET /employees/{employee_id}/manager
**Description**: Returns the employee's reporting manager details.
**Dependencies**: T-041
**Complexity**: XS
**Done Criteria**:
- Returns `null` if no manager assigned
- Returns manager's name, code, designation, department

---

### T-050
**Task**: Implement GET /employees/{employee_id}/reports
**Description**: Returns list of employees who report to this employee (direct reports).
**Dependencies**: T-040
**Complexity**: S
**Done Criteria**:
- Uses `idx_employee_manager` index
- Returns paginated list
- Empty list (not 404) if no reports

---

### T-051
**Task**: Implement GET /employees/search
**Description**: Search endpoint with query parameter `q`. Searches `first_name`, `last_name`, `email`, `employee_code`.
**Dependencies**: T-040
**Complexity**: S
**Done Criteria**:
- Returns top 20 matches by default
- Case-insensitive search using `ILIKE`
- Results include `id`, `full_name`, `employee_code`, `department`

---

### T-052
**Task**: Implement employee audit logging
**Description**: Write to `audit_logs` on: create, update, deactivate. Include `before_state` (JSONB snapshot) and `after_state`.
**Dependencies**: T-018, T-043 – T-047
**Complexity**: S
**Done Criteria**:
- Every mutation has a corresponding audit log row
- `before_state` captures old values on update
- `after_state` captures new values

---

### T-053
**Task**: Wire employee routes
**Description**: Register all employee routes in `modules/employee/routes.py` under `/api/v1/employees`.
**Dependencies**: T-043 – T-052
**Complexity**: XS
**Done Criteria**:
- All routes registered and visible in OpenAPI
- RBAC enforced per API.md authorization matrix
- Integration test: employee cannot list all employees

---

---

## E6 — Core Backend: Department & Designation Module

### T-054
**Task**: Implement department repository and service
**Description**: CRUD for `departments`. Prevent deletion if employees are assigned. `list_departments` returns all departments with employee count.
**Dependencies**: T-014
**Complexity**: S
**Done Criteria**:
- Delete with assigned employees returns `409`
- Unique name enforced → `409`
- Employee count included in list response

---

### T-055
**Task**: Implement department Pydantic schemas
**Description**: `CreateDepartmentRequest`, `UpdateDepartmentRequest`, `DepartmentResponse`.
**Dependencies**: T-007
**Complexity**: XS
**Done Criteria**:
- `name` max 150 chars, required, non-empty

---

### T-056
**Task**: Wire department routes (CRUD)
**Description**: `POST`, `GET` (list), `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` under `/api/v1/departments`. Admin and HR Manager access.
**Dependencies**: T-054, T-055
**Complexity**: S
**Done Criteria**:
- All 5 routes functional
- `DELETE` returns `409` if department has active employees

---

### T-057
**Task**: Implement designation repository and service
**Description**: CRUD for `designations`. Prevent deletion if employees are assigned. Unique title enforced.
**Dependencies**: T-014
**Complexity**: S
**Done Criteria**:
- Same pattern as departments
- Employee count in list response

---

### T-058
**Task**: Implement designation Pydantic schemas
**Description**: `CreateDesignationRequest`, `UpdateDesignationRequest`, `DesignationResponse`.
**Dependencies**: T-007
**Complexity**: XS
**Done Criteria**:
- `title` max 150 chars, required

---

### T-059
**Task**: Wire designation routes (CRUD)
**Description**: `/api/v1/designations` full CRUD. Same access pattern as departments.
**Dependencies**: T-057, T-058
**Complexity**: S
**Done Criteria**:
- All 5 routes functional
- Mirrors department endpoint behavior

---

### T-060
**Task**: Implement employment status endpoints
**Description**: `GET /api/v1/employment-statuses` — returns list of all employment statuses. Seed data populated via T-011.
**Dependencies**: T-014
**Complexity**: XS
**Done Criteria**:
- Returns all statuses from `employment_statuses`
- No create/delete (reference data, managed via seed)

---

### T-061
**Task**: Implement attendance status endpoints
**Description**: `GET /api/v1/attendance-statuses` — returns list. Reference data only.
**Dependencies**: T-016
**Complexity**: XS
**Done Criteria**:
- Returns all statuses from `attendance_statuses`

---

---

## E7 — Core Backend: Attendance Module

### T-062
**Task**: Implement attendance repository
**Description**: In `modules/attendance/repository.py`: `create_check_in`, `update_check_out`, `get_record_by_employee_date`, `list_records` (by employee, date range), `get_monthly_summary`, `create_correction`, `list_corrections`, `update_correction_status`.
**Dependencies**: T-016
**Complexity**: M
**Done Criteria**:
- Uses `idx_attendance_employee_date` composite index
- Monthly summary aggregates by status
- All queries async

---

### T-063
**Task**: Implement attendance service — check-in
**Description**: `check_in(employee_id, timestamp)`. Validate: employee is active, no existing record for today, timestamp is today's date. Create `attendance_records` row with `check_in_time`.
**Dependencies**: T-062
**Complexity**: S
**Done Criteria**:
- Duplicate check-in returns `409`
- Returns created attendance record
- Sets `attendance_status_id` to "present" on check-in

---

### T-064
**Task**: Implement attendance service — check-out
**Description**: `check_out(employee_id, timestamp)`. Validate existing check-in exists for today. Update `check_out_time` and compute `work_duration_minutes`.
**Dependencies**: T-062
**Complexity**: S
**Done Criteria**:
- Check-out without prior check-in returns `400`
- `work_duration_minutes` = `(check_out - check_in) / 60` (integer)
- Cannot check out twice

---

### T-065
**Task**: Implement attendance service — history and filters
**Description**: `get_attendance_history(employee_id, date_from, date_to, page, page_size)`. HR Manager can query any employee. Employee can only query own records.
**Dependencies**: T-062
**Complexity**: S
**Done Criteria**:
- Paginated results
- Date range filter enforced
- Includes status name (joined from `attendance_statuses`)

---

### T-066
**Task**: Implement attendance service — daily attendance
**Description**: `get_daily_attendance(date)`. HR Manager view: all employees' attendance for a given date. Returns present/absent/late counts.
**Dependencies**: T-062
**Complexity**: S
**Done Criteria**:
- Returns per-employee status for the date
- Missing records treated as "absent"
- Accessible only by HR Manager/Admin

---

### T-067
**Task**: Implement attendance service — monthly summary
**Description**: `get_monthly_summary(employee_id, year, month)`. Returns counts: `present_days`, `absent_days`, `late_days`, `half_days`, `total_working_days`, `total_hours`.
**Dependencies**: T-062
**Complexity**: M
**Done Criteria**:
- Totals computed from `attendance_records`
- Employee can view own summary; HR can view any
- Returns `404` if employee not found

---

### T-068
**Task**: Implement attendance corrections — request
**Description**: `POST /attendance/{record_id}/corrections`. Employee submits correction request with `reason`. Creates row in `attendance_corrections` with status `"pending"`.
**Dependencies**: T-062
**Complexity**: S
**Done Criteria**:
- Only employee who owns the record can request
- Returns created correction object
- Duplicate pending correction for same record → `409`

---

### T-069
**Task**: Implement attendance corrections — review
**Description**: `PATCH /attendance/corrections/{correction_id}`. HR Manager approves or rejects. Updates `correction_status`, `reviewed_by`, `reviewed_at`.
**Dependencies**: T-068
**Complexity**: S
**Done Criteria**:
- HR Manager/Admin only
- Valid statuses: `"approved"`, `"rejected"`
- `reviewed_at` set to current timestamp

---

### T-070
**Task**: Implement attendance Pydantic schemas
**Description**: `CheckInRequest`, `CheckOutRequest`, `AttendanceRecordResponse`, `MonthlySummaryResponse`, `CorrectionRequest`, `CorrectionResponse`, `DailyAttendanceResponse`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- All date fields use `date` type
- All timestamps use `datetime` with timezone
- `work_duration_minutes` is nullable (null until check-out)

---

### T-071
**Task**: Wire attendance routes
**Description**: Register under `/api/v1/attendance`: `POST /check-in`, `POST /check-out`, `GET /`, `GET /daily`, `GET /monthly`, `GET /{record_id}/corrections`, `POST /{record_id}/corrections`, `PATCH /corrections/{correction_id}`.
**Dependencies**: T-063 – T-070
**Complexity**: S
**Done Criteria**:
- All routes registered and documented in OpenAPI
- RBAC enforced per API.md matrix

---

### T-072
**Task**: Implement attendance report endpoint
**Description**: `GET /api/v1/attendance/report`. HR Manager only. Filters: `department_id`, `date_from`, `date_to`, `status`. Returns paginated rows with employee details.
**Dependencies**: T-062, T-070
**Complexity**: M
**Done Criteria**:
- Joins `employees`, `departments`, `attendance_statuses`
- Supports all filter parameters
- Returns pagination envelope

---

### T-073
**Task**: Implement attendance audit logging
**Description**: Log to `audit_logs`: check-in, check-out, correction approval/rejection.
**Dependencies**: T-018, T-063, T-064, T-069
**Complexity**: XS
**Done Criteria**:
- Each action type has a distinct `action` string
- `resource_type = "attendance_records"`

---

---

## E8 — Core Backend: Leave Module

### T-074
**Task**: Implement leave repository
**Description**: `create_leave_request`, `get_leave_request_by_id`, `list_leave_requests` (filters), `update_leave_status`, `get_leave_balance`, `update_leave_balance`, `create_leave_approval`, `list_pending_approvals`, `get_leave_history`.
**Dependencies**: T-016
**Complexity**: M
**Done Criteria**:
- All queries async
- `list_leave_requests` supports: `employee_id`, `status`, `leave_type_id`, `date_from`, `date_to`
- Uses `idx_leave_employee`, `idx_leave_status` indexes

---

### T-075
**Task**: Implement leave service — create request
**Description**: `create_leave_request(employee_id, leave_type_id, start_date, end_date, reason)`. Validate: `end_date >= start_date`, sufficient balance exists, no overlapping approved leave.
**Dependencies**: T-074
**Complexity**: M
**Done Criteria**:
- Insufficient balance → `400` with current balance in error
- Overlapping dates → `409`
- Creates request with status `"pending"`
- Triggers notification to manager (call notification service)

---

### T-076
**Task**: Implement leave service — approve/reject
**Description**: `approve_leave(leave_request_id, approver_id, remarks)` and `reject_leave(leave_request_id, approver_id, remarks)`. On approval: deduct balance from `leave_balances`.
**Dependencies**: T-074
**Complexity**: M
**Done Criteria**:
- Approver must be a valid employee with HR Manager or Department Manager role
- Cannot approve own leave request
- Approval deducts calendar days from balance
- Creates row in `leave_approvals`
- Triggers notification to requesting employee

---

### T-077
**Task**: Implement leave service — cancel
**Description**: `cancel_leave(leave_request_id, requesting_user_id)`. Employee can cancel own pending request. HR can cancel pending/approved requests. Restore balance if cancelling approved leave.
**Dependencies**: T-074
**Complexity**: S
**Done Criteria**:
- Only pending/approved requests can be cancelled
- Balance restored for approved → cancelled transitions
- Status set to `"cancelled"`

---

### T-078
**Task**: Implement leave balance endpoint
**Description**: `GET /leave/balance` and `GET /leave/balance/{employee_id}`. Returns all leave types with current balance for the employee.
**Dependencies**: T-074
**Complexity**: S
**Done Criteria**:
- Employee sees own balance; HR sees any employee's
- Returns list of `{leave_type, annual_allocation, current_balance}`

---

### T-079
**Task**: Implement pending approvals endpoint
**Description**: `GET /leave/pending-approvals`. Returns all leave requests pending approval, filtered by approver's scope (HR sees all; Department Manager sees team).
**Dependencies**: T-074
**Complexity**: M
**Done Criteria**:
- HR Manager sees all pending
- Department Manager sees only their direct reports
- Sorted by `created_at` ascending

---

### T-080
**Task**: Implement leave history endpoint
**Description**: `GET /leave/history` — paginated history for an employee. `GET /leave` — HR list with all filters.
**Dependencies**: T-074
**Complexity**: S
**Done Criteria**:
- Employee sees own history only
- HR can filter by any employee, status, date range
- Results include leave type name, approver name

---

### T-081
**Task**: Implement leave Pydantic schemas
**Description**: `CreateLeaveRequest`, `LeaveRequestResponse`, `LeaveApprovalRequest`, `LeaveBalanceResponse`, `LeaveListResponse`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- `start_date` and `end_date` are `date` types
- Status enum: `pending`, `approved`, `rejected`, `cancelled`
- `approval_level` included in approval response

---

### T-082
**Task**: Wire leave routes
**Description**: Register under `/api/v1/leave`: `POST /`, `GET /`, `GET /{id}`, `POST /{id}/approve`, `POST /{id}/reject`, `POST /{id}/cancel`, `GET /balance`, `GET /balance/{employee_id}`, `GET /pending-approvals`, `GET /history`.
**Dependencies**: T-075 – T-081
**Complexity**: S
**Done Criteria**:
- All routes operational and in OpenAPI docs
- RBAC enforced per authorization matrix

---

### T-083
**Task**: Implement leave type management endpoints
**Description**: CRUD for `leave_types`. Admin/HR only. `GET /leave-types` is accessible to all authenticated users.
**Dependencies**: T-016
**Complexity**: S
**Done Criteria**:
- `annual_allocation` must be positive integer
- Unique name enforced
- Deletion blocked if active leave balances exist

---

### T-084
**Task**: Implement leave balance initialization
**Description**: `POST /leave/balance/initialize` — HR Manager initializes leave balances for an employee (or all employees) for the current year. Populates `leave_balances` from `leave_types.annual_allocation`.
**Dependencies**: T-074
**Complexity**: S
**Done Criteria**:
- Idempotent: re-running does not reset existing balances
- Returns list of created balance records

---

### T-085
**Task**: Implement leave audit logging
**Description**: Log create, approve, reject, cancel to `audit_logs`.
**Dependencies**: T-018, T-075 – T-077
**Complexity**: XS
**Done Criteria**:
- `resource_type = "leave_requests"`
- `before_state` and `after_state` capture status transitions

---

---

## E9 — Core Backend: Recruitment Module

### T-086
**Task**: Implement job repository
**Description**: `create_job`, `get_job_by_id`, `list_jobs` (filtered), `update_job`, `soft_delete_job`, `publish_job`, `close_job`, `add_job_skill`, `remove_job_skill`, `get_job_skills`.
**Dependencies**: T-015
**Complexity**: M
**Done Criteria**:
- `list_jobs` supports: `status`, `department_id`, `search`, `sort_by`, `sort_order`
- Uses `idx_jobs_status` index
- Skills loaded as list of strings

---

### T-087
**Task**: Implement job service
**Description**: Business rules: only `draft` jobs can be published, only `published` jobs can be closed, deleted jobs cannot be updated, `department_id` must reference existing department.
**Dependencies**: T-086
**Complexity**: M
**Done Criteria**:
- Invalid status transitions return `400`
- Publish sets `status = "published"`
- Close sets `status = "closed"`
- Audit log written on every status change

---

### T-088
**Task**: Implement job Pydantic schemas
**Description**: `CreateJobRequest`, `UpdateJobRequest`, `JobResponse`, `JobListResponse`. Skills as `List[str]`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- `status` enum: `draft`, `published`, `closed`
- `skills` is a list of skill name strings
- `created_by_name` returned in response

---

### T-089
**Task**: Wire job routes
**Description**: Under `/api/v1/jobs`: `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `POST /{id}/publish`, `POST /{id}/close`.
**Dependencies**: T-087, T-088
**Complexity**: S
**Done Criteria**:
- All routes operational
- HR Manager and Recruiter can create/manage jobs
- Status transition routes return updated job

---

### T-090
**Task**: Implement candidate repository
**Description**: `create_candidate`, `get_candidate_by_id`, `get_candidate_by_email`, `list_candidates` (filtered), `soft_delete_candidate`, `get_applications_by_candidate`, `create_application`, `get_application_by_id`, `list_applications_by_job`, `update_application_status`, `create_status_history`.
**Dependencies**: T-015
**Complexity**: M
**Done Criteria**:
- List supports: `job_id`, `status`, `search`, `sort_by ai_score`, `sort_order`
- Uses `idx_candidate_application_job`, `idx_candidate_application_score`

---

### T-091
**Task**: Implement candidate service
**Description**: Business rules: email uniqueness per candidate, valid `job_id` required for application, status transition validation (cannot move backward), `recruiter_override` flag management.
**Dependencies**: T-090
**Complexity**: M
**Done Criteria**:
- Duplicate candidate email → `409`
- Status history row created on every status change
- `changed_by` populated from authenticated user

---

### T-092
**Task**: Implement candidate Pydantic schemas
**Description**: `CreateCandidateRequest`, `CandidateResponse`, `CreateApplicationRequest`, `ApplicationResponse`, `CandidateStatusUpdateRequest`, `CandidateTimelineResponse`, `CandidateRankingResponse`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- `ai_score` nullable (null until screening)
- `ranking` nullable
- `application_status` enum documented
- Timeline includes timestamp and actor

---

### T-093
**Task**: Wire candidate routes
**Description**: Under `/api/v1/candidates` and `/api/v1/jobs/{job_id}/candidates`: `POST`, `GET`, `GET /{id}`, `PATCH /{id}/status`, `GET /{id}/timeline`, `POST /{id}/shortlist`, `POST /{id}/reject`.
**Dependencies**: T-091, T-092
**Complexity**: S
**Done Criteria**:
- Shortlist sets `application_status = "shortlisted"`
- Reject sets `application_status = "rejected"`
- Timeline returns ordered status history

---

### T-094
**Task**: Implement resume file upload endpoint
**Description**: `POST /candidates/{candidate_id}/resume`. Accept `multipart/form-data`. Store file metadata in `resume_files`. For MVP: store file on local filesystem at `/uploads/resumes/`. Return file URL.
**Dependencies**: T-090
**Complexity**: M
**Done Criteria**:
- Accepts PDF and DOCX only (validate MIME type)
- Max file size: 10MB
- Stores `file_name`, `file_url`, `uploaded_at` in `resume_files`
- Returns `resume_file_id` and `file_url`

---

### T-095
**Task**: Implement candidate notes endpoints
**Description**: `POST /candidates/{candidate_id}/notes`, `GET /candidates/{candidate_id}/notes`. Create and list notes for a candidate.
**Dependencies**: T-090
**Complexity**: S
**Done Criteria**:
- `note` text required, max 5000 chars
- `created_by` populated from authenticated user
- List sorted by `created_at` descending

---

### T-096
**Task**: Implement manual override endpoint
**Description**: `POST /candidates/{application_id}/override`. Recruiter sets `recruiter_override = true`, updates `application_status` manually, bypassing AI recommendation.
**Dependencies**: T-090, T-091
**Complexity**: S
**Done Criteria**:
- Sets `recruiter_override = true`
- Status transition recorded in `candidate_status_history`
- Audit log written
- Accessible by Recruiter and HR Manager

---

### T-097
**Task**: Implement candidate ranking endpoint
**Description**: `GET /jobs/{job_id}/candidates/ranking`. Returns candidates sorted by `ai_score DESC`, then `ranking ASC`. Includes `matched_skills`, `missing_skills`, `recommendation`.
**Dependencies**: T-090, T-015
**Complexity**: S
**Done Criteria**:
- Joins `candidate_applications`, `resume_analysis`, `candidates`
- Returns ranked list with AI fields
- Paginated

---

### T-098
**Task**: Implement interview scheduling endpoints
**Description**: `POST /interviews`, `GET /interviews`, `GET /interviews/{id}`, `PATCH /interviews/{id}`. Linked to `candidate_applications`. Status: `scheduled`, `completed`, `cancelled`.
**Dependencies**: T-015
**Complexity**: M
**Done Criteria**:
- `application_id` must reference existing application
- `interviewer_id` must reference existing employee
- `scheduled_at` must be in the future
- List filterable by `application_id`, `interviewer_id`, `status`

---

### T-099
**Task**: Implement interview Pydantic schemas
**Description**: `ScheduleInterviewRequest`, `UpdateInterviewRequest`, `InterviewResponse`.
**Dependencies**: T-007
**Complexity**: XS
**Done Criteria**:
- `scheduled_at` validated as future datetime
- Status enum: `scheduled`, `completed`, `cancelled`

---

### T-100
**Task**: Wire interview routes
**Description**: Under `/api/v1/interviews`: full CRUD. Accessible by Recruiter, HR Manager, Admin.
**Dependencies**: T-098, T-099
**Complexity**: XS
**Done Criteria**:
- All routes operational
- RBAC enforced

---

### T-101
**Task**: Implement resume analysis get endpoint
**Description**: `GET /candidates/{candidate_id}/analysis`. Returns the latest `resume_analysis` record for a candidate.
**Dependencies**: T-015
**Complexity**: S
**Done Criteria**:
- Returns `404` if no analysis exists yet
- Returns JSONB fields deserialized: `extracted_skills`, `matched_skills`, `missing_skills`, `explanation`
- Includes `score` and `recommendation`

---

### T-102
**Task**: Implement GET /jobs/{job_id}/candidates/analysis-results
**Description**: Returns analysis results for all candidates of a job. Sorted by score descending.
**Dependencies**: T-015, T-090
**Complexity**: S
**Done Criteria**:
- Joins `candidate_applications`, `resume_analysis`, `candidates`
- Paginated
- Recruiter and HR Manager access

---

### T-103
**Task**: Wire recruitment audit logging
**Description**: Log to `audit_logs`: job create/publish/close, candidate create, status change, manual override.
**Dependencies**: T-018, T-087, T-091, T-096
**Complexity**: S
**Done Criteria**:
- Distinct action strings for each event type
- `resource_type` set correctly per entity

---

### T-104
**Task**: Implement recruitment report endpoint
**Description**: `GET /api/v1/reports/recruitment`. Filters: `job_id`, `status`, `date_from`, `date_to`. Returns: total candidates, shortlisted, rejected, pending, average AI score per job.
**Dependencies**: T-090
**Complexity**: M
**Done Criteria**:
- All aggregations computed in database
- Paginated job-level breakdown
- HR Manager and Admin access

---

### T-105
**Task**: Implement GET /jobs/{job_id}/candidates (with sorting)
**Description**: List candidates for a specific job. Supports: `sort_by=ai_score`, `sort_order=desc`, `status` filter.
**Dependencies**: T-090, T-092
**Complexity**: S
**Done Criteria**:
- Returns paginated candidate list
- Each row includes `ai_score`, `ranking`, `recommendation`, `application_status`

---

---

## E10 — Core Backend: AI Screening Engine

### T-106
**Task**: Set up AI module structure
**Description**: Create `backend/app/ai/` with: `parser.py` (resume parsing), `extractor.py` (skill extraction), `matcher.py` (TF-IDF + cosine similarity), `scorer.py` (score computation), `screener.py` (orchestrator).
**Dependencies**: T-002
**Complexity**: S
**Done Criteria**:
- All modules importable
- Install: `pymupdf`, `spacy`, `scikit-learn`, `python-docx`
- `python -m spacy download en_core_web_sm` documented in setup

---

### T-107
**Task**: Implement resume parser (PDF + DOCX)
**Description**: In `ai/parser.py`, implement `extract_text(file_path: str) -> str`. Handle PDF via PyMuPDF (`fitz`), DOCX via `python-docx`. Return raw text.
**Dependencies**: T-106
**Complexity**: M
**Done Criteria**:
- Handles multi-page PDFs
- Handles DOCX with tables and lists
- Returns empty string (not exception) for unreadable files
- Unit tested with sample files

---

### T-108
**Task**: Implement skill extractor (spaCy NLP)
**Description**: In `ai/extractor.py`, implement `extract_skills(text: str) -> list[str]`. Use spaCy NER + a curated skills vocabulary list. Return deduplicated, normalized skill names.
**Dependencies**: T-106, T-107
**Complexity**: L
**Done Criteria**:
- Extracts common technical skills (Python, SQL, React, etc.)
- Case-normalized output (e.g., "python" → "Python")
- Returns `[]` for empty/unparseable text
- Unit tested with 5+ sample resumes

---

### T-109
**Task**: Implement job-resume matcher (TF-IDF + cosine)
**Description**: In `ai/matcher.py`, implement `compute_match(job_skills: list[str], candidate_skills: list[str]) -> dict`. Returns: `matched_skills`, `missing_skills`, `score` (0–100).
**Dependencies**: T-108
**Complexity**: M
**Done Criteria**:
- Uses scikit-learn TF-IDF vectorizer
- Score is cosine similarity scaled to 0–100
- `matched_skills` = intersection
- `missing_skills` = job_skills not in candidate_skills
- Score is deterministic for same inputs

---

### T-110
**Task**: Implement scorer and recommendation logic
**Description**: In `ai/scorer.py`, implement `generate_recommendation(score: float) -> str`. Rules: score ≥ 70 → "Shortlist", 40–69 → "Review", < 40 → "Reject".
**Dependencies**: T-109
**Complexity**: XS
**Done Criteria**:
- Threshold values match PRD requirements
- Returns one of three string values only
- Unit tested for boundary conditions

---

### T-111
**Task**: Implement AI screener orchestrator
**Description**: In `ai/screener.py`, implement `screen_candidate(candidate_id, job_id, file_path) -> dict`. Calls parser → extractor → matcher → scorer. Writes result to `resume_analysis` table. Updates `candidate_applications.ai_score`, `ranking`, `recommendation`.
**Dependencies**: T-107 – T-110, T-015
**Complexity**: L
**Done Criteria**:
- End-to-end pipeline produces a `resume_analysis` row
- `candidate_applications` updated atomically
- All JSONB fields (`extracted_skills`, `matched_skills`, `missing_skills`, `explanation`) populated
- Returns the analysis result dict

---

### T-112
**Task**: Implement POST /candidates/{candidate_id}/analyze (trigger analysis)
**Description**: Endpoint to trigger AI screening for a candidate. Validates resume exists, runs `screen_candidate()`, returns analysis result.
**Dependencies**: T-111, T-094
**Complexity**: M
**Done Criteria**:
- Returns `400` if no resume file exists
- Returns analysis result on success
- Idempotent: re-triggering overwrites previous analysis
- Accessible by Recruiter and HR Manager

---

### T-113
**Task**: Implement auto-ranking after analysis
**Description**: After each screening, recompute `ranking` field for all `candidate_applications` of the same job, ordered by `ai_score DESC`.
**Dependencies**: T-111
**Complexity**: M
**Done Criteria**:
- Ranking is 1-indexed, no gaps
- Ties broken by `created_at ASC`
- Ranking updated in a single bulk UPDATE query

---

### T-114
**Task**: Implement GET /candidates/{application_id}/match-explanation
**Description**: Returns the `explanation` JSONB field from `resume_analysis`, formatted as a human-readable breakdown of matched and missing skills with score rationale.
**Dependencies**: T-101
**Complexity**: S
**Done Criteria**:
- Returns structured explanation object
- Includes `score`, `matched_skills`, `missing_skills`, `recommendation`
- Returns `404` if no analysis exists

---

### T-115
**Task**: Write AI pipeline integration test
**Description**: End-to-end test: upload a sample PDF resume, trigger analysis, verify `resume_analysis` row exists with correct fields, verify `candidate_applications` updated.
**Dependencies**: T-112, T-113
**Complexity**: M
**Done Criteria**:
- Test passes with a real PDF file
- `score` is between 0 and 100
- `matched_skills` is a subset of job skills
- `ranking` is assigned

---

---

## E11 — Core Backend: Performance Module

### T-116
**Task**: Implement performance repository
**Description**: CRUD for: `performance_cycles`, `performance_reviews`, `performance_metrics`, `employee_metric_scores`, `performance_feedback`. List reviews by `employee_id`, `cycle_id`, `reviewer_id`.
**Dependencies**: T-017
**Complexity**: M
**Done Criteria**:
- Uses `idx_review_employee` index
- Metric scores loaded as list per review
- Feedback loaded as list per review

---

### T-117
**Task**: Implement performance cycle service and endpoints
**Description**: `POST /performance/cycles`, `GET /performance/cycles`, `GET /performance/cycles/{id}`. Validate: `end_date >= start_date`. Admin/HR only for create.
**Dependencies**: T-116
**Complexity**: S
**Done Criteria**:
- Cycle name unique enforced
- Date validation on create/update
- Returns `404` for unknown cycle

---

### T-118
**Task**: Implement performance review service
**Description**: `create_review(cycle_id, employee_id, reviewer_id, rating, comments)`. Validate: `rating` between 1 and 5, both employee and reviewer must exist, cycle must exist.
**Dependencies**: T-116
**Complexity**: M
**Done Criteria**:
- Duplicate review (same cycle + employee + reviewer) returns `409`
- Rating validation: 1.00–5.00
- Audit log written on create

---

### T-119
**Task**: Implement performance metrics endpoints
**Description**: CRUD for `performance_metrics`. `GET /performance/metrics` accessible to all. Create/update/delete Admin/HR only.
**Dependencies**: T-116
**Complexity**: S
**Done Criteria**:
- Metric name max 150 chars
- Delete blocked if metric has scores

---

### T-120
**Task**: Implement metric score endpoints
**Description**: `POST /performance/reviews/{review_id}/scores`, `GET /performance/reviews/{review_id}/scores`. Add and list metric scores for a review.
**Dependencies**: T-116
**Complexity**: S
**Done Criteria**:
- `score` validated: 0–100
- `metric_id` must reference existing metric
- Returns all scores for the review

---

### T-121
**Task**: Implement performance feedback endpoints
**Description**: `POST /performance/reviews/{review_id}/feedback`, `GET /performance/reviews/{review_id}/feedback`. Create and list feedback entries.
**Dependencies**: T-116
**Complexity**: S
**Done Criteria**:
- `feedback_text` required, max 5000 chars
- `created_by` from authenticated user's employee record
- List sorted by `created_at` descending

---

### T-122
**Task**: Implement employee performance view
**Description**: `GET /performance/my-reviews`. Returns the authenticated employee's reviews across all cycles. Includes scores and feedback.
**Dependencies**: T-116
**Complexity**: S
**Done Criteria**:
- Employee sees only own reviews
- Ordered by cycle descending
- Includes average metric score per review

---

### T-123
**Task**: Implement manager performance view
**Description**: `GET /performance/team`. Returns performance reviews for all employees reporting to the authenticated manager.
**Dependencies**: T-116, T-040
**Complexity**: M
**Done Criteria**:
- Filters by manager's direct reports
- Supports `cycle_id` filter
- Includes employee name, rating, average score

---

### T-124
**Task**: Implement historical performance view
**Description**: `GET /performance/employees/{employee_id}/history`. Returns all reviews for an employee across all cycles. HR and Admin only (or the employee themselves).
**Dependencies**: T-116
**Complexity**: S
**Done Criteria**:
- Sorted by cycle start date descending
- Includes cycle name, reviewer name, rating, scores, feedback count

---

### T-125
**Task**: Implement performance Pydantic schemas
**Description**: `CycleRequest`, `CycleResponse`, `ReviewRequest`, `ReviewResponse`, `MetricScoreRequest`, `MetricScoreResponse`, `FeedbackRequest`, `FeedbackResponse`, `EmployeePerformanceSummary`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- `rating` typed as `float` with range annotation
- `score` typed as `float` 0–100
- Nested objects for cycle, reviewer, employee in responses

---

### T-126
**Task**: Implement performance report endpoint
**Description**: `GET /api/v1/reports/performance`. Filters: `cycle_id`, `department_id`, `date_from`, `date_to`. Returns: average rating per department, top performers (rating ≥ 4.0), score distribution.
**Dependencies**: T-116
**Complexity**: M
**Done Criteria**:
- Aggregations computed in SQL
- Returns both summary stats and paginated employee list
- HR Manager/Admin access

---

### T-127
**Task**: Wire performance routes
**Description**: Register all performance routes under `/api/v1/performance`.
**Dependencies**: T-117 – T-126
**Complexity**: S
**Done Criteria**:
- All routes in OpenAPI docs
- RBAC enforced per authorization matrix

---

### T-128
**Task**: Implement performance audit logging
**Description**: Log create review, update scores, and add feedback to `audit_logs`.
**Dependencies**: T-018, T-118
**Complexity**: XS
**Done Criteria**:
- `resource_type = "performance_reviews"`

---

---

## E12 — Core Backend: Notifications Module

### T-129
**Task**: Implement notification repository and service
**Description**: `create_notification(user_id, title, message)`, `list_notifications(user_id, is_read, page, page_size)`, `mark_read(notification_id, user_id)`, `mark_all_read(user_id)`, `get_unread_count(user_id)`, `get_preferences(user_id)`, `update_preferences(user_id, in_app_enabled)`.
**Dependencies**: T-018
**Complexity**: M
**Done Criteria**:
- `list_notifications` uses `idx_notifications_user` index
- `mark_read` validates notification belongs to user
- `get_unread_count` returns integer, not list

---

### T-130
**Task**: Implement notification Pydantic schemas
**Description**: `NotificationResponse`, `NotificationListResponse`, `NotificationPreferenceResponse`, `UpdatePreferenceRequest`, `UnreadCountResponse`.
**Dependencies**: T-007
**Complexity**: XS
**Done Criteria**:
- `is_read`, `created_at` always included
- Preference includes `in_app_enabled`

---

### T-131
**Task**: Wire notification routes
**Description**: Under `/api/v1/notifications`: `GET /`, `GET /{id}`, `PATCH /{id}/read`, `POST /read-all`, `GET /count`, `GET /preferences`, `PATCH /preferences`. User sees only own notifications.
**Dependencies**: T-129, T-130
**Complexity**: S
**Done Criteria**:
- Accessing another user's notification returns `403`
- `GET /count` returns `{"unread_count": N}`

---

### T-132
**Task**: Implement notification triggers — leave events
**Description**: In leave service, after approve/reject/cancel, call `create_notification()` for the requesting employee. Message includes leave type, dates, and decision.
**Dependencies**: T-129, T-076, T-077
**Complexity**: S
**Done Criteria**:
- Employee receives notification on approval, rejection, and cancellation
- Notification `title` and `message` are descriptive

---

### T-133
**Task**: Implement notification triggers — recruitment events
**Description**: In recruitment service, trigger notifications: candidate status change (to recruiter), interview scheduled (to interviewer).
**Dependencies**: T-129, T-091, T-098
**Complexity**: S
**Done Criteria**:
- Recruiter notified on candidate status changes
- Interviewer notified when interview scheduled for them

---

### T-134
**Task**: Implement notification triggers — attendance corrections
**Description**: When a correction request is created, notify HR Manager. When reviewed, notify the requesting employee.
**Dependencies**: T-129, T-068, T-069
**Complexity**: S
**Done Criteria**:
- Notifications created for correct recipients
- Message includes correction status

---

### T-135
**Task**: Implement notification triggers — performance reviews
**Description**: When a performance review is created for an employee, notify that employee.
**Dependencies**: T-129, T-118
**Complexity**: XS
**Done Criteria**:
- Employee receives notification with cycle name and reviewer name

---

---

## E13 — Core Backend: Dashboard APIs

### T-136
**Task**: Implement HR Dashboard endpoint
**Description**: `GET /api/v1/dashboard/hr`. Returns: total employees, active employees, new hires (last 30 days), departments count, attendance rate (today), pending leave requests count, open job postings, candidates this month. HR Manager/Admin only.
**Dependencies**: T-040, T-062, T-074, T-086, T-090
**Complexity**: L
**Done Criteria**:
- All KPIs computed in single optimized query or minimal queries
- Returns consistent snapshot
- Response time target: < 3 seconds

---

### T-137
**Task**: Implement Recruitment Dashboard endpoint
**Description**: `GET /api/v1/dashboard/recruitment`. Returns: open jobs, total candidates, shortlisted candidates, rejected, pending screening, average AI score, top candidates per job. Recruiter/HR/Admin.
**Dependencies**: T-086, T-090
**Complexity**: M
**Done Criteria**:
- Per-job breakdown included
- Average score across all active candidates

---

### T-138
**Task**: Implement Attendance Dashboard endpoint
**Description**: `GET /api/v1/dashboard/attendance`. Returns: today's present/absent/late counts, attendance rate %, weekly trend (7 days), top absent departments. HR/Admin.
**Dependencies**: T-062
**Complexity**: M
**Done Criteria**:
- Weekly trend is array of `{date, present_count, absent_count}`
- Today's stats reflect current-day records

---

### T-139
**Task**: Implement Performance Dashboard endpoint
**Description**: `GET /api/v1/dashboard/performance`. Returns: active cycle name, average rating, top performers (rating ≥ 4), employees not yet reviewed in current cycle. HR/Admin.
**Dependencies**: T-116
**Complexity**: M
**Done Criteria**:
- "Not yet reviewed" uses current active cycle
- Returns `null` if no active cycle

---

### T-140
**Task**: Implement Employee Dashboard endpoint
**Description**: `GET /api/v1/dashboard/employee`. Returns: own attendance this month (present days, total hours), leave balance summary, latest performance rating, unread notifications count. Employee-scoped.
**Dependencies**: T-062, T-074, T-116, T-129
**Complexity**: M
**Done Criteria**:
- All data scoped to authenticated employee
- Returns `null` for missing data (no review yet, etc.)
- Target: < 2 second response

---

### T-141
**Task**: Implement dashboard Pydantic schemas
**Description**: `HRDashboardResponse`, `RecruitmentDashboardResponse`, `AttendanceDashboardResponse`, `PerformanceDashboardResponse`, `EmployeeDashboardResponse`.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- All KPI fields named exactly as per API.md spec
- Nullable fields annotated

---

---

## E14 — Core Backend: Reporting & Export

### T-142
**Task**: Implement employee report endpoint
**Description**: `GET /api/v1/reports/employees`. Filters: `department_id`, `designation_id`, `employment_status_id`, `date_from` (join_date), `sort_by`, `sort_order`. Paginated. HR/Admin only.
**Dependencies**: T-040
**Complexity**: M
**Done Criteria**:
- All filters functional
- Includes employee code, name, department, designation, status, join date
- Pagination envelope returned

---

### T-143
**Task**: Implement attendance report endpoint
**Description**: `GET /api/v1/reports/attendance`. Filters: `employee_id`, `department_id`, `date_from`, `date_to`, `status`. Returns per-employee daily attendance rows.
**Dependencies**: T-062
**Complexity**: M
**Done Criteria**:
- Joins employees and departments
- Paginated
- HR/Admin only

---

### T-144
**Task**: Implement CSV export utility
**Description**: In `backend/app/core/export.py`, implement `generate_csv(headers: list, rows: list) -> StreamingResponse`. Return as `text/csv` with `Content-Disposition: attachment`.
**Dependencies**: T-004
**Complexity**: S
**Done Criteria**:
- Headers row included
- Handles empty data sets
- Streaming (not in-memory buffered) for large datasets

---

### T-145
**Task**: Implement CSV export endpoints
**Description**: `GET /api/v1/reports/employees/export`, `GET /api/v1/reports/attendance/export`, `GET /api/v1/reports/recruitment/export`. Same filters as report endpoints. Return CSV file.
**Dependencies**: T-142, T-143, T-104, T-144
**Complexity**: M
**Done Criteria**:
- Filename includes report type and date: `employees_2025-01-15.csv`
- All data rows exported (not paginated)
- HR/Admin only

---

### T-146
**Task**: Implement performance report endpoint
**Description**: Already defined in T-126. Add export: `GET /api/v1/reports/performance/export`.
**Dependencies**: T-126, T-144
**Complexity**: S
**Done Criteria**:
- CSV includes: employee name, cycle, rating, average score, department
- Same filters as performance report

---

### T-147
**Task**: Implement pagination utility
**Description**: In `backend/app/core/pagination.py`, implement `paginate(query, page, page_size) -> PaginatedResult`. Computes `total_items`, `total_pages`, applies LIMIT/OFFSET.
**Dependencies**: T-007
**Complexity**: S
**Done Criteria**:
- Works with any SQLAlchemy async query
- `page_size` capped at 100
- `page` minimum 1

---

### T-148
**Task**: Implement sorting utility
**Description**: In `backend/app/core/sorting.py`, implement `apply_sorting(query, model, sort_by, sort_order)`. Validates `sort_by` against model columns (whitelist). Defaults to `created_at DESC`.
**Dependencies**: T-005
**Complexity**: S
**Done Criteria**:
- Invalid `sort_by` returns `400`
- `sort_order` accepts `asc` and `desc` only
- Case-insensitive sort_order

---

### T-149
**Task**: Implement filtering utility
**Description**: In `backend/app/core/filtering.py`, implement generic filter applier. Handles: `search` (ILIKE on specified columns), date range (`date_from`, `date_to`), exact match filters.
**Dependencies**: T-005
**Complexity**: S
**Done Criteria**:
- Reusable across all list endpoints
- `search` is case-insensitive
- Ignores `None` filter values (partial filtering)

---

### T-150
**Task**: Wire all report routes
**Description**: Register all report endpoints under `/api/v1/reports`.
**Dependencies**: T-142 – T-149
**Complexity**: XS
**Done Criteria**:
- All endpoints in OpenAPI docs
- RBAC enforced (HR/Admin for all reports)

---

---

## E15 — Core Backend: Audit Log Module

### T-151
**Task**: Implement audit log repository
**Description**: `list_audit_logs` (paginated), `get_audit_log_by_id`, `get_user_activity(user_id)`, `get_resource_activity(resource_type, resource_id)`.
**Dependencies**: T-018
**Complexity**: M
**Done Criteria**:
- `list_audit_logs` supports: `actor_user_id`, `action`, `resource_type`, `date_from`, `date_to`
- Uses `idx_audit_created`, `idx_audit_actor` indexes
- Sorted by `created_at DESC` by default

---

### T-152
**Task**: Implement audit log service and schemas
**Description**: Thin service layer wrapping repository. `AuditLogResponse` schema: `id`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `created_at`.
**Dependencies**: T-151
**Complexity**: S
**Done Criteria**:
- `before_state` and `after_state` returned as JSON objects
- System Admin only access

---

### T-153
**Task**: Wire audit log routes
**Description**: Under `/api/v1/audit-logs`: `GET /`, `GET /{id}`, `GET /users/{user_id}/activity`, `GET /resources/{resource_type}/{resource_id}`. System Admin only.
**Dependencies**: T-151, T-152
**Complexity**: S
**Done Criteria**:
- Non-admin returns `403`
- All filter parameters documented

---

### T-154
**Task**: Implement centralized audit log writer
**Description**: In `backend/app/core/audit.py`, implement `write_audit_log(db, actor_user_id, action, resource_type, resource_id, before_state, after_state, ip_address)`. Used by all services.
**Dependencies**: T-018
**Complexity**: S
**Done Criteria**:
- Non-blocking: failures don't break the parent transaction
- All fields optional except `action` and `resource_type`
- Used consistently across all modules

---

### T-155
**Task**: Implement audit log date range search
**Description**: `GET /audit-logs?date_from=&date_to=`. Filter by `created_at` range.
**Dependencies**: T-151
**Complexity**: XS
**Done Criteria**:
- Both dates inclusive
- ISO 8601 date format accepted

---

### T-156
**Task**: Implement audit log full-text search
**Description**: `GET /audit-logs?search=` — searches across `action`, `resource_type` fields using ILIKE.
**Dependencies**: T-151
**Complexity**: XS
**Done Criteria**:
- Case-insensitive search
- Returns matching logs paginated

---

---

## E16 — Frontend: Project Setup

### T-157
**Task**: Configure Axios API client
**Description**: In `frontend/src/services/api.ts`, create Axios instance with base URL `/api/v1`. Add request interceptor to attach `Authorization: Bearer <token>` from localStorage. Add response interceptor for 401 → trigger token refresh, 403 → redirect, 500 → global error toast.
**Dependencies**: T-012, T-029
**Complexity**: M
**Done Criteria**:
- Token attached automatically on every request
- 401 triggers refresh flow (calls `/auth/refresh`, retries original request)
- Refresh failure redirects to `/login`

---

### T-158
**Task**: Implement auth context and provider
**Description**: In `frontend/src/providers/AuthProvider.tsx`, implement React context with: `user`, `isAuthenticated`, `login()`, `logout()`, `refreshToken()`. Persist tokens in `localStorage`. Restore session on page load.
**Dependencies**: T-157
**Complexity**: M
**Done Criteria**:
- Session persists across page refresh
- `logout()` clears tokens and redirects to `/login`
- `isAuthenticated` is `false` until tokens validated

---

### T-159
**Task**: Implement TanStack Query provider and configuration
**Description**: Wrap app in `QueryClientProvider`. Configure: `staleTime: 30s`, `retry: 1`, global error handler. Create `useQuery` and `useMutation` wrappers for typed API calls.
**Dependencies**: T-157
**Complexity**: S
**Done Criteria**:
- QueryClient configured in `providers/QueryProvider.tsx`
- Default error handler shows toast on 500 errors

---

### T-160
**Task**: Implement route protection (middleware)
**Description**: In Next.js `middleware.ts`, redirect unauthenticated users from protected routes to `/login`. Implement role-based route guards: HR routes inaccessible to Employee role.
**Dependencies**: T-158
**Complexity**: M
**Done Criteria**:
- Unauthenticated → redirect to `/login`
- Wrong role → redirect to `/unauthorized`
- Public routes (`/login`, `/forgot-password`) always accessible

---

### T-161
**Task**: Create shared UI components library
**Description**: Build reusable components in `frontend/src/components/`: `DataTable` (with pagination, sort, filter), `PageHeader`, `StatCard`, `LoadingSpinner`, `EmptyState`, `ConfirmDialog`, `FormField`, `StatusBadge`.
**Dependencies**: T-012
**Complexity**: M
**Done Criteria**:
- `DataTable` accepts columns config and data prop
- `StatCard` accepts label, value, trend, icon
- All components use shadcn/ui primitives
- Storybook-ready (props documented)

---

### T-162
**Task**: Implement toast/notification system
**Description**: Configure shadcn/ui `Toaster`. Implement `useToast()` hook with: `success()`, `error()`, `info()` methods. Wire to Axios response interceptor.
**Dependencies**: T-159
**Complexity**: XS
**Done Criteria**:
- Success mutations show green toast
- API errors show red toast with message from error envelope
- Toast auto-dismisses after 5 seconds

---

### T-163
**Task**: Create app layout components
**Description**: Implement: `Sidebar` (role-aware navigation links), `TopBar` (user menu, notifications bell), `MainLayout` (wraps all protected pages). Navigation items differ per role.
**Dependencies**: T-160, T-161
**Complexity**: M
**Done Criteria**:
- Sidebar shows correct items for each role
- Notifications bell shows unread count badge
- Mobile-responsive sidebar (collapsible)

---

### T-164
**Task**: Implement Zod validation schemas (shared)
**Description**: In `frontend/src/lib/validations/`, create Zod schemas matching API.md request bodies: `loginSchema`, `createEmployeeSchema`, `leaveRequestSchema`, `createJobSchema`, etc.
**Dependencies**: T-012
**Complexity**: M
**Done Criteria**:
- All schemas match API.md validation rules
- Email regex, min/max lengths, enum values enforced
- Schemas shared between form and API call

---

### T-165
**Task**: Create TypeScript type definitions
**Description**: In `frontend/src/types/`, define types for all API response objects: `User`, `Employee`, `Job`, `Candidate`, `AttendanceRecord`, `LeaveRequest`, `PerformanceReview`, `Notification`, `AuditLog`, `PaginatedResponse<T>`.
**Dependencies**: T-012
**Complexity**: S
**Done Criteria**:
- All types match API.md response schemas exactly
- `PaginatedResponse<T>` is generic
- No `any` types

---

---

## E17 — Frontend: Auth Pages

### T-166
**Task**: Implement Login page
**Description**: `/login` — email + password form. Calls `POST /auth/login`. On success: store tokens, redirect to role-appropriate dashboard. Show error on failure.
**Dependencies**: T-157, T-158, T-164
**Complexity**: S
**Done Criteria**:
- Form validates before submission
- Loading state shown during API call
- Error message displayed on invalid credentials
- Redirects HR to `/hr/dashboard`, Employee to `/employee/dashboard`

---

### T-167
**Task**: Implement Forgot Password page
**Description**: `/forgot-password` — email input. Calls `POST /auth/forgot-password`. Always shows success message (security).
**Dependencies**: T-157
**Complexity**: S
**Done Criteria**:
- Shows "If this email exists, you'll receive instructions" on submit
- Form validated before submission

---

### T-168
**Task**: Implement Reset Password page
**Description**: `/reset-password?token=` — new password + confirm. Calls `POST /auth/reset-password`. Redirects to login on success.
**Dependencies**: T-157
**Complexity**: S
**Done Criteria**:
- Token extracted from query params
- Password confirmation validated client-side
- Expired token error shown

---

### T-169
**Task**: Implement service functions for auth API
**Description**: In `frontend/src/services/auth.service.ts`, create typed functions: `login()`, `logout()`, `refreshToken()`, `forgotPassword()`, `resetPassword()`, `getMe()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions return typed responses
- Error handling uses standard error envelope

---

### T-170
**Task**: Implement useAuth hook
**Description**: `frontend/src/hooks/useAuth.ts` — wraps auth context. Exposes: `user`, `isAuthenticated`, `login()`, `logout()`, `isLoading`, `hasRole(role)`.
**Dependencies**: T-158
**Complexity**: S
**Done Criteria**:
- `hasRole()` returns boolean
- `isLoading` true during initial session restore
- Used across all role-gated components

---

### T-171
**Task**: Implement unauthorized page
**Description**: `/unauthorized` — simple page shown when user accesses a route without required role. Link back to dashboard.
**Dependencies**: T-160
**Complexity**: XS
**Done Criteria**:
- Clear message explaining access denied
- Role-appropriate dashboard link shown

---

### T-172
**Task**: Implement user profile menu
**Description**: Top-right avatar dropdown: shows user name and email, link to profile, logout button. Calls `POST /auth/logout` on click.
**Dependencies**: T-163, T-170
**Complexity**: S
**Done Criteria**:
- Displays current user name and role
- Logout clears auth state and redirects
- Accessible via keyboard

---

---

## E18 — Frontend: Employee Management

### T-173
**Task**: Implement employee service functions
**Description**: `frontend/src/services/employee.service.ts`: `listEmployees()`, `getEmployee()`, `createEmployee()`, `updateEmployee()`, `deactivateEmployee()`, `searchEmployees()`, `getEmployeeProfile()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions typed with `Employee` type
- Filter params typed

---

### T-174
**Task**: Implement employee list page
**Description**: `/hr/employees` — DataTable of employees. Filters: search, department, designation, status. Pagination. Row click → employee detail. "Add Employee" button (HR only).
**Dependencies**: T-161, T-173
**Complexity**: M
**Done Criteria**:
- Table shows: name, code, department, designation, status, join date
- Filters update URL params
- Pagination works

---

### T-175
**Task**: Implement employee detail page
**Description**: `/hr/employees/{id}` — full employee profile. Tabs: Profile, Attendance, Leave, Performance. Edit and Deactivate buttons (HR only).
**Dependencies**: T-173
**Complexity**: M
**Done Criteria**:
- Profile tab shows all employee fields
- Edit button opens edit form (inline or modal)
- Deactivate shows confirmation dialog

---

### T-176
**Task**: Implement create employee form
**Description**: Modal or page form. Fields: first_name, last_name, email, phone, employee_code, department (dropdown), designation (dropdown), employment_status (dropdown), manager (search), salary, join_date.
**Dependencies**: T-161, T-164, T-173
**Complexity**: M
**Done Criteria**:
- All dropdowns populated from API
- Manager search uses employee search endpoint
- Validation errors shown per field
- Success closes modal and refreshes list

---

### T-177
**Task**: Implement edit employee form
**Description**: Pre-populated form for updating employee. Same fields as create. Salary field hidden from non-HR roles.
**Dependencies**: T-176
**Complexity**: S
**Done Criteria**:
- Form pre-fills with current values
- Only changed fields submitted
- Salary visible to HR/Admin only

---

### T-178
**Task**: Implement department management page
**Description**: `/admin/departments` — list, create, edit, delete departments. Inline edit. Confirm deletion (with warning if employees assigned).
**Dependencies**: T-161
**Complexity**: M
**Done Criteria**:
- Delete shows employee count warning
- 409 error shown if deletion blocked
- Admin and HR access

---

### T-179
**Task**: Implement designation management page
**Description**: `/admin/designations` — mirrors department management page.
**Dependencies**: T-161
**Complexity**: S
**Done Criteria**:
- Same pattern as T-178
- Unique title enforced client-side

---

### T-180
**Task**: Implement employee search component
**Description**: Reusable `EmployeeSearch` component. Autocomplete input that calls `GET /employees/search?q=`. Used in: manager field, interview interviewer field, etc.
**Dependencies**: T-173, T-161
**Complexity**: M
**Done Criteria**:
- Debounced input (300ms)
- Shows name, code, department in dropdown
- Returns selected employee ID to parent

---

### T-181
**Task**: Implement employee service functions (hooks)
**Description**: `useEmployees()`, `useEmployee(id)`, `useCreateEmployee()`, `useUpdateEmployee()`, `useDeactivateEmployee()` — TanStack Query hooks.
**Dependencies**: T-159, T-173
**Complexity**: S
**Done Criteria**:
- Mutations invalidate employee list cache
- Loading and error states exposed

---

### T-182
**Task**: Implement employee report view
**Description**: `/hr/reports/employees` — filterable employee table with "Export CSV" button.
**Dependencies**: T-173, T-161
**Complexity**: M
**Done Criteria**:
- All filters functional
- CSV download triggers file save
- HR/Admin access only

---

---

## E19 — Frontend: Recruitment

### T-183
**Task**: Implement job service functions and hooks
**Description**: `job.service.ts` + TanStack Query hooks: `useJobs()`, `useJob(id)`, `useCreateJob()`, `usePublishJob()`, `useCloseJob()`, `useDeleteJob()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions typed
- Status mutations invalidate job cache

---

### T-184
**Task**: Implement job list page
**Description**: `/recruiter/jobs` — cards or table of jobs. Filter by status. Status badges (draft/published/closed). "Create Job" button.
**Dependencies**: T-161, T-183
**Complexity**: M
**Done Criteria**:
- Status filter tabs (All / Draft / Published / Closed)
- Each card shows title, department, status, candidate count, date
- Publish/Close actions in row menu

---

### T-185
**Task**: Implement job detail page
**Description**: `/recruiter/jobs/{id}` — job info, skills list, candidate count, action buttons (Publish/Close). Tab: Candidates.
**Dependencies**: T-183
**Complexity**: M
**Done Criteria**:
- Skills displayed as tags
- Status transition buttons show based on current status
- Candidates tab links to filtered candidate list

---

### T-186
**Task**: Implement create/edit job form
**Description**: Form with: title, department, description (textarea), skills (tag input), status. Validation per API.md.
**Dependencies**: T-164, T-183
**Complexity**: M
**Done Criteria**:
- Skills input allows adding/removing tags
- Description min 10 chars
- Department from dropdown

---

### T-187
**Task**: Implement candidate service functions and hooks
**Description**: `candidate.service.ts` + hooks: `useCandidates(jobId)`, `useCandidate(id)`, `useCreateCandidate()`, `useUpdateCandidateStatus()`, `useShortlistCandidate()`, `useRejectCandidate()`, `useOverrideAI()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions typed
- Status mutations invalidate candidate list cache

---

### T-188
**Task**: Implement candidate list page
**Description**: `/recruiter/jobs/{jobId}/candidates` — table sorted by AI score. Columns: name, email, AI score, ranking, recommendation, status. Filters: status.
**Dependencies**: T-161, T-187
**Complexity**: M
**Done Criteria**:
- AI score shown as progress bar
- Recommendation badge (Shortlist/Review/Reject)
- Row actions: View, Shortlist, Reject, Override

---

### T-189
**Task**: Implement candidate detail page
**Description**: `/recruiter/candidates/{id}` — profile, resume analysis results, status timeline, notes, interview list.
**Dependencies**: T-187, T-161
**Complexity**: L
**Done Criteria**:
- Skills shown as matched (green) and missing (red) tags
- Timeline shows full status history with timestamps
- Notes list with add note form

---

### T-190
**Task**: Implement resume upload component
**Description**: Drag-and-drop file upload. Accepts PDF/DOCX. Shows upload progress. After upload, shows "Run AI Screening" button.
**Dependencies**: T-187
**Complexity**: M
**Done Criteria**:
- File type validated client-side
- Max 10MB validated client-side
- Progress shown during upload
- "Analyze" button triggers AI screening

---

### T-191
**Task**: Implement AI analysis results display
**Description**: In candidate detail, show analysis card: score gauge, matched skills (green chips), missing skills (red chips), recommendation badge, explanation text.
**Dependencies**: T-189
**Complexity**: M
**Done Criteria**:
- Score displayed as circular gauge (0–100)
- Skills shown as color-coded chips
- "Override AI Decision" button visible to Recruiter

---

### T-192
**Task**: Implement candidate ranking view
**Description**: `/recruiter/jobs/{jobId}/ranking` — ranked table of candidates. Position number, name, score, matched skills count, recommendation. Actions: Shortlist, Reject.
**Dependencies**: T-187, T-161
**Complexity**: M
**Done Criteria**:
- Ranked 1→N by AI score
- Manually overridden candidates flagged with icon
- Bulk shortlist selected candidates

---

### T-193
**Task**: Implement candidate notes component
**Description**: Notes section in candidate detail. Textarea + submit. List of notes with author and timestamp.
**Dependencies**: T-187
**Complexity**: S
**Done Criteria**:
- Notes load with candidate detail
- New note appends to list optimistically
- Recruiter/HR access

---

### T-194
**Task**: Implement interview scheduling form
**Description**: Modal form: select candidate application, date/time picker, select interviewer (EmployeeSearch), notes. Calls `POST /interviews`.
**Dependencies**: T-180, T-183
**Complexity**: M
**Done Criteria**:
- Date/time must be in future (validated)
- Interviewer search functional
- Success notification sent

---

### T-195
**Task**: Implement interview list view
**Description**: `/recruiter/interviews` — table of upcoming and past interviews. Status badges. Update status action.
**Dependencies**: T-194
**Complexity**: M
**Done Criteria**:
- Filter by status (scheduled/completed/cancelled)
- Update status inline

---

### T-196
**Task**: Implement recruitment report view
**Description**: `/hr/reports/recruitment` — stats cards + candidate table. Export CSV.
**Dependencies**: T-187, T-161
**Complexity**: M
**Done Criteria**:
- Stats: total candidates, shortlisted %, average score
- Filterable by job, status, date range
- CSV export functional

---

---

## E20 — Frontend: Attendance

### T-197
**Task**: Implement attendance service functions and hooks
**Description**: `attendance.service.ts` + hooks: `useCheckIn()`, `useCheckOut()`, `useAttendanceHistory()`, `useMonthlySummary()`, `useDailyAttendance()`, `useCreateCorrection()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions typed
- Date parameters typed as `string` (ISO format)

---

### T-198
**Task**: Implement employee attendance page
**Description**: `/employee/attendance` — check-in/check-out button (toggle based on state), today's status, monthly summary card, history table.
**Dependencies**: T-197, T-161
**Complexity**: M
**Done Criteria**:
- Check-in button disabled after check-in, check-out shown
- Today's check-in/check-out times displayed
- Monthly summary: present days, total hours
- History table paginated

---

### T-199
**Task**: Implement attendance calendar view
**Description**: Monthly calendar showing attendance status per day. Color-coded: green (present), red (absent), yellow (late), grey (holiday/weekend).
**Dependencies**: T-197
**Complexity**: M
**Done Criteria**:
- Month navigation (prev/next)
- Clicking a day shows details
- Works for own records and HR view

---

### T-200
**Task**: Implement HR daily attendance view
**Description**: `/hr/attendance/daily` — table of all employees for a selected date. Status filter. Shows present/absent/late counts in header.
**Dependencies**: T-197, T-161
**Complexity**: M
**Done Criteria**:
- Date picker for selecting day
- Summary counts in header
- Searchable by employee name

---

### T-201
**Task**: Implement attendance correction flow
**Description**: In attendance detail, "Request Correction" button opens modal with reason textarea. Submits correction request.
**Dependencies**: T-197
**Complexity**: S
**Done Criteria**:
- Reason field required, min 10 chars
- Success notification shown
- Pending correction indicated on record

---

### T-202
**Task**: Implement correction review page (HR)
**Description**: `/hr/attendance/corrections` — list of pending corrections. Approve/Reject buttons with remarks input.
**Dependencies**: T-197, T-161
**Complexity**: M
**Done Criteria**:
- Pending corrections highlighted
- Approve/Reject with optional remarks
- Status updated in list after action

---

### T-203
**Task**: Implement attendance report view
**Description**: `/hr/reports/attendance` — filterable attendance table. Export CSV.
**Dependencies**: T-197, T-161
**Complexity**: M
**Done Criteria**:
- Filters: employee, department, date range, status
- CSV export functional

---

### T-204
**Task**: Implement monthly attendance summary (HR)
**Description**: `/hr/attendance/monthly` — select employee + month/year → summary card with daily breakdown table.
**Dependencies**: T-197, T-161
**Complexity**: M
**Done Criteria**:
- Employee dropdown (search)
- Month/year pickers
- Summary: present, absent, late, total hours

---

---

## E21 — Frontend: Leave Management

### T-205
**Task**: Implement leave service functions and hooks
**Description**: `leave.service.ts` + hooks: `useLeaveRequests()`, `useLeaveBalance()`, `useCreateLeaveRequest()`, `useApproveLeave()`, `useRejectLeave()`, `useCancelLeave()`, `usePendingApprovals()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions typed
- Mutations invalidate leave and balance cache

---

### T-206
**Task**: Implement employee leave page
**Description**: `/employee/leave` — leave balance cards (one per type), request history table, "Apply for Leave" button.
**Dependencies**: T-205, T-161
**Complexity**: M
**Done Criteria**:
- Balance cards show type, allocated, remaining
- History table: type, dates, status, reason
- Cancel action for pending requests

---

### T-207
**Task**: Implement leave request form
**Description**: Modal: leave type dropdown, start date, end date (with day count display), reason. Validates balance sufficient.
**Dependencies**: T-205, T-164
**Complexity**: M
**Done Criteria**:
- Day count calculated and shown as user selects dates
- Remaining balance shown for selected type
- Insufficient balance shown as warning before submit
- Weekends excluded from count (optional enhancement)

---

### T-208
**Task**: Implement leave approval page (HR/Manager)
**Description**: `/hr/leave/approvals` — table of pending leave requests. Approve/Reject with remarks.
**Dependencies**: T-205, T-161
**Complexity**: M
**Done Criteria**:
- Pending requests sorted by created date
- Approve/Reject opens dialog with remarks field
- List refreshes after action

---

### T-209
**Task**: Implement HR leave management page
**Description**: `/hr/leave` — all leave requests with filters: employee, status, leave type, date range.
**Dependencies**: T-205, T-161
**Complexity**: M
**Done Criteria**:
- All filters functional
- Status badges color-coded
- Pagination

---

### T-210
**Task**: Implement leave balance management (HR)
**Description**: `/hr/leave/balances` — view all employees' balances. Initialize balances for new year. Adjust individual balance.
**Dependencies**: T-205, T-161
**Complexity**: M
**Done Criteria**:
- Initialize button with confirmation dialog
- Per-employee balance table
- Manual adjustment form

---

### T-211
**Task**: Implement leave types management page
**Description**: `/admin/leave-types` — CRUD for leave types. Name, annual allocation.
**Dependencies**: T-161
**Complexity**: S
**Done Criteria**:
- Annual allocation must be positive integer
- Delete blocked if balances exist (409 shown)

---

### T-212
**Task**: Implement leave notification integration
**Description**: Show notification badge on `/employee/leave` when leave status changes. Clicking notification navigates to relevant request.
**Dependencies**: T-205
**Complexity**: S
**Done Criteria**:
- Unread count badge appears on leave nav item when relevant notification exists
- Notification links to leave detail

---

---

## E22 — Frontend: Performance

### T-213
**Task**: Implement performance service functions and hooks
**Description**: `performance.service.ts` + hooks: `useCycles()`, `useReviews()`, `useCreateReview()`, `useMetrics()`, `useMetricScores()`, `useFeedback()`, `useMyReviews()`, `useTeamPerformance()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- All functions typed
- Mutations invalidate review cache

---

### T-214
**Task**: Implement performance cycles management
**Description**: `/hr/performance/cycles` — list, create, view cycles. Form: name, start_date, end_date.
**Dependencies**: T-213, T-161
**Complexity**: S
**Done Criteria**:
- Active/past cycle distinction
- Date validation client-side

---

### T-215
**Task**: Implement performance review creation
**Description**: `/hr/performance/reviews/new` — select cycle, employee, fill rating (star or slider 1–5), comments, metric scores.
**Dependencies**: T-213, T-161, T-164
**Complexity**: M
**Done Criteria**:
- Cycle dropdown
- Employee search component
- Rating 1–5 with half-star or decimal
- All metrics listed with score inputs (0–100)

---

### T-216
**Task**: Implement employee performance view
**Description**: `/employee/performance` — own review history. Cards per cycle with rating, scores, feedback.
**Dependencies**: T-213, T-161
**Complexity**: M
**Done Criteria**:
- Rating displayed as star visual
- Metric scores as progress bars
- Feedback text expandable

---

### T-217
**Task**: Implement manager team performance view
**Description**: `/manager/performance/team` — table of direct reports with latest rating. Click → employee detail.
**Dependencies**: T-213, T-161
**Complexity**: M
**Done Criteria**:
- Sorted by rating descending by default
- Cycle filter
- Average team rating shown in header

---

### T-218
**Task**: Implement performance metrics management
**Description**: `/admin/performance/metrics` — CRUD list for performance metrics.
**Dependencies**: T-213, T-161
**Complexity**: S
**Done Criteria**:
- Name and description fields
- Delete blocked if scores exist

---

### T-219
**Task**: Implement performance history view
**Description**: `/hr/employees/{id}/performance` — full performance history for an employee. HR/Admin access.
**Dependencies**: T-213, T-161
**Complexity**: M
**Done Criteria**:
- Timeline of reviews across cycles
- Average rating trend line chart (Recharts)
- Each review expandable for scores and feedback

---

### T-220
**Task**: Implement performance report view
**Description**: `/hr/reports/performance` — stats: average rating, top performers, score distribution chart. Export CSV.
**Dependencies**: T-213, T-161
**Complexity**: M
**Done Criteria**:
- Bar chart: average rating per department
- Top performers table (rating ≥ 4)
- Cycle and department filters

---

### T-221
**Task**: Implement feedback form
**Description**: Inline feedback form on review detail. Text area + submit. Shows existing feedback list below.
**Dependencies**: T-213
**Complexity**: S
**Done Criteria**:
- Feedback text required, max 5000 chars
- Submitted feedback appears immediately
- Author and timestamp shown

---

---

## E23 — Frontend: Dashboards

### T-222
**Task**: Implement HR Dashboard page
**Description**: `/hr/dashboard` — KPI cards + charts. Cards: total employees, active, new hires, open jobs, pending leaves, today's attendance rate. Charts: attendance trend (7 days), department headcount.
**Dependencies**: T-163, T-161
**Complexity**: L
**Done Criteria**:
- All KPIs populated from `GET /dashboard/hr`
- Recharts line chart for attendance trend
- Recharts bar chart for department headcount
- Loading skeleton shown during fetch
- Auto-refresh every 60 seconds

---

### T-223
**Task**: Implement Recruitment Dashboard page
**Description**: `/recruiter/dashboard` — cards: open jobs, total candidates, shortlisted %, average AI score. Table: top candidates per job.
**Dependencies**: T-163, T-161
**Complexity**: M
**Done Criteria**:
- Data from `GET /dashboard/recruitment`
- Recharts donut chart: candidate status distribution
- Links to job detail from table rows

---

### T-224
**Task**: Implement Attendance Dashboard page
**Description**: `/hr/dashboard/attendance` — today's stats, weekly trend chart, department breakdown.
**Dependencies**: T-163, T-161
**Complexity**: M
**Done Criteria**:
- Recharts area chart: weekly attendance trend
- Today's present/absent/late counts as cards
- Department with highest absence highlighted

---

### T-225
**Task**: Implement Performance Dashboard page
**Description**: `/hr/dashboard/performance` — current cycle stats, average rating, top performers list, employees pending review.
**Dependencies**: T-163, T-161
**Complexity**: M
**Done Criteria**:
- Recharts bar chart: average rating by department
- Top performers list (rating ≥ 4)
- "No active cycle" state handled

---

### T-226
**Task**: Implement Employee Dashboard page
**Description**: `/employee/dashboard` — personal attendance summary, leave balance widget, latest performance rating card, recent notifications list.
**Dependencies**: T-163, T-161
**Complexity**: M
**Done Criteria**:
- Data from `GET /dashboard/employee`
- Check-in/check-out shortcut button
- Quick leave apply button
- All widgets handle empty state

---

### T-227
**Task**: Implement StatCard component
**Description**: Reusable KPI card component. Props: `title`, `value`, `subtitle`, `icon`, `trend` (up/down/neutral), `trendValue`.
**Dependencies**: T-161
**Complexity**: S
**Done Criteria**:
- Trend arrow with color (green up, red down)
- Skeleton variant for loading state
- Consistent size across all dashboards

---

### T-228
**Task**: Implement dashboard hooks
**Description**: `useHRDashboard()`, `useRecruitmentDashboard()`, `useAttendanceDashboard()`, `usePerformanceDashboard()`, `useEmployeeDashboard()` using TanStack Query with 60s refresh.
**Dependencies**: T-159
**Complexity**: S
**Done Criteria**:
- All hooks typed with response types
- `refetchInterval: 60000` configured
- Loading and error states exposed

---

---

## E24 — Frontend: Notifications

### T-229
**Task**: Implement notification service and hooks
**Description**: `notification.service.ts` + hooks: `useNotifications()`, `useUnreadCount()`, `useMarkRead()`, `useMarkAllRead()`, `useNotificationPreferences()`.
**Dependencies**: T-157, T-165
**Complexity**: S
**Done Criteria**:
- `useUnreadCount()` polls every 30 seconds
- Mark read invalidates both notification list and count cache

---

### T-230
**Task**: Implement notifications bell component
**Description**: Bell icon in TopBar showing unread badge. Click opens dropdown with last 5 notifications. "View all" link.
**Dependencies**: T-229, T-163
**Complexity**: M
**Done Criteria**:
- Badge hidden when count is 0
- Dropdown closes on outside click
- Each notification shows title, time ago, unread indicator

---

### T-231
**Task**: Implement notifications list page
**Description**: `/notifications` — full list, paginated. Mark all read button. Filter: read/unread.
**Dependencies**: T-229, T-161
**Complexity**: M
**Done Criteria**:
- Unread notifications have distinct background
- Clicking marks as read
- Mark all read updates entire list

---

### T-232
**Task**: Implement notification preferences page
**Description**: `/settings/notifications` — toggle: in-app notifications enabled/disabled.
**Dependencies**: T-229
**Complexity**: XS
**Done Criteria**:
- Toggle persists via API
- Immediate feedback on save

---

### T-233
**Task**: Implement notification polling
**Description**: Poll `GET /notifications/count` every 30 seconds when user is authenticated. Update bell badge without full page reload.
**Dependencies**: T-229, T-230
**Complexity**: S
**Done Criteria**:
- Polling stops when user logs out
- No unnecessary re-renders on same count
- Uses TanStack Query `refetchInterval`

---

---

## E25 — Frontend: Admin Pages

### T-234
**Task**: Implement user management page
**Description**: `/admin/users` — table of all users. Create, edit, deactivate. Assign/remove roles.
**Dependencies**: T-161
**Complexity**: M
**Done Criteria**:
- System Admin access only
- Role assignment as multi-select
- Deactivate with confirmation dialog

---

### T-235
**Task**: Implement create user form
**Description**: Modal: email, password, assign roles. Calls `POST /users`.
**Dependencies**: T-164, T-234
**Complexity**: S
**Done Criteria**:
- Role multi-select populated from roles list
- Password shown/hidden toggle
- Duplicate email error shown

---

### T-236
**Task**: Implement role management page
**Description**: `/admin/roles` — list of roles with permission count. View permissions per role.
**Dependencies**: T-161
**Complexity**: M
**Done Criteria**:
- List shows role name, description, permission count
- Click → role detail with permissions list
- Read-only for MVP (roles seeded, not UI-created)

---

### T-237
**Task**: Implement audit log viewer page
**Description**: `/admin/audit-logs` — filterable table of audit log entries. Filters: actor, action, resource type, date range.
**Dependencies**: T-161
**Complexity**: M
**Done Criteria**:
- Expandable rows showing `before_state` and `after_state` as JSON
- Date range picker
- Search by action or resource type
- System Admin only

---

### T-238
**Task**: Implement audit log detail view
**Description**: Expandable row or modal showing full audit log: actor, action, resource, IP, timestamp, before/after state diff.
**Dependencies**: T-237
**Complexity**: S
**Done Criteria**:
- JSON diff view for before/after states
- IP address displayed
- Actor linked to user profile

---

### T-239
**Task**: Implement system settings page stub
**Description**: `/admin/settings` — placeholder page with: environment info display (version), seed data re-run button (dev only).
**Dependencies**: T-163
**Complexity**: XS
**Done Criteria**:
- Page accessible to System Admin only
- Shows app version from env var

---

### T-240
**Task**: Implement admin navigation
**Description**: Sidebar section "Administration" visible only to System Administrator role. Links: Users, Roles, Audit Logs, Settings, Departments, Designations, Leave Types, Performance Metrics.
**Dependencies**: T-163, T-170
**Complexity**: S
**Done Criteria**:
- Section hidden for non-admin roles
- All links functional
- Active link highlighted

---

---

## E26 — Testing

### T-241
**Task**: Set up pytest configuration
**Description**: Configure `pytest` with `pytest-asyncio`, `httpx` (async test client), `pytest-cov`. Create `backend/tests/` with `conftest.py` providing: test database session, test client, mock authenticated user fixtures for each role.
**Dependencies**: T-010, T-029
**Complexity**: M
**Done Criteria**:
- `pytest` runs without error on empty test suite
- Test database is separate from development database
- `conftest.py` provides `hr_manager_token`, `employee_token`, `admin_token` fixtures

---

### T-242
**Task**: Write auth module tests
**Description**: Unit and integration tests for: login success, login wrong password, login inactive user, token refresh, token expiry, forgot password, reset password.
**Dependencies**: T-241, T-029
**Complexity**: M
**Done Criteria**:
- 100% branch coverage for auth service
- Tests for all error codes (401, 400, 404)

---

### T-243
**Task**: Write user/RBAC module tests
**Description**: Tests: create user, duplicate email, assign role, remove role, list users, RBAC enforcement (non-admin cannot create users).
**Dependencies**: T-241, T-039
**Complexity**: M
**Done Criteria**:
- 403 returned for unauthorized role access
- 409 returned for duplicate email

---

### T-244
**Task**: Write employee module tests
**Description**: Tests: create, list with filters, get, update, deactivate, search. Test salary visibility per role.
**Dependencies**: T-241, T-053
**Complexity**: M
**Done Criteria**:
- Employee cannot see other employees
- Employee cannot see salary
- HR Manager can list all employees

---

### T-245
**Task**: Write attendance module tests
**Description**: Tests: check-in, duplicate check-in, check-out, check-out without check-in, monthly summary, corrections flow.
**Dependencies**: T-241, T-071
**Complexity**: M
**Done Criteria**:
- Work duration computed correctly
- 409 on duplicate check-in
- Correction status transitions tested

---

### T-246
**Task**: Write leave module tests
**Description**: Tests: create request, insufficient balance, overlapping dates, approve, reject, cancel, balance deduction, balance restore on cancel.
**Dependencies**: T-241, T-082
**Complexity**: M
**Done Criteria**:
- Balance correctly deducted on approval
- Balance correctly restored on cancel of approved leave
- All status transitions tested

---

### T-247
**Task**: Write recruitment module tests
**Description**: Tests: job CRUD, status transitions (draft→published→closed), candidate create, application, status update, resume upload, manual override.
**Dependencies**: T-241, T-103
**Complexity**: M
**Done Criteria**:
- Invalid status transitions return 400
- Recruiter cannot manage jobs (HR Manager can)
- Resume upload validates file type

---

### T-248
**Task**: Write AI screening unit tests
**Description**: Unit tests for: `extract_text()` (PDF + DOCX), `extract_skills()`, `compute_match()`, `generate_recommendation()`. Use sample fixture files.
**Dependencies**: T-241, T-106 – T-110
**Complexity**: M
**Done Criteria**:
- Parser handles malformed files gracefully
- Matcher returns score 0–100
- Recommendation thresholds correct at boundaries (39, 40, 69, 70)

---

### T-249
**Task**: Write performance module tests
**Description**: Tests: cycle CRUD, review creation, duplicate review, metric scores, feedback, rating boundary (1–5).
**Dependencies**: T-241, T-127
**Complexity**: M
**Done Criteria**:
- Rating < 1 or > 5 returns 422
- Score < 0 or > 100 returns 422
- Duplicate review (same cycle/employee/reviewer) returns 409

---

### T-250
**Task**: Write notification module tests
**Description**: Tests: create, list, mark read, mark all read, unread count, preferences.
**Dependencies**: T-241, T-131
**Complexity**: S
**Done Criteria**:
- User cannot read another user's notifications
- Unread count decrements on mark read

---

### T-251
**Task**: Write dashboard API tests
**Description**: Integration tests for all 5 dashboard endpoints. Validate returned KPI field names and types.
**Dependencies**: T-241, T-141
**Complexity**: M
**Done Criteria**:
- All KPI fields present in response
- Role restrictions enforced (employee cannot access HR dashboard)

---

### T-252
**Task**: Write reporting and export tests
**Description**: Tests: employee report filters, attendance report filters, CSV export (correct headers, correct row count).
**Dependencies**: T-241, T-150
**Complexity**: M
**Done Criteria**:
- CSV response has correct `Content-Type` header
- CSV row count matches report count

---

### T-253
**Task**: Write audit log module tests
**Description**: Tests: list, filter by date range, filter by actor, resource activity view. Admin-only access.
**Dependencies**: T-241, T-153
**Complexity**: S
**Done Criteria**:
- Non-admin receives 403
- Date range filter returns correct records

---

### T-254
**Task**: Set up frontend testing (Vitest + Testing Library)
**Description**: Configure Vitest and React Testing Library in `frontend/`. Create test utilities: render with providers (QueryClient, AuthProvider). Write smoke tests for Login page, AuthProvider.
**Dependencies**: T-166, T-170
**Complexity**: M
**Done Criteria**:
- `npm run test` runs all frontend tests
- Login form renders and submits correctly
- Auth context provides correct state

---

### T-255
**Task**: Compute test coverage and enforce threshold
**Description**: Configure `pytest-cov` with 80% minimum coverage threshold. Run in CI. Generate HTML coverage report.
**Dependencies**: T-241 – T-253
**Complexity**: S
**Done Criteria**:
- `pytest --cov=app --cov-fail-under=80` passes
- Coverage report generated to `backend/htmlcov/`

---

---

## E27 — DevOps & Deployment

### T-256
**Task**: Write Dockerfile — backend
**Description**: Multi-stage Dockerfile for FastAPI. Base: `python:3.12-slim`. Install dependencies, copy app, expose port 8000. Non-root user.
**Dependencies**: T-004
**Complexity**: S
**Done Criteria**:
- `docker build` succeeds
- Container starts and health endpoint responds
- No root user in container

---

### T-257
**Task**: Write Dockerfile — frontend
**Description**: Multi-stage Dockerfile for Next.js. Build stage + production stage. Expose port 3000.
**Dependencies**: T-012
**Complexity**: S
**Done Criteria**:
- `docker build` succeeds
- Built app serves at port 3000

---

### T-258
**Task**: Write docker-compose.yml (development)
**Description**: Services: `backend` (FastAPI), `frontend` (Next.js), `db` (PostgreSQL 16). Mount volumes for hot reload. Environment variables from `.env`.
**Dependencies**: T-256, T-257
**Complexity**: S
**Done Criteria**:
- `docker-compose up` starts all 3 services
- Backend connects to PostgreSQL
- Frontend connects to backend via service name

---

### T-259
**Task**: Write docker-compose.prod.yml
**Description**: Production compose: no volume mounts, `restart: always`, health checks on all services, `db` not exposed externally.
**Dependencies**: T-258
**Complexity**: S
**Done Criteria**:
- All services have `healthcheck` defined
- `db` port not bound to host
- Backend waits for `db` healthy before starting

---

### T-260
**Task**: Configure Nginx reverse proxy
**Description**: `infrastructure/nginx/nginx.conf`: proxy `/api/v1` to backend, all other paths to frontend. TLS termination stub. Security headers: `X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`.
**Dependencies**: T-258
**Complexity**: M
**Done Criteria**:
- Nginx routes correctly
- Security headers present on all responses
- Gzip compression enabled

---

### T-261
**Task**: Set up GitHub Actions CI pipeline
**Description**: `.github/workflows/ci.yml`: trigger on PR to `main`. Jobs: backend lint (`ruff`), backend tests (`pytest`), frontend lint (`eslint`), frontend type check (`tsc`), frontend build.
**Dependencies**: T-241, T-254
**Complexity**: M
**Done Criteria**:
- All jobs pass on clean code
- Failed tests block PR merge
- Coverage report published as PR comment

---

### T-262
**Task**: Set up GitHub Actions CD pipeline
**Description**: `.github/workflows/deploy.yml`: trigger on merge to `main`. Build Docker images, tag with commit SHA, push to registry, SSH deploy to server.
**Dependencies**: T-261
**Complexity**: M
**Done Criteria**:
- Images tagged and pushed to container registry
- Deploy script runs `docker-compose pull && docker-compose up -d`
- Rollback documented in README

---

### T-263
**Task**: Write database backup script
**Description**: `infrastructure/scripts/backup.sh`: runs `pg_dump`, compresses output, stores with timestamp. Designed for cron scheduling.
**Dependencies**: T-010
**Complexity**: S
**Done Criteria**:
- Script produces valid `.sql.gz` backup
- Restore tested with `pg_restore`
- Script documented in README

---

### T-264
**Task**: Write project README
**Description**: `README.md` at project root. Sections: overview, tech stack, local setup (docker-compose), environment variables, running migrations, seeding, running tests, deployment.
**Dependencies**: All previous tasks
**Complexity**: S
**Done Criteria**:
- New developer can run project locally following README alone
- All environment variables documented with examples
- Links to Architecture.md, PRD.md, API.md

---

## Task Summary

| Epic | Tasks | Total Tasks |
|------|-------|-------------|
| E1 — Scaffolding | T-001–T-012 | 12 |
| E2 — Database | T-013–T-018 | 6 |
| E3 — Auth Module | T-019–T-030 | 12 |
| E4 — User & RBAC | T-031–T-039 | 9 |
| E5 — Employee | T-040–T-053 | 14 |
| E6 — Dept & Designation | T-054–T-061 | 8 |
| E7 — Attendance | T-062–T-073 | 12 |
| E8 — Leave | T-074–T-085 | 12 |
| E9 — Recruitment | T-086–T-105 | 20 |
| E10 — AI Screening | T-106–T-115 | 10 |
| E11 — Performance | T-116–T-128 | 13 |
| E12 — Notifications | T-129–T-135 | 7 |
| E13 — Dashboard APIs | T-136–T-141 | 6 |
| E14 — Reporting | T-142–T-150 | 9 |
| E15 — Audit Logs | T-151–T-156 | 6 |
| E16 — Frontend Setup | T-157–T-165 | 9 |
| E17 — Auth Pages | T-166–T-172 | 7 |
| E18 — Employee UI | T-173–T-182 | 10 |
| E19 — Recruitment UI | T-183–T-196 | 14 |
| E20 — Attendance UI | T-197–T-204 | 8 |
| E21 — Leave UI | T-205–T-212 | 8 |
| E22 — Performance UI | T-213–T-221 | 9 |
| E23 — Dashboards | T-222–T-228 | 7 |
| E24 — Notifications UI | T-229–T-233 | 5 |
| E25 — Admin Pages | T-234–T-240 | 7 |
| E26 — Testing | T-241–T-255 | 15 |
| E27 — DevOps | T-256–T-264 | 9 |
| **Total** | | **264** |

---

## Dependency Graph (Critical Path)

```
T-001 (repo root)
  └── T-002 (backend init)
        ├── T-003 (module skeleton)
        │     └── T-004 (main.py)
        ├── T-005 (DB connection)
        │     ├── T-009 (Alembic init)
        │     │     └── T-010 (initial migration)
        │     │           └── T-011 (seed data)
        │     └── T-013–T-018 (ORM models)
        └── T-006 (config)
              └── T-008 (RBAC middleware)

T-008 + T-013 → T-019–T-030 (Auth Module)
T-013 + T-019 → T-031–T-039 (User Module)
T-014 + T-008 → T-040–T-053 (Employee Module)
T-014 → T-054–T-061 (Dept/Designation)
T-016 → T-062–T-073 (Attendance)
T-016 → T-074–T-085 (Leave)
T-015 → T-086–T-105 (Recruitment)
T-094 + T-106–T-110 → T-111–T-115 (AI Screening)
T-017 → T-116–T-128 (Performance)
T-018 → T-129–T-135 (Notifications)
T-040+T-062+T-074+T-086+T-116+T-129 → T-136–T-141 (Dashboards)
All backend → T-142–T-150 (Reporting)
T-018 → T-151–T-156 (Audit)

T-012 (frontend init)
  └── T-157–T-165 (frontend setup)
        └── T-166–T-172 (Auth Pages)
              └── E18–E25 (Feature Pages)
                    └── E23 (Dashboards — depends on all feature pages)

All → T-241–T-255 (Testing)
All → T-256–T-264 (DevOps)
```

---

## Suggested Sprint Order (2-week sprints)

| Sprint | Focus | Tasks |
|--------|-------|-------|
| 1 | Foundation | E1 (T-001–T-012) + E2 (T-013–T-018) |
| 2 | Auth + User | E3 (T-019–T-030) + E4 (T-031–T-039) |
| 3 | Employee + Org | E5 (T-040–T-053) + E6 (T-054–T-061) |
| 4 | Attendance + Leave | E7 (T-062–T-073) + E8 (T-074–T-085) |
| 5 | Recruitment Backend | E9 (T-086–T-105) |
| 6 | AI Screening + Performance | E10 (T-106–T-115) + E11 partial |
| 7 | Performance + Notifications | E11 complete + E12 (T-129–T-135) |
| 8 | Dashboards + Reports | E13 + E14 + E15 |
| 9 | Frontend Setup + Auth UI | E16 + E17 |
| 10 | Employee + Recruitment UI | E18 + E19 partial |
| 11 | Recruitment UI + Attendance UI | E19 complete + E20 |
| 12 | Leave + Performance UI | E21 + E22 |
| 13 | Dashboards + Notifications UI | E23 + E24 + E25 |
| 14 | Testing + DevOps | E26 + E27 |

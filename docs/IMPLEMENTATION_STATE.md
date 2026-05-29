### Metrics

- ORM tables: 35
- Passing tests: `157` backend tests in `backend/tests` (full run requires `sklearn` + spaCy model in environment)
- Frontend checks: production `docker build` and `next build` verified in CI/Docker context
- Alembic migrations: 1 (0001_initial_schema — all 35 tables)
- Docker images: `infrastructure/docker/Dockerfile.backend`, `infrastructure/docker/Dockerfile.frontend`
- Compose: `docker-compose.yml` (dev), `docker-compose.prod.yml` (prod + nginx)
- CI/CD: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`

---

### Completed Epics

- E1 T-001–T-012: Scaffolding + infrastructure
- E2 T-013–T-018: ORM models (35 tables)
- E3 T-019–T-030: Auth module
- E4 T-031–T-039: User & RBAC module
- E5 T-040–T-053: Employee module
- E6 T-054–T-061: Department, Designation, reference lists
- E7 T-062–T-073: Attendance module
- E8 T-074–T-085: Leave module
- E9 T-086–T-105: Recruitment module
- E10 T-106–T-115: AI Screening Engine
- E11 T-116–T-128: Performance module
- E12 T-129–T-135: Notifications module
- E13 T-136–T-141: Dashboard APIs (HR, Recruitment, Attendance, Performance, Employee)
- E14 T-142–T-150: Reporting & Export (employees, attendance, recruitment/performance CSV exports, shared utilities)
- E15 T-151–T-156: Audit Log Module (admin-only list/detail/activity endpoints + date/search filters + centralized writer)
- E16 T-157–T-165: Frontend Project Setup (API client, auth/query providers, route middleware, shared components, validations, types)
- E17 T-166–T-172: Frontend Auth Pages (login/forgot/reset/unauthorized + auth hook + profile menu)
- E18 T-173–T-182: Frontend Employee Management (services, hooks, list/detail/forms, org admin pages, search, report export)
- E19 T-183–T-196: Frontend Recruitment (jobs, candidates, AI screening, interviews, ranking, recruitment report)
- E20 T-197–T-204: Frontend Attendance (check-in/out, calendar, HR daily/monthly views, corrections, attendance report)
- E21 T-205–T-212: Frontend Leave Management (service/hooks, employee leave, request modal, approvals, HR views, leave types, notifications)
- E22 T-213–T-221: Frontend Performance (service/hooks, cycles, review creation, employee/manager views, metrics admin, history, report, feedback)
- E23 T-222–T-228: Frontend Dashboards (HR, recruitment, attendance, performance, employee dashboards; StatCard upgrade; dashboard hooks)
- E24 T-229–T-233: Frontend Notifications UI (service/hooks, bell dropdown, list page, preferences page, 30s polling)
- E25 T-234–T-240: Frontend Admin Pages (users, roles, audit logs, settings stub, admin navigation section)
- E26 T-241–T-255: Testing (pytest config/fixtures, backend test suites, Vitest setup, smoke tests, coverage threshold config)
- E27 T-256–T-264: DevOps & Deployment (Dockerfiles, compose dev/prod, nginx, GitHub Actions CI/CD, backup script, README)

---

### Active Epic

None — implementation plan complete (T-001–T-264).

---

### Implemented Modules

- `app/modules/auth/` — `/api/v1/auth/`
- `app/modules/user/` — `/api/v1/users/`
- `app/modules/employee/` — `/api/v1/employees/`
- `app/modules/organization/` — `/api/v1/departments/`, `/api/v1/designations/`, `/api/v1/employment-statuses/`, `/api/v1/attendance-statuses/`
- `app/modules/attendance/` — `/api/v1/attendance/`
- `app/modules/leave/` — `/api/v1/leave/`, `/api/v1/leave-types/`
- `app/modules/recruitment/` — `/api/v1/jobs/`, `/api/v1/candidates/`, `/api/v1/applications/`, `/api/v1/interviews/`
- `app/modules/performance/` — `/api/v1/performance/`
- `app/modules/notifications/` — `/api/v1/notifications/`
- `app/modules/dashboard/` — `/api/v1/dashboard/` (`/hr`, `/recruitment`, `/attendance`, `/performance`, `/employee`)
- `app/modules/reporting/` — `/api/v1/reports/employees`, `/api/v1/reports/attendance`, `/api/v1/reports/recruitment`, `/api/v1/reports/performance`, export endpoints (`/employees/export`, `/attendance/export`, `/recruitment/export`, `/performance/export`)
- `app/modules/audit_logs/` — `/api/v1/audit-logs` (`GET /`, `GET /{id}`, `GET /users/{user_id}/activity`, `GET /resources/{resource_type}/{resource_id}`)
- `app/core/` — shared reporting utilities (`export.py`, `pagination.py`, `sorting.py`, `filtering.py`)
- `app/core/` — centralized audit writer (`audit.py`)
- `app/ai/` — screening engine, resume parser, skill extractor, matcher, scorer, LLM client
- `frontend/src/services/api.ts` — Axios client with auth headers, refresh retry, and 401/403 handling
- `frontend/src/providers/` — `auth-provider`, `query-provider`, `toast-provider`
- `frontend/middleware.ts` — route protection + role-based redirects
- `frontend/src/components/common/` and `frontend/src/components/layout/` — E16 shared UI/layout components
- `frontend/src/lib/validations/index.ts` + `frontend/src/types/api.ts` — shared Zod schemas and API type system
- `frontend/src/app/login`, `frontend/src/app/forgot-password`, `frontend/src/app/reset-password` — auth pages
- `frontend/src/app/unauthorized` + `frontend/src/components/layout/user-profile-menu.tsx` — unauthorized page + profile menu
- `frontend/src/services/employee.service.ts`, `organization.service.ts`, `reporting.service.ts` — E18 API clients
- `frontend/src/hooks/use-employees.ts` — E18 TanStack Query hooks
- `frontend/src/app/hr/employees`, `frontend/src/app/hr/reports/employees` — employee list + report pages
- `frontend/src/app/admin/departments`, `frontend/src/app/admin/designations` — organization admin pages
- `frontend/src/components/employees/` — `employee-form`, `employee-search`
- `frontend/src/services/job.service.ts`, `candidate.service.ts`, `interview.service.ts` — E19 API clients
- `frontend/src/hooks/use-jobs.ts`, `use-candidates.ts`, `use-interviews.ts` — E19 TanStack Query hooks
- `frontend/src/app/recruiter/jobs`, `frontend/src/app/recruiter/candidates`, `frontend/src/app/recruiter/interviews` — recruitment pages
- `frontend/src/app/hr/reports/recruitment` — recruitment report page
- `frontend/src/components/recruitment/` — job form, resume upload, AI analysis, notes, interview schedule
- `frontend/src/services/attendance.service.ts` — E20 attendance API client
- `frontend/src/hooks/use-attendance.ts` — E20 TanStack Query hooks
- `frontend/src/app/employee/attendance` — employee check-in/out + calendar + history
- `frontend/src/app/hr/attendance/daily`, `corrections`, `monthly` — HR attendance views
- `frontend/src/app/hr/reports/attendance` — attendance report + CSV export
- `frontend/src/components/attendance/` — calendar, correction request dialog
- `frontend/src/services/leave.service.ts` — E21 leave API client + leave type/balance operations
- `frontend/src/hooks/use-leave.ts` — E21 TanStack Query leave hooks
- `frontend/src/app/employee/leave` — employee leave balance/history/request page
- `frontend/src/components/leave/` — leave request and approval dialogs
- `frontend/src/app/hr/leave`, `hr/leave/approvals`, `hr/leave/balances` — HR leave management, approvals, and balances
- `frontend/src/app/admin/leave-types` — leave type CRUD page
- `frontend/src/services/notification.service.ts`, `frontend/src/hooks/use-notifications.ts` — notification queries used for leave badge integration
- `frontend/src/services/performance.service.ts` — E22 performance API client + report/export
- `frontend/src/hooks/use-performance.ts` — E22 TanStack Query performance hooks
- `frontend/src/app/hr/performance/cycles`, `hr/performance/reviews/new` — cycle management + review creation
- `frontend/src/app/employee/performance` — employee review history view
- `frontend/src/app/manager/performance/team` — manager team performance table
- `frontend/src/app/admin/performance/metrics` — performance metrics CRUD
- `frontend/src/app/hr/employees/[id]/performance` — employee performance history + trend chart
- `frontend/src/app/hr/reports/performance` — performance report + CSV export
- `frontend/src/components/performance/` — star rating, review detail card, feedback form
- `frontend/src/services/dashboard.service.ts` — E23 dashboard API client
- `frontend/src/hooks/use-dashboard.ts` — E23 dashboard hooks with 60s refresh
- `frontend/src/app/hr/dashboard` — HR dashboard KPIs + charts
- `frontend/src/app/recruiter/dashboard` — recruitment dashboard KPIs + donut chart
- `frontend/src/app/hr/dashboard/attendance` — attendance dashboard with weekly trend + dept breakdown
- `frontend/src/app/hr/dashboard/performance` — performance dashboard with cycle state handling
- `frontend/src/app/employee/dashboard` — employee dashboard widgets + shortcuts
- `frontend/src/components/layout/notifications-bell.tsx` — E24 notification bell/dropdown with unread badge
- `frontend/src/app/notifications` — full notifications list with filter, pagination, mark-read actions
- `frontend/src/app/settings/notifications` — notification preferences page
- `frontend/src/services/admin-user.service.ts` + `frontend/src/hooks/use-admin.ts` — E25 admin user and audit hooks/services
- `frontend/src/app/admin/users` — user list/create/assign/deactivate management page
- `frontend/src/app/admin/roles` — read-only role and permission catalog page
- `frontend/src/app/admin/audit-logs` — filterable audit logs with detail modal and JSON diff panes
- `frontend/src/app/admin/settings` — admin settings stub (version + seed placeholder)
- `backend/tests/conftest.py` — shared testing env + test client/session/token fixtures
- `backend/pyproject.toml` — pytest async settings + coverage threshold/reporting config
- `frontend/vitest.config.ts` + `frontend/src/test/` — Vitest + Testing Library setup utilities
- `frontend/src/app/login/page.test.tsx`, `frontend/src/providers/auth-provider.test.tsx` — frontend smoke tests
- `infrastructure/docker/Dockerfile.backend`, `Dockerfile.frontend` — production images (non-root)
- `docker-compose.yml`, `docker-compose.prod.yml` — dev and prod orchestration
- `infrastructure/nginx/nginx.conf` — reverse proxy, gzip, security headers
- `infrastructure/scripts/backup.sh`, `deploy.sh` — backup and remote deploy helpers
- `.github/workflows/ci.yml`, `deploy.yml` — CI on PR, CD on merge to `main`

---

### Known Deviations from Spec

- Departments: flat (no `parent_department_id` — column absent from schema.sql)
- Job statuses: `published`/`closed` (not `open`/`archived` — matches schema.sql)
- Application pipeline: `applied`→`shortlisted`→`interview_scheduled`→`interviewed`→`offered`→`hired`/`rejected`
- Employment status values: `active`/`inactive`/`on_leave` (seed follows ImplementationPlan, not schema.sql Title Case)
- Password reset expiry: 24h (architecture.md) overrides plan's 1h
- Employee deactivate button shown to system administrators only (backend DELETE is admin-only; edit remains HR/Admin)
- Job candidate count on list cards fetched via lightweight candidates pagination query (backend JobResponse has no candidate_count field)
- Manual override endpoint path uses `/candidates/{application_id}/override` per backend route mount
- HR pending corrections list aggregates per-record correction queries (no global pending-corrections API)
- Monthly summary uses `listAttendance` for daily breakdown (MonthlySummaryResponse has aggregates only)
- `useMyEmployeeId` resolves employee via email search on employees list (no dedicated `/me/employee` endpoint)
- Leave balance manual adjustment endpoint is not exposed in leave routes; HR balances page surfaces initialization flows and flags manual adjustment as API-unavailable
- Leave notification deep-linking parses `leave_request_id` from notification title/message UUID text when present (notification schema has no explicit resource link field)
- Manager team performance row click navigates to `/hr/employees/{id}` (no dedicated manager employee detail route)
- Performance feedback form re-fetches feedback list after submit (backend create response does not include full author enrichment in all paths)
- HR dashboard charts use `GET /dashboard/attendance` and `GET /departments` for trend/headcount because `GET /dashboard/hr` provides KPIs only (response schema omits chart series)
- Employee dashboard “recent notifications” uses `/notifications` list because `GET /dashboard/employee` returns unread count only (no notification list payload)
- Notification polling uses `GET /notifications/unread-count` alias at 30s interval (backend supports both `/count` and `/unread-count`)
- Role management is read-only/static because `/api/v1/roles` list endpoint remains unimplemented; user role removal by slug is blocked by missing role-id mapping in current API responses
- Local runtime currently lacks `sklearn`; full backend test run halts in AI matcher tests until dependency is installed in environment
- HANDOFF previously referenced T-265; ImplementationPlan ends at T-264

---

### Technical Debt / Pending Wire-ups

- Leave balance initialization on employee creation not yet wired
- No profile photo upload endpoint yet
- No delete endpoint for notifications (schema has no deleted_at)
- `/api/v1/roles` list endpoint not implemented (role slugs managed via seed + constants)
- Production CD requires repository secrets (`SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `DEPLOY_PATH`)

---

### Config Variables (all in `core/config.py` + `.env.example`)

DATABASE_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES,
REFRESH_TOKEN_EXPIRE_DAYS, PASSWORD_RESET_EXPIRE_HOURS, CORS_ORIGINS,
RESUME_UPLOAD_DIR, MAX_RESUME_SIZE_BYTES, OPENAI_API_KEY, AI_API_KEY,
AI_MODEL, AI_BASE_URL, AI_MAX_TOKENS, AI_TEMPERATURE, AI_AUTO_SCREEN_ON_UPLOAD,
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT, POSTGRES_HOST,
BACKEND_PORT, FRONTEND_PORT, HTTP_PORT, NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_API_URL

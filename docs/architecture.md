\# System Overview



Smart HR is a web-based Human Resource Management platform designed around the MVP scope defined in the PRD.



The platform provides:



\- Authentication \& RBAC

\- Employee Management

\- Recruitment Management

\- AI Resume Screening

\- Attendance Management

\- Leave Management

\- Performance Management

\- Analytics \& Reporting

\- Notifications

\- HR and Employee Dashboards



The architecture follows a modular monolith approach for MVP delivery.



Reasoning:



\- Faster implementation

\- Easier deployment

\- Lower operational complexity

\- Simpler debugging

\- Appropriate for expected MVP scale

\- Can evolve into microservices later without major rewrites



\---



\# Technology Stack



\## Frontend



\### Framework



\*\*Next.js 15 (App Router)\*\*



Why:



\- Production-ready React framework

\- Excellent routing system

\- Server Components support

\- Optimized performance

\- Easy deployment

\- Strong ecosystem



\---



\### Language



\*\*TypeScript\*\*



Why:



\- Type safety

\- Better maintainability

\- Fewer runtime bugs

\- Superior developer experience



\---



\### UI Components



\*\*shadcn/ui\*\*



Why:



\- Professional design system

\- Accessible components

\- Full customization

\- No vendor lock-in



\---



\### Styling



\*\*Tailwind CSS\*\*



Why:



\- Fast UI development

\- Consistent design

\- Excellent responsiveness

\- Small production bundles



\---



\### Form Management



\*\*React Hook Form\*\*



Why:



\- High performance

\- Minimal rerenders

\- Easy validation



\---



\### Validation



\*\*Zod\*\*



Why:



\- Shared validation schemas

\- Strong TypeScript integration

\- Backend/frontend consistency



\---



\### State Management



\*\*TanStack Query\*\*



Why:



\- Server state management

\- Request caching

\- Automatic refetching

\- Mutation support



\---



\### Charts



\*\*Recharts\*\*



Why:



\- Dashboard analytics

\- Attendance visualization

\- Recruitment metrics

\- Performance trends



\---



\# Architecture Diagram



```text

┌──────────────────────────────────────────────┐

│                  Frontend                    │

│               Next.js Application            │

└─────────────────────┬────────────────────────┘

&#x20;                     │ HTTPS

&#x20;                     ▼

┌──────────────────────────────────────────────┐

│                API Layer                     │

│             FastAPI REST API                 │

└─────────────────────┬────────────────────────┘

&#x20;                     │

&#x20;     ┌───────────────┼────────────────┐

&#x20;     ▼               ▼                ▼

┌──────────┐   ┌────────────┐   ┌────────────┐

│ Auth     │   │ HR Modules │   │ AI Engine  │

│ Module   │   │ Services   │   │            │

└────┬─────┘   └─────┬──────┘   └─────┬──────┘

&#x20;    │               │                │

&#x20;    └───────────────┼────────────────┘

&#x20;                    ▼

&#x20;         ┌──────────────────┐

&#x20;         │ PostgreSQL       │

&#x20;         │ Primary Database │

&#x20;         └──────────────────┘

```



\---



\# Frontend Design



\## Architecture Pattern



Feature-Based Architecture



```text

src/

├── app/

├── components/

├── features/

├── hooks/

├── services/

├── lib/

├── types/

├── providers/

└── constants/

```



\---



\## Application Areas



\### Public



\- Login

\- Forgot Password



\---



\### Admin



\- User Management

\- Role Management

\- Audit Logs



\---



\### HR



\- Dashboard

\- Employees

\- Recruitment

\- Attendance

\- Leave

\- Performance

\- Reports

\- Notifications



\---



\### Recruiter



\- Jobs

\- Candidates

\- Resume Reviews

\- Candidate Rankings



\---



\### Employee



\- Dashboard

\- Profile

\- Attendance

\- Leave Requests

\- Performance

\- Notifications



\---



\## Frontend Communication



All communication occurs through:



```text

Frontend

&#x20;   ↓

Axios Client

&#x20;   ↓

REST API

```



Request interceptor:



\- JWT attachment



Response interceptor:



\- Refresh token handling

\- Global error handling



\---



\# Backend Design



\## Framework



\*\*FastAPI\*\*



Why:



\- Excellent performance

\- Native OpenAPI generation

\- Python ecosystem compatibility

\- Ideal for AI integration

\- Async support



\---



\## Architecture Pattern



Layered Clean Architecture



```text

API Layer

&#x20;   ↓

Service Layer

&#x20;   ↓

Repository Layer

&#x20;   ↓

Database Layer

```



\---



\## Modules



\### Authentication Module



Responsibilities:



\- Login

\- Logout

\- Token refresh

\- RBAC enforcement



\---



\### Employee Module



Responsibilities:



\- Employee CRUD

\- Employee search

\- Employee filtering



\---



\### Recruitment Module



Responsibilities:



\- Job postings

\- Resume uploads

\- Candidate management

\- Candidate ranking

\- Shortlisting



\---



\### Attendance Module



Responsibilities:



\- Check-in

\- Check-out

\- Attendance reports

\- Attendance analytics



\---



\### Leave Module



Responsibilities:



\- Leave requests

\- Leave approvals

\- Leave history



\---



\### Performance Module



Responsibilities:



\- KPI tracking

\- Reviews

\- Ratings

\- Reports



\---



\### Reporting Module



Responsibilities:



\- Workforce analytics

\- Exportable reports

\- Dashboard metrics



\---



\### Notification Module



Responsibilities:



\- In-app notifications

\- Event generation



\---



\### Event Dispatch Pattern



Notifications are generated by an internal in-process event dispatcher (MVP: direct service-layer calls; future: pub/sub).



Events that produce notifications:



\- leave\_request.approved → notify requesting employee

\- leave\_request.rejected → notify requesting employee

\- resume\_analysis.complete → notify assigned recruiter

\- performance\_review.submitted → notify reviewed employee

\- attendance\_correction.reviewed → notify requesting employee



Each event handler calls the Notification Service to insert a record into the \`notifications\` table.



\---



\## Internal Structure



```text

module/

├── controller.py

├── service.py

├── repository.py

├── schema.py

├── model.py

└── routes.py

```



\---



\# Database Design



\## Database



\*\*PostgreSQL\*\*



Why:



\- ACID compliance

\- Excellent indexing

\- JSON support

\- Production ready

\- Strong analytics performance



\---



\## Core Tables



\### users



```text

id

email

password\_hash

is\_active

created\_at

updated\_at

```



\---



\### roles



```text

id

name

description

```



\---



\### user\_roles



```text

user\_id

role\_id

```



\---



\### employees



```text

id

employee\_code

first\_name

last\_name

email

phone

department

designation

salary

employment\_status

join\_date

created\_at

updated\_at

```



\---



\### jobs



```text

id

title

department

description

required\_skills

status

created\_by

created\_at

```



\---



\### candidates



```text

id

job\_id

name

email

resume\_url

screening\_score

screening\_result

status

created\_at

```



\---



\### resume\_analysis



```text

id

candidate\_id

extracted\_skills

matched\_skills

missing\_skills

score

explanation

created\_at

```



\---



\### attendance



```text

id

employee\_id

date

check\_in

check\_out

status

```



\---



\### leave\_requests



```text

id

employee\_id

leave\_type

start\_date

end\_date

status

approved\_by

created\_at

```



\---



\### performance\_reviews



```text

id

employee\_id

review\_period

rating

comments

created\_by

created\_at

```



\---



\### notifications



```text

id

user\_id

title

message

is\_read

created\_at

```



\---



\### audit\_logs



```text

id

user\_id

action

resource

resource\_id

ip\_address

created\_at

```



\---



\# Authentication Design



\## Authentication Method



JWT Authentication



\---



\### JWT Claims



Every issued access token includes:



\- \`iss\`: "smarthr-api"

\- \`aud\`: "smarthr-client"

\- \`sub\`: user UUID

\- \`roles\`: list of role names

\- \`exp\`: expiry timestamp



Both \`iss\` and \`aud\` are validated on every authenticated request. Tokens missing or mismatching either claim are rejected with 401 Unauthorized.



\---



\## Token Strategy



\### Access Token



```text

Lifetime: 15 minutes

```



Purpose:



\- API authorization



\---



\### Refresh Token



```text

Lifetime: 7 days

```



Purpose:



\- Silent session renewal



\---



\### Refresh Token Storage



Refresh tokens are persisted in the \`refresh\_tokens\` table.



On logout, the token's \`revoked\_at\` is set to the current timestamp immediately.



On \`POST /auth/refresh\`, the system verifies the token exists, is not revoked, and has not expired. Token rotation is applied: each refresh call invalidates the old token and issues a new one with a new expiry.



Token reuse detection: if a revoked token is presented, all tokens for that user are immediately revoked.



\---



\## Login Flow



```text

User Login

&#x20;     ↓

Credentials Validation

&#x20;     ↓

Password Verification

&#x20;     ↓

Generate JWT

&#x20;     ↓

Generate Refresh Token

&#x20;     ↓

Return Tokens

```



\---



\### Employee Account Creation Flow



Employee accounts are created by HR Managers, not through self-registration.



Flow:



\```text

HR creates employee record

      ↓

Service layer auto-creates linked users record (is\_active = FALSE)

      ↓

password\_reset\_tokens record generated (expires in 24 hours)

      ↓

Token returned in API response (MVP: HR shares manually; future: email dispatch)

      ↓

Employee sets password via POST /auth/reset-password

      ↓

users.is\_active set to TRUE on first successful password set

\```



\---



\## Password Security



Algorithm:



```text

Argon2

```



Why:



\- Memory-hard

\- Resistant to GPU attacks

\- Industry recommended



\---



\## RBAC Model



Roles:



\- System Administrator

\- HR Manager

\- Recruiter

\- Employee

\- Department Manager



Authorization performed:



```text

User

&#x20;↓

Role

&#x20;↓

Permission

&#x20;↓

Resource Access

```



\---



\### Row-Level Authorization Rules



Role-based access is enforced at the module level. Row-level ownership is enforced in the service layer:



\- Employee role: all data access endpoints validate that the resource \`employee\_id\` or \`user\_id\` matches the \`user\_id\` extracted from the JWT. Mismatches return 403 Forbidden.

\- Department Manager role: attendance, leave, and performance data access is filtered to employees where \`employees.manager\_id\` matches the manager's employee record.

\- HR Manager and System Administrator: no row-level restriction beyond module-level RBAC.

\- Recruiters: employee read access is scoped to name and contact fields only; salary and employment\_status fields are excluded from response payloads.



\---



\### Canonical Permissions



Permission strings use the \`resource:action\` format and are seeded in \`schema.sql\` (see SEED DATA — ROLES \& PERMISSIONS). Middleware maps each API route to one permission; missing permission returns 403 Forbidden.



| Permission | Endpoint / capability |
|------------|----------------------|
| \`auth:setup\` | \`POST /auth/setup\` |
| \`auth:login\` | \`POST /auth/login\` |
| \`auth:refresh\` | \`POST /auth/refresh\` |
| \`auth:logout\` | \`POST /auth/logout\` |
| \`auth:password:reset\` | \`POST /auth/forgot-password\`, \`POST /auth/reset-password\` |
| \`auth:me:read\` | \`GET /auth/me\` |
| \`user:*\` | User management APIs |
| \`employee:*\` | Employee CRUD and profile APIs |
| \`department:*\`, \`designation:*\` | Organization APIs |
| \`employment_status:read\`, \`attendance_status:read\` | Lookup list endpoints |
| \`attendance:*\` | Check-in, check-out, history, corrections, reports |
| \`leave:*\` | Leave requests, approvals, balances |
| \`job:*\`, \`candidate:*\`, \`application:*\` | Recruitment APIs |
| \`resume:upload\`, \`ai:analyze\`, \`ai:read\` | Resume upload and analysis polling |
| \`interview:*\` | Interview scheduling APIs |
| \`performance:*\` | Cycles, reviews, metrics, feedback |
| \`notification:*\` | Notifications and preferences |
| \`dashboard:*\` | Dashboard aggregation endpoints |
| \`report:*\` | Reporting and export endpoints |
| \`audit:read\` | \`GET /audit-logs\` |



Default role-to-permission mappings are seeded for: System Administrator (all), HR Manager, Recruiter, Department Manager, and Employee. Row-level rules in the service layer further restrict \`employee:read\` and team-scoped modules beyond these coarse grants.



\---



\### First Administrator Bootstrap



On first deployment, the database contains no users. The backend exposes a one-time setup endpoint:



\`POST /auth/setup\`



This endpoint:



\- Is only callable when the \`users\` table contains zero rows

\- Creates the initial System Administrator user and role assignment

\- Returns a temporary password that must be changed on first login

\- Returns 409 Conflict on all subsequent calls



No seed SQL is used for admin accounts to avoid hardcoded credentials in the repository.



\---



\# AI Resume Screening Design



\## Objective



Provide:



\- Skill extraction

\- Resume matching

\- Candidate scoring

\- Candidate ranking

\- Shortlisting



As defined by the PRD.



\---



\## Pipeline



Resume Upload (synchronous):



\```text

POST /candidates/\{id\}/resume

      ↓

Validate MIME type (PDF/DOCX only, max 10 MB; read file magic bytes, not extension)

      ↓

Store file to local Docker volume (/app/uploads/resumes/)

      ↓

Insert resume\_files record (mime\_type, file\_size\_bytes, is\_active = TRUE)

      ↓

Create resume\_analysis record (analysis\_status = 'pending')

      ↓

Enqueue background analysis task (FastAPI BackgroundTasks for MVP)

      ↓

Return 202 Accepted with \{ "analysis\_id": "<uuid>" \}

\```



Analysis Processing (asynchronous):



\```text

FastAPI BackgroundTask executes:

      ↓

PyMuPDF / python-docx parse

      ↓

Update resume\_analysis (analysis\_status = 'processing')

      ↓

spaCy skill extraction

      ↓

TF-IDF cosine similarity vs job\_skills for the linked application

      ↓

Score calculation

      ↓

Update resume\_analysis (analysis\_status = 'complete', scores, matched/missing skills)

      ↓

Update candidate\_applications.ai\_score and ranking

      ↓

Create notification record for recruiter

\```



Status Polling:



\```text

GET /ai/analysis/\{analysis\_id\}

      ↓

Returns analysis\_status and full result when status = 'complete'

\```



\---



\## Technologies



\### Resume Parsing



PyMuPDF



Why:



\- Fast PDF extraction

\- Reliable parsing



\---



\### NLP



spaCy



Why:



\- Lightweight

\- Production ready

\- Excellent skill extraction



\---



\### Matching



Scikit-learn



Technique:



```text

TF-IDF

\+

Cosine Similarity

```



Why:



\- Transparent scoring

\- Explainable results

\- Easy manual verification



\---



\## AI Output



```json

{

&#x20; "candidate\_score": 82,

&#x20; "matched\_skills": \[

&#x20;   "Python",

&#x20;   "SQL",

&#x20;   "Machine Learning"

&#x20; ],

&#x20; "missing\_skills": \[

&#x20;   "Docker"

&#x20; ],

&#x20; "recommendation": "Shortlist"

}

```



\---



\## Manual Override



Recruiters can:



\- Approve candidate

\- Reject candidate

\- Override AI ranking



Required by PRD acceptance criteria.



\---



\# Security Architecture



\## Identity Security



\- JWT authentication

\- Refresh tokens

\- Argon2 password hashing

\- RBAC authorization



\---



\## API Security



\- HTTPS only

\- Rate limiting

\- Rate limiting on \`POST /auth/login\`: maximum 10 attempts per IP per 15-minute window, enforced via FastAPI middleware with a Redis-backed counter (Redis is added to docker-compose.yml alongside the existing services)

\- Request validation

\- Input sanitization



\---



\### CORS Policy



FastAPI is configured with CORSMiddleware.



\- Development: allowed origins include \`http://localhost:3000\`

\- Production: allowed origins locked to the deployed Next.js domain

\- Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS

\- Allowed headers: Authorization, Content-Type

\- Credentials: allowed (required for cookie-based refresh token future upgrade)



\---



\## Database Security



\- Parameterized queries

\- Encrypted backups

\- Least-privilege database user

\- Salary data (\`employees.salary\`) is protected at rest via full-disk encryption on the PostgreSQL Docker volume. Column-level encryption using pgcrypto (\`pgp\_sym\_encrypt\` / \`pgp\_sym\_decrypt\`) is targeted for the post-MVP hardening phase. The encryption key is stored in environment variables, never in source code.



\---



\## Application Security



\- CSRF protection

\- XSS protection

\- Content Security Policy

\- Secure cookies



\---



\## Audit Logging



Track:



\- Login events

\- Logout events

\- Employee modifications

\- Candidate decisions

\- Leave approvals

\- Role changes



\---



\### Audit Log Data Policy



\- Salary fields are excluded from \`before\_state\` and \`after\_state\` JSONB snapshots. The service layer replaces salary values with the string "REDACTED" before writing the snapshot.

\- Audit log retention period: 2 years. Records older than 2 years are eligible for archival or deletion via a scheduled maintenance job.

\- \`ip\_address\` is NOT NULL on all audit log records (column default \`0.0.0.0\`). System-generated events use the sentinel value \`0.0.0.0\` when no client IP is available.



\---



\## Secrets Management



Never store secrets in source code.



Store:



```text

JWT secrets

Database credentials

Encryption keys

```



inside environment variables.



\---



\# Deployment Architecture



\## Containers



Dockerized deployment.



Services:



```text

Frontend

Backend

PostgreSQL

```



\---



\## Environment



\### Production



```text

Internet

&#x20;   ↓

Nginx Reverse Proxy

&#x20;   ↓

Next.js Frontend

&#x20;   ↓

FastAPI Backend

&#x20;   ↓

PostgreSQL

```



\---



\## Reverse Proxy



Nginx



Responsibilities:



\- TLS termination

\- Compression

\- Security headers

\- Routing



\---



\## CI/CD



GitHub Actions



Pipeline:



```text

Push

&#x20;↓

Lint

&#x20;↓

Tests

&#x20;↓

Build

&#x20;↓

Docker Image

&#x20;↓

Deploy

```



\---



\# Folder Structure



```text

smart-hr/



├── frontend/

│

│   ├── src/

│   │   ├── app/

│   │   ├── components/

│   │   ├── features/

│   │   ├── hooks/

│   │   ├── services/

│   │   ├── providers/

│   │   ├── types/

│   │   ├── lib/

│   │   └── constants/

│   │

│   ├── public/

│   └── package.json

│

├── backend/

│

│   ├── app/

│   │

│   │   ├── modules/

│   │   │

│   │   ├── auth/

│   │   ├── employee/

│   │   ├── recruitment/

│   │   ├── attendance/

│   │   ├── leave/

│   │   ├── performance/

│   │   ├── reporting/

│   │   └── notifications/

│   │

│   ├── core/

│   ├── database/

│   ├── ai/

│   │   ├── parser.py          \# PyMuPDF / python-docx resume text extraction

│   │   ├── extractor.py       \# spaCy skill entity extraction

│   │   ├── matcher.py         \# scikit-learn TF-IDF cosine similarity scoring

│   │   └── engine.py          \# Orchestrator: coordinates parse → extract → match → store

│   ├── middleware/

│   ├── tests/

│   └── main.py

│

├── infrastructure/

│

│   ├── docker/

│   ├── nginx/

│   └── scripts/

│

├── docs/

│   ├── PRD.md

│   └── Architecture.md

│

├── .env.example

├── docker-compose.yml

└── README.md

```



\---



\# Scalability Considerations



\## Database



Future upgrades:



\- Read replicas

\- Query optimization

\- Connection pooling



\---



\## Backend



Future upgrades:



\- Horizontal API scaling

\- Background workers

\- Queue processing



\---



\## AI Processing



Future upgrades:



\- Dedicated AI service

\- Async resume processing

\- Batch screening



\---



\## Storage



\### Current MVP Storage



Resume files are stored on the local filesystem inside a named Docker volume mounted at \`/app/uploads/resumes/\` in the backend container.



Constraints:



\- Maximum file size: 10 MB

\- Accepted MIME types: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document (DOCX)

\- MIME type validated by reading file magic bytes server-side, not by file extension

\- \`resume\_files.file\_url\` stores the relative server path

\- Volume is declared in docker-compose.yml as a named volume for persistence across container restarts



Future upgrades:



\- Object storage for resumes

\- CDN integration



\---



\## Architecture Evolution



Current:



```text

Modular Monolith

```



Future:



```text

Auth Service

Employee Service

Recruitment Service

AI Screening Service

Notification Service

Reporting Service

```



The MVP architecture intentionally remains a modular monolith because it satisfies all approved PRD requirements while minimizing development complexity and operational overhead.


You are a Principal Database Architect.

PRD.md and Architecture.md are APPROVED and IMMUTABLE.

Do not modify requirements.
Do not invent new product features.
Design the database strictly from those documents.

# Objective

Create the complete production-ready PostgreSQL database design for Smart HR.

The database must support:

- Authentication
- RBAC
- Employee Management
- Recruitment Management
- AI Resume Screening
- Attendance Management
- Leave Management
- Performance Management
- Notifications
- Dashboards
- Reporting
- Audit Logging

Architecture constraints:

- PostgreSQL
- FastAPI backend
- JWT authentication
- Modular Monolith architecture

Output must be implementation-ready.

---

# Requirements

## 1. Database Design

Design a fully normalized relational database.

Target:

- 3NF minimum
- Avoid duplication
- Support future scalability

Explain normalization decisions.

---

## 2. ER Diagram Description

Produce a textual ER diagram section.

For every entity provide:

- Purpose
- Primary key
- Important attributes
- Relationships

Use notation such as:

Department
    1 ─────── * Employee

Employee
    1 ─────── * Attendance

Job
    1 ─────── * Candidate

etc.

---

## 3. Table Definitions

For every table provide:

### Table Name

Purpose

Columns:

| Column | Type | Nullable | Default | Description |

Primary Key

Foreign Keys

Unique Constraints

Indexes

Check Constraints

---

## 4. Authentication & RBAC Schema

Design:

users

roles

permissions

role_permissions

user_roles

Requirements:

- many-to-many user-role
- many-to-many role-permission
- support future multi-role users
- soft delete capable

Include:

- created_at
- updated_at
- created_by
- updated_by

where appropriate.

---

## 5. Employee Module Schema

Design:

employees

departments

designations

employment_statuses

Requirements:

- employee code uniqueness
- manager hierarchy support
- department assignment
- designation assignment
- future organizational scaling

---

## 6. Recruitment Module Schema

Design:

jobs

job_skills

candidates

candidate_applications

candidate_status_history

resume_files

resume_analysis

candidate_notes

interviews (future-ready)

Requirements:

Support:

- resume uploads
- AI screening
- scoring
- ranking
- recruiter comments
- status tracking

Store:

- extracted skills
- matched skills
- missing skills
- AI score
- recommendation
- explanation

Use JSONB where beneficial.

---

## 7. Attendance Module Schema

Design:

attendance_records

attendance_corrections

attendance_statuses

Requirements:

Support:

- check in
- check out
- work duration
- attendance status
- manual corrections
- reporting

---

## 8. Leave Management Schema

Design:

leave_types

leave_balances

leave_requests

leave_approvals

Requirements:

Support:

- approval workflow
- balances
- future multi-level approvals

---

## 9. Performance Management Schema

Design:

performance_cycles

performance_reviews

performance_metrics

employee_metric_scores

performance_feedback

Requirements:

Support:

- KPI tracking
- ratings
- manager reviews
- historical evaluations

---

## 10. Notification Schema

Design:

notifications

notification_preferences

Requirements:

- in-app notifications
- read status
- future email integration

---

## 11. Reporting & Dashboard Support

Design any supporting aggregate/reference tables only if necessary.

Do not prematurely denormalize.

Explain rationale.

---

## 12. Audit Logging

Design:

audit_logs

Requirements:

Track:

- login
- logout
- create
- update
- delete
- approvals
- recruitment actions
- role changes

Store:

- actor
- action
- resource
- before state
- after state
- timestamp
- IP address

Use JSONB for snapshots.

---

## 13. Constraints

Define:

- PKs
- FKs
- UNIQUE constraints
- CHECK constraints
- NOT NULL constraints

Explain why each exists.

Examples:

- email unique
- employee_code unique
- score between 0 and 100
- valid status enums

---

## 14. Indexing Strategy

For every major table define:

### Primary indexes

### Foreign key indexes

### Search indexes

### Composite indexes

### Reporting indexes

Include rationale.

Examples:

- users(email)
- employees(employee_code)
- candidates(status, created_at)
- attendance(employee_id, attendance_date)

Explain expected query optimization.

---

## 15. PostgreSQL Data Types

Use production-quality types:

Examples:

- UUID
- VARCHAR(n)
- TEXT
- DATE
- TIMESTAMP WITH TIME ZONE
- BOOLEAN
- NUMERIC
- JSONB

Avoid vague types.

---

## 16. Audit Fields

Every transactional table must include:

created_at
updated_at

And where appropriate:

created_by
updated_by

Use TIMESTAMPTZ.

---

## 17. Soft Delete Strategy

Identify tables requiring:

deleted_at

Explain why.

Do not apply blindly.

---

## 18. PostgreSQL DDL

Generate complete:

database/schema.sql

Requirements:

- CREATE EXTENSION statements
- CREATE TABLE statements
- PKs
- FKs
- UNIQUE constraints
- CHECK constraints
- indexes
- comments where useful

Schema must execute successfully on PostgreSQL 16+.

Use:

gen_random_uuid()

for UUID primary keys.

---

# Output Format

# DatabaseDesign.md

## Overview

## Normalization Strategy

## ER Diagram Description

## Table Definitions

## Relationships

## Constraints

## Indexing Strategy

## Soft Delete Strategy

## Future Scalability Considerations

---

# schema.sql

Provide complete executable PostgreSQL DDL.

No placeholders.

No pseudo-code.

No omitted tables.

Generate production-ready output.
You are a Principal Backend Architect.

PRD.md, Architecture.md, and schema.sql are APPROVED and IMMUTABLE.

These documents are the only source of truth.

Do not invent entities.
Do not invent tables.
Do not invent fields.
Do not invent workflows.

Every endpoint must map directly to schema.sql and approved requirements.

# Objective

Design the complete production-ready REST API contract for Smart HR.

Architecture constraints:

- FastAPI
- PostgreSQL
- JWT Authentication
- RBAC Authorization
- Modular Monolith
- REST API only

The API contract must be implementation-ready and OpenAPI-friendly.

---

# API Standards

## Base URL

/api/v1

---

## Content Type

application/json

---

## Authentication

JWT Bearer Token

Header:

Authorization: Bearer <access_token>

---

## Token Strategy

Access Token:
15 minutes

Refresh Token:
7 days

---

## Response Format

Success:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "Email already exists"
    }
  ]
}
```

---

## HTTP Status Codes

200 OK

201 Created

204 No Content

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error

---

# Output Structure

Generate:

# docs/API.md

Use the following sections.

---

# Authentication APIs

Design endpoints strictly according to schema.sql authentication tables.

Include:

POST /auth/login

POST /auth/refresh

POST /auth/logout

POST /auth/forgot-password

POST /auth/reset-password

GET /auth/me

For every endpoint provide:

## Endpoint

Method

Route

Purpose

Authentication Required

Authorized Roles

Request Body Schema

Response Body Schema

Validation Rules

Error Responses

Database Tables Used

Business Rules

---

# User Management APIs

Only if users table exists in schema.sql.

Include:

Create User

List Users

Get User

Update User

Deactivate User

Assign Role

Remove Role

Permissions Listing

Every endpoint must reference actual tables and columns.

---

# Employee APIs

Generate CRUD and search endpoints strictly from employees-related tables.

Include:

Create Employee

List Employees

Get Employee

Update Employee

Deactivate Employee

Employee Profile

Employee Reporting Manager

Employee Search

Department Filter

Designation Filter

Status Filter

For every endpoint provide:

Method

Route

Purpose

Request Schema

Response Schema

Authorization Rules

Validation Rules

Error Responses

Database Tables Used

Indexes Used

---

# Department APIs

Only if departments table exists.

Generate:

Create

List

Get

Update

Delete

Validation

Permissions

---

# Designation APIs

Only if designations table exists.

Generate full CRUD.

---

# Attendance APIs

Generate endpoints from attendance tables only.

Include:

Check In

Check Out

Attendance History

Daily Attendance

Monthly Attendance

Attendance Corrections

Attendance Summary

Attendance Reports

For every endpoint specify:

Request Schema

Response Schema

Business Rules

Validation Rules

Permission Rules

Database Tables Used

---

# Leave Management APIs

Generate endpoints from leave tables.

Include:

Create Leave Request

List Leave Requests

Approve Leave

Reject Leave

Cancel Leave

Leave Balance

Leave History

Pending Approvals

Multi-level approval readiness

For every endpoint define:

Method

Route

Purpose

Request

Response

Permissions

Validation

Error Handling

Database Tables Used

---

# Recruitment APIs

Generate endpoints strictly from recruitment tables.

Include:

Create Job

Update Job

Publish Job

Close Job

List Jobs

Get Job

Upload Resume

Create Candidate

List Candidates

Get Candidate

Candidate Notes

Candidate Status Update

Candidate Timeline

Shortlist Candidate

Reject Candidate

Manual Override AI Decision

Candidate Ranking

Resume Analysis Results

Interview Scheduling
(only if corresponding table exists)

For each endpoint provide:

Method

Route

Purpose

Request Schema

Response Schema

Authorization

Validation

Error Responses

Database Tables Used

AI Services Used

---

# AI Resume Screening APIs

Generate endpoints only if supported by schema.sql and PRD.

Include:

Resume Upload

Trigger Analysis

Get Analysis

Get Ranking

Get Match Explanation

Manual Override

For every endpoint:

Input

Output

Validation

Authorization

Business Logic

Database Usage

---

# Performance APIs

Generate endpoints from performance tables.

Include:

Performance Cycles

Performance Reviews

Metrics

Scores

Feedback

Reports

Employee View

Manager View

Historical Reviews

For every endpoint provide:

Method

Route

Purpose

Request

Response

Permissions

Validation

Tables Used

---

# Notification APIs

Generate endpoints from notification tables.

Include:

List Notifications

Get Notification

Mark Read

Mark All Read

Notification Preferences

Unread Count

---

# Dashboard APIs

Generate endpoints supporting approved dashboard requirements.

Examples:

GET /dashboard/hr

GET /dashboard/recruitment

GET /dashboard/attendance

GET /dashboard/performance

GET /dashboard/employee

For each endpoint specify:

Returned KPIs

Data Sources

Aggregation Logic

Authorization

Caching Recommendations

---

# Reporting APIs

Generate report endpoints only from available data.

Include:

Attendance Report

Recruitment Report

Performance Report

Employee Report

Dashboard Export

CSV Export

Excel Export
(if approved by architecture)

For every report endpoint define:

Filters

Sorting

Pagination

Response Schema

Performance Considerations

Indexes Used

---

# Audit Log APIs

Generate endpoints only if audit_logs exists.

Include:

List Logs

Get Log

User Activity

Resource Activity

Audit Search

Filtering

Date Range Search

Role Restrictions

---

# Pagination Standard

Use:

?page=1
&page_size=20

Response:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5
  }
}
```

---

# Filtering Standard

Support:

search
status
department
designation
date_from
date_to

Only where applicable.

---

# Sorting Standard

sort_by
sort_order=asc|desc

---

# Validation Rules

Define validation for every field.

Examples:

email

employee_code

salary

rating

score

attendance dates

leave dates

candidate score

status enums

UUID values

---

# Authorization Matrix

Generate a matrix showing:

System Administrator

HR Manager

Recruiter

Department Manager

Employee

vs

Every endpoint.

Use:

Allow
Deny
Conditional

---

# OpenAPI Readiness

Ensure every endpoint includes:

Request DTO

Response DTO

Path Parameters

Query Parameters

Headers

Authentication Requirement

HTTP Status Codes

Validation Constraints

---

# Final Deliverable

Produce a single document:

docs/API.md

Implementation-ready.

No pseudo-code.

No assumptions outside schema.sql.

No endpoints without database support.
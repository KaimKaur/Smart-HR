CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- AUTHENTICATION & RBAC
-- =====================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ,

    CONSTRAINT uq_users_email UNIQUE(email)
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(100) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_roles_name UNIQUE(name)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_permissions_name UNIQUE(name)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(user_id, role_id),

    CONSTRAINT fk_user_roles_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_roles_role
        FOREIGN KEY(role_id)
        REFERENCES roles(id)
        ON DELETE CASCADE
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL,
    permission_id UUID NOT NULL,

    PRIMARY KEY(role_id, permission_id),

    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY(role_id)
        REFERENCES roles(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_role_permissions_permission
        FOREIGN KEY(permission_id)
        REFERENCES permissions(id)
        ON DELETE CASCADE
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_refresh_token_hash UNIQUE(token_hash),
    CONSTRAINT fk_refresh_token_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);

CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_prt_hash UNIQUE(token_hash),
    CONSTRAINT fk_prt_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);
CREATE INDEX idx_prt_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_prt_user ON password_reset_tokens(user_id);

-- =====================================================
-- ORGANIZATION
-- =====================================================

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_departments_name UNIQUE(name)
);

CREATE TABLE designations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    title VARCHAR(150) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_designations_title UNIQUE(title)
);

CREATE TABLE employment_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(100) NOT NULL,

    created_by UUID,
    updated_by UUID,

    CONSTRAINT uq_employment_status_name UNIQUE(name),

    CONSTRAINT fk_employment_statuses_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_employment_statuses_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id)
);

-- =====================================================
-- EMPLOYEES
-- =====================================================

CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID UNIQUE,

    employee_code VARCHAR(50) NOT NULL,

    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),

    department_id UUID NOT NULL,
    designation_id UUID NOT NULL,
    employment_status_id UUID NOT NULL,

    manager_id UUID,

    salary NUMERIC(12,2),

    join_date DATE NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ,

    CONSTRAINT uq_employee_code UNIQUE(employee_code),
    CONSTRAINT uq_employee_email UNIQUE(email),

    CONSTRAINT fk_employee_user
        FOREIGN KEY(user_id)
        REFERENCES users(id),

    CONSTRAINT fk_employee_department
        FOREIGN KEY(department_id)
        REFERENCES departments(id),

    CONSTRAINT fk_employee_designation
        FOREIGN KEY(designation_id)
        REFERENCES designations(id),

    CONSTRAINT fk_employee_status
        FOREIGN KEY(employment_status_id)
        REFERENCES employment_statuses(id),

    CONSTRAINT fk_employee_manager
        FOREIGN KEY(manager_id)
        REFERENCES employees(id)
);

-- =====================================================
-- RECRUITMENT
-- =====================================================

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    title VARCHAR(200) NOT NULL,

    department_id UUID,

    description TEXT NOT NULL,

    status VARCHAR(50) NOT NULL,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ,

    CONSTRAINT chk_job_status
        CHECK(status IN ('draft','published','closed')),

    FOREIGN KEY(department_id)
        REFERENCES departments(id),

    FOREIGN KEY(created_by)
        REFERENCES users(id)
);

CREATE TABLE job_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    job_id UUID NOT NULL,

    skill_name VARCHAR(150) NOT NULL,

    FOREIGN KEY(job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE
);

CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    full_name VARCHAR(200) NOT NULL,

    email VARCHAR(255) NOT NULL,

    phone VARCHAR(50),

    current_status VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ,

    CONSTRAINT uq_candidate_email UNIQUE(email),

    CONSTRAINT chk_candidate_current_status CHECK (
        current_status IN (
            'applied','screening','shortlisted',
            'interview_scheduled','interviewed',
            'offered','rejected','withdrawn'
        ) OR current_status IS NULL
    )
);

CREATE TABLE candidate_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    candidate_id UUID NOT NULL,
    job_id UUID NOT NULL,

    ai_score NUMERIC(5,2),

    ranking INTEGER,

    recommendation VARCHAR(50),

    recruiter_override BOOLEAN DEFAULT FALSE,

    application_status VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ,

    FOREIGN KEY(candidate_id)
        REFERENCES candidates(id),

    FOREIGN KEY(job_id)
        REFERENCES jobs(id),

    CONSTRAINT chk_ai_score
        CHECK(ai_score BETWEEN 0 AND 100),

    CONSTRAINT chk_application_status CHECK (
        application_status IN (
            'applied','screening','shortlisted',
            'interview_scheduled','interviewed',
            'offered','rejected','withdrawn'
        )
    )
);

CREATE TABLE candidate_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL,

    old_status VARCHAR(100),
    new_status VARCHAR(100) NOT NULL,

    changed_by UUID,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(application_id)
        REFERENCES candidate_applications(id),

    FOREIGN KEY(changed_by)
        REFERENCES users(id)
);

CREATE TABLE resume_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    candidate_id UUID NOT NULL,

    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,

    mime_type VARCHAR(100),
    file_size_bytes INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(candidate_id)
        REFERENCES candidates(id)
);

CREATE TABLE resume_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    analysis_status VARCHAR(50) NOT NULL DEFAULT 'pending',

    candidate_id UUID NOT NULL,

    application_id UUID NOT NULL,

    extracted_skills JSONB NOT NULL,
    matched_skills JSONB NOT NULL,
    missing_skills JSONB NOT NULL,

    score NUMERIC(5,2) NOT NULL,

    recommendation VARCHAR(50),

    explanation JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_analysis_status CHECK (
        analysis_status IN ('pending','processing','complete','failed')
    ),

    CONSTRAINT chk_resume_score
        CHECK(score BETWEEN 0 AND 100),

    FOREIGN KEY(candidate_id)
        REFERENCES candidates(id),

    CONSTRAINT fk_resume_analysis_application
        FOREIGN KEY(application_id)
        REFERENCES candidate_applications(id)
);

CREATE TABLE candidate_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    candidate_id UUID NOT NULL,

    note TEXT NOT NULL,

    created_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(candidate_id)
        REFERENCES candidates(id),

    FOREIGN KEY(created_by)
        REFERENCES users(id)
);

CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL,

    scheduled_at TIMESTAMPTZ NOT NULL,

    interviewer_id UUID,

    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',

    notes TEXT,

    created_by UUID,
    updated_by UUID,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(application_id)
        REFERENCES candidate_applications(id),

    FOREIGN KEY(interviewer_id)
        REFERENCES employees(id),

    CONSTRAINT fk_interviews_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_interviews_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id),

    CONSTRAINT chk_interview_status CHECK (
        status IN ('scheduled','completed','cancelled','no_show')
    )
);

-- =====================================================
-- ATTENDANCE
-- =====================================================

CREATE TABLE attendance_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(50) UNIQUE NOT NULL,

    created_by UUID,
    updated_by UUID,

    CONSTRAINT fk_attendance_statuses_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_attendance_statuses_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id)
);

CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID NOT NULL,

    attendance_date DATE NOT NULL,

    check_in_time TIMESTAMPTZ,
    check_out_time TIMESTAMPTZ,

    work_duration_minutes INTEGER,

    attendance_status_id UUID NOT NULL,

    created_by UUID,
    updated_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(employee_id)
        REFERENCES employees(id),

    FOREIGN KEY(attendance_status_id)
        REFERENCES attendance_statuses(id),

    CONSTRAINT fk_attendance_records_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_attendance_records_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id),

    CONSTRAINT uq_employee_attendance
        UNIQUE(employee_id, attendance_date)
);

CREATE TABLE attendance_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    attendance_record_id UUID NOT NULL,

    requested_by UUID NOT NULL,

    reason TEXT NOT NULL,

    correction_status VARCHAR(50) NOT NULL,

    reviewed_by UUID,

    reviewed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(attendance_record_id)
        REFERENCES attendance_records(id),

    FOREIGN KEY(requested_by)
        REFERENCES users(id),

    FOREIGN KEY(reviewed_by)
        REFERENCES users(id),

    CONSTRAINT chk_correction_status CHECK (
        correction_status IN ('pending','approved','rejected')
    )
);

-- =====================================================
-- LEAVE MANAGEMENT
-- =====================================================

CREATE TABLE leave_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(100) NOT NULL UNIQUE,

    annual_allocation INTEGER NOT NULL
);

CREATE TABLE leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID NOT NULL,
    leave_type_id UUID NOT NULL,

    balance NUMERIC(6,2) NOT NULL,

    created_by UUID,
    updated_by UUID,

    FOREIGN KEY(employee_id)
        REFERENCES employees(id),

    FOREIGN KEY(leave_type_id)
        REFERENCES leave_types(id),

    CONSTRAINT fk_leave_balances_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_leave_balances_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id),

    UNIQUE(employee_id, leave_type_id),

    CONSTRAINT chk_balance_non_negative CHECK (balance >= 0)
);

CREATE TABLE leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID NOT NULL,

    leave_type_id UUID NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    reason TEXT,

    status VARCHAR(50) NOT NULL,

    created_by UUID,
    updated_by UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ,

    FOREIGN KEY(employee_id)
        REFERENCES employees(id),

    FOREIGN KEY(leave_type_id)
        REFERENCES leave_types(id),

    CONSTRAINT fk_leave_requests_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_leave_requests_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id),

    CONSTRAINT chk_leave_dates
        CHECK(end_date >= start_date),

    CONSTRAINT chk_leave_status CHECK (
        status IN ('pending','approved','rejected','cancelled')
    )
);

CREATE TABLE leave_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    leave_request_id UUID NOT NULL,

    approver_id UUID NOT NULL,

    approval_level INTEGER NOT NULL DEFAULT 1,

    status VARCHAR(50) NOT NULL,

    remarks TEXT,

    approved_at TIMESTAMPTZ,

    FOREIGN KEY(leave_request_id)
        REFERENCES leave_requests(id),

    CONSTRAINT fk_leave_approvals_approver
        FOREIGN KEY(approver_id)
        REFERENCES users(id)
);

-- =====================================================
-- PERFORMANCE
-- =====================================================

CREATE TABLE performance_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    created_by UUID,
    updated_by UUID,

    CONSTRAINT chk_cycle_dates
        CHECK(end_date >= start_date),

    CONSTRAINT fk_performance_cycles_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_performance_cycles_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id)
);

CREATE TABLE performance_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cycle_id UUID NOT NULL,

    employee_id UUID NOT NULL,

    reviewer_id UUID NOT NULL,

    rating NUMERIC(5,2) NOT NULL,

    comments TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rating
        CHECK(rating BETWEEN 1 AND 5),

    CONSTRAINT uq_review_cycle_employee_reviewer UNIQUE(cycle_id, employee_id, reviewer_id),

    FOREIGN KEY(cycle_id)
        REFERENCES performance_cycles(id),

    FOREIGN KEY(employee_id)
        REFERENCES employees(id),

    FOREIGN KEY(reviewer_id)
        REFERENCES employees(id)
);

CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL,
    description TEXT,

    created_by UUID,
    updated_by UUID,

    CONSTRAINT fk_performance_metrics_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_performance_metrics_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id)
);

CREATE TABLE employee_metric_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    review_id UUID NOT NULL,

    metric_id UUID NOT NULL,

    score NUMERIC(5,2) NOT NULL,

    created_by UUID,
    updated_by UUID,

    CONSTRAINT chk_metric_score
        CHECK(score BETWEEN 0 AND 100),

    FOREIGN KEY(review_id)
        REFERENCES performance_reviews(id),

    FOREIGN KEY(metric_id)
        REFERENCES performance_metrics(id),

    CONSTRAINT fk_employee_metric_scores_created_by
        FOREIGN KEY(created_by)
        REFERENCES users(id),

    CONSTRAINT fk_employee_metric_scores_updated_by
        FOREIGN KEY(updated_by)
        REFERENCES users(id)
);

CREATE TABLE performance_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    review_id UUID NOT NULL,

    feedback_text TEXT NOT NULL,

    created_by UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(review_id)
        REFERENCES performance_reviews(id),

    FOREIGN KEY(created_by)
        REFERENCES employees(id)
);

-- =====================================================
-- NOTIFICATIONS
-- =====================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    is_read BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(user_id)
        REFERENCES users(id)
);

CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL UNIQUE,

    in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    FOREIGN KEY(user_id)
        REFERENCES users(id)
);

-- =====================================================
-- AUDIT LOGS
-- =====================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    actor_user_id UUID,

    action VARCHAR(100) NOT NULL,

    resource_type VARCHAR(100) NOT NULL,

    resource_id UUID,

    ip_address INET NOT NULL DEFAULT '0.0.0.0',

    before_state JSONB,
    after_state JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY(actor_user_id)
        REFERENCES users(id)
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX idx_users_email
ON users(email);

CREATE INDEX idx_employee_code
ON employees(employee_code);

CREATE INDEX idx_employee_department
ON employees(department_id);

CREATE INDEX idx_employee_manager
ON employees(manager_id);

CREATE INDEX idx_jobs_status
ON jobs(status);

CREATE INDEX idx_candidate_email
ON candidates(email);

CREATE INDEX idx_candidate_application_job
ON candidate_applications(job_id);

CREATE INDEX idx_candidate_application_score
ON candidate_applications(ai_score DESC);

CREATE INDEX idx_attendance_employee_date
ON attendance_records(employee_id, attendance_date);

CREATE INDEX idx_leave_employee
ON leave_requests(employee_id);

CREATE INDEX idx_leave_status
ON leave_requests(status);

CREATE INDEX idx_review_employee
ON performance_reviews(employee_id);

CREATE INDEX idx_notifications_user
ON notifications(user_id, is_read);

CREATE INDEX idx_audit_created
ON audit_logs(created_at DESC);

CREATE INDEX idx_audit_actor
ON audit_logs(actor_user_id);

CREATE INDEX idx_resume_analysis_application ON resume_analysis(application_id);
CREATE INDEX idx_resume_analysis_candidate_created ON resume_analysis(candidate_id, created_at DESC);

CREATE INDEX idx_ca_job_status ON candidate_applications(job_id, application_status);

CREATE INDEX idx_leave_emp_status ON leave_requests(employee_id, status);

-- =====================================================
-- SEED DATA — LOOKUP TABLES
-- =====================================================

INSERT INTO employment_statuses (id, name) VALUES
    (gen_random_uuid(), 'Active'),
    (gen_random_uuid(), 'Inactive'),
    (gen_random_uuid(), 'On Notice'),
    (gen_random_uuid(), 'Terminated')
ON CONFLICT (name) DO NOTHING;

INSERT INTO attendance_statuses (id, name) VALUES
    (gen_random_uuid(), 'Present'),
    (gen_random_uuid(), 'Absent'),
    (gen_random_uuid(), 'Half Day'),
    (gen_random_uuid(), 'Leave'),
    (gen_random_uuid(), 'Holiday')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- SEED DATA — ROLES & PERMISSIONS (R-03)
-- =====================================================

INSERT INTO roles (id, name, description) VALUES
    (gen_random_uuid(), 'System Administrator', 'Full platform access'),
    (gen_random_uuid(), 'HR Manager', 'HR operations and workforce management'),
    (gen_random_uuid(), 'Recruiter', 'Recruitment module access'),
    (gen_random_uuid(), 'Department Manager', 'Team attendance, leave, and performance'),
    (gen_random_uuid(), 'Employee', 'Self-service employee access')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description) VALUES
    ('auth:setup', 'One-time initial administrator bootstrap'),
    ('auth:login', 'Authenticate with credentials'),
    ('auth:refresh', 'Refresh access token'),
    ('auth:logout', 'Revoke session'),
    ('auth:password:reset', 'Forgot/reset password flow'),
    ('auth:me:read', 'Read current authenticated user'),
    ('user:create', 'Create user accounts'),
    ('user:read', 'List and view users'),
    ('user:update', 'Update user accounts'),
    ('user:deactivate', 'Deactivate user accounts'),
    ('user:role:assign', 'Assign roles to users'),
    ('user:role:remove', 'Remove roles from users'),
    ('role:read', 'List roles'),
    ('role:permission:read', 'List permissions for a role'),
    ('permission:read', 'List canonical permissions'),
    ('employee:create', 'Create employee records'),
    ('employee:read', 'Read employee records'),
    ('employee:update', 'Update employee records'),
    ('employee:deactivate', 'Deactivate employee records'),
    ('department:create', 'Create departments'),
    ('department:read', 'List and view departments'),
    ('department:update', 'Update departments'),
    ('department:delete', 'Delete departments'),
    ('designation:create', 'Create designations'),
    ('designation:read', 'List and view designations'),
    ('designation:update', 'Update designations'),
    ('designation:delete', 'Delete designations'),
    ('employment_status:read', 'List employment statuses'),
    ('attendance_status:read', 'List attendance statuses'),
    ('attendance:checkin', 'Employee check-in'),
    ('attendance:checkout', 'Employee check-out'),
    ('attendance:read', 'View attendance records'),
    ('attendance:report', 'Attendance reports'),
    ('attendance:correction:create', 'Request attendance correction'),
    ('attendance:correction:review', 'Review attendance corrections'),
    ('leave:request:create', 'Submit leave request'),
    ('leave:request:read', 'View leave requests'),
    ('leave:request:approve', 'Approve leave request'),
    ('leave:request:reject', 'Reject leave request'),
    ('leave:request:cancel', 'Cancel leave request'),
    ('leave:balance:read', 'View leave balances'),
    ('job:create', 'Create job postings'),
    ('job:read', 'List and view jobs'),
    ('job:update', 'Update job postings'),
    ('job:publish', 'Publish job postings'),
    ('job:close', 'Close job postings'),
    ('candidate:create', 'Create candidates'),
    ('candidate:read', 'List and view candidates'),
    ('candidate:update', 'Update candidates'),
    ('application:read', 'View candidate applications'),
    ('application:update', 'Update application status'),
    ('application:shortlist', 'Shortlist candidate application'),
    ('application:override', 'Override AI recommendation'),
    ('application:history:read', 'View application status history'),
    ('resume:upload', 'Upload candidate resume'),
    ('ai:analyze', 'Trigger resume analysis'),
    ('ai:read', 'Read resume analysis results'),
    ('interview:create', 'Schedule interview'),
    ('interview:read', 'View interviews'),
    ('interview:update', 'Update interview'),
    ('performance:cycle:create', 'Create performance cycle'),
    ('performance:cycle:read', 'List performance cycles'),
    ('performance:review:create', 'Submit performance review'),
    ('performance:review:read', 'View performance reviews'),
    ('performance:metric:create', 'Define performance metric'),
    ('performance:metric:read', 'List performance metrics'),
    ('performance:feedback:create', 'Add performance feedback'),
    ('notification:read', 'List notifications'),
    ('notification:update', 'Mark notifications read'),
    ('notification:preference:read', 'Read notification preferences'),
    ('notification:preference:update', 'Update notification preferences'),
    ('dashboard:hr', 'HR dashboard'),
    ('dashboard:recruitment', 'Recruitment dashboard'),
    ('dashboard:attendance', 'Attendance dashboard'),
    ('dashboard:performance', 'Performance dashboard'),
    ('dashboard:employee', 'Employee dashboard'),
    ('report:attendance', 'Attendance reporting'),
    ('report:recruitment', 'Recruitment reporting'),
    ('report:performance', 'Performance reporting'),
    ('report:workforce', 'Workforce reporting'),
    ('report:export', 'Export reports'),
    ('audit:read', 'View audit logs')
ON CONFLICT (name) DO NOTHING;

-- System Administrator: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'System Administrator'
ON CONFLICT DO NOTHING;

-- HR Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN (
    'auth:login', 'auth:refresh', 'auth:logout', 'auth:password:reset', 'auth:me:read',
    'employee:create', 'employee:read', 'employee:update', 'employee:deactivate',
    'department:create', 'department:read', 'department:update', 'department:delete',
    'designation:create', 'designation:read', 'designation:update', 'designation:delete',
    'employment_status:read', 'attendance_status:read',
    'attendance:read', 'attendance:report', 'attendance:correction:review',
    'leave:request:read', 'leave:request:approve', 'leave:request:reject', 'leave:balance:read',
    'job:create', 'job:read', 'job:update', 'job:publish', 'job:close',
    'candidate:create', 'candidate:read', 'candidate:update',
    'application:read', 'application:update', 'application:shortlist', 'application:override',
    'application:history:read', 'resume:upload', 'ai:analyze', 'ai:read',
    'interview:create', 'interview:read', 'interview:update',
    'performance:cycle:create', 'performance:cycle:read',
    'performance:review:create', 'performance:review:read',
    'performance:metric:create', 'performance:metric:read', 'performance:feedback:create',
    'notification:read', 'notification:update',
    'notification:preference:read', 'notification:preference:update',
    'dashboard:hr', 'dashboard:recruitment', 'dashboard:attendance', 'dashboard:performance',
    'report:attendance', 'report:recruitment', 'report:performance', 'report:workforce', 'report:export'
)
WHERE r.name = 'HR Manager'
ON CONFLICT DO NOTHING;

-- Recruiter
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN (
    'auth:login', 'auth:refresh', 'auth:logout', 'auth:password:reset', 'auth:me:read',
    'employee:read',
    'employment_status:read', 'attendance_status:read',
    'job:create', 'job:read', 'job:update', 'job:publish', 'job:close',
    'candidate:create', 'candidate:read', 'candidate:update',
    'application:read', 'application:update', 'application:shortlist', 'application:override',
    'application:history:read', 'resume:upload', 'ai:analyze', 'ai:read',
    'interview:create', 'interview:read', 'interview:update',
    'notification:read', 'notification:update',
    'notification:preference:read', 'notification:preference:update',
    'dashboard:recruitment',
    'report:recruitment'
)
WHERE r.name = 'Recruiter'
ON CONFLICT DO NOTHING;

-- Department Manager
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN (
    'auth:login', 'auth:refresh', 'auth:logout', 'auth:password:reset', 'auth:me:read',
    'employee:read',
    'attendance:checkin', 'attendance:checkout', 'attendance:read', 'attendance:report',
    'attendance:correction:create', 'attendance:correction:review',
    'leave:request:create', 'leave:request:read', 'leave:request:approve', 'leave:request:reject',
    'leave:balance:read',
    'performance:review:create', 'performance:review:read', 'performance:feedback:create',
    'notification:read', 'notification:update',
    'notification:preference:read', 'notification:preference:update',
    'dashboard:attendance', 'dashboard:performance', 'dashboard:employee',
    'report:attendance', 'report:performance'
)
WHERE r.name = 'Department Manager'
ON CONFLICT DO NOTHING;

-- Employee
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN (
    'auth:login', 'auth:refresh', 'auth:logout', 'auth:password:reset', 'auth:me:read',
    'employee:read',
    'attendance:checkin', 'attendance:checkout', 'attendance:read',
    'attendance:correction:create',
    'leave:request:create', 'leave:request:read', 'leave:request:cancel', 'leave:balance:read',
    'performance:review:read',
    'notification:read', 'notification:update',
    'notification:preference:read', 'notification:preference:update',
    'dashboard:employee'
)
WHERE r.name = 'Employee'
ON CONFLICT DO NOTHING;
export type RoleSlug =
  | "system_administrator"
  | "hr_manager"
  | "recruiter"
  | "department_manager"
  | "employee";

export interface ErrorDetail {
  field?: string | null;
  message: string;
}

export interface ErrorResponse {
  success: false;
  message: string;
  errors: ErrorDetail[];
}

export interface SuccessResponse<T> {
  success: true;
  message: string;
  data: T;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  roles: RoleSlug[];
  created_at: string;
}

export interface Employee {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone?: string | null;
  department?: { id: string; name: string };
  designation?: { id: string; title: string };
  employment_status?: { id: string; name: string };
  manager?: { id: string; name: string; employee_code: string } | null;
  salary?: number | null;
  join_date: string;
  created_at: string;
  updated_at: string;
}

export interface EmployeeSearchItem {
  id: string;
  full_name: string;
  employee_code: string;
  department: { id: string; name: string };
}

export interface Department {
  id: string;
  name: string;
  description?: string | null;
  employee_count: number;
  created_at: string;
  updated_at: string;
}

export interface Designation {
  id: string;
  title: string;
  description?: string | null;
  employee_count: number;
  created_at: string;
  updated_at: string;
}

export interface EmploymentStatus {
  id: string;
  name: string;
}

export interface EmployeeReportRow {
  employee_id: string;
  employee_code: string;
  full_name: string;
  email: string;
  department_name: string;
  designation_title: string;
  employment_status: string;
  join_date: string;
}

export interface Job {
  id: string;
  title: string;
  department_id?: string | null;
  department_name?: string | null;
  status: "draft" | "published" | "closed";
  description: string;
  skills: string[];
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export type ApplicationStatus =
  | "applied"
  | "screening"
  | "shortlisted"
  | "interview_scheduled"
  | "interviewed"
  | "offered"
  | "rejected"
  | "withdrawn";

export interface Application {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  job_id: string;
  job_title: string;
  application_status: ApplicationStatus;
  ai_score?: number | null;
  ranking?: number | null;
  recommendation?: string | null;
  recruiter_override: boolean;
  created_at: string;
}

export interface JobCandidateRow {
  application_id: string;
  candidate_id: string;
  full_name: string;
  email: string;
  application_status: ApplicationStatus;
  ai_score?: number | null;
  ranking?: number | null;
  recommendation?: string | null;
  matched_skills?: string[] | null;
  missing_skills?: string[] | null;
  recruiter_override?: boolean;
  score?: number | null;
}

export interface CandidateNote {
  id: string;
  candidate_id: string;
  note: string;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
}

export interface CandidateTimelineItem {
  old_status?: string | null;
  new_status: string;
  changed_at: string;
  changed_by?: string | null;
  changed_by_name?: string | null;
}

export interface ResumeAnalysis {
  id: string;
  candidate_id: string;
  application_id: string;
  analysis_status: string;
  extracted_skills: string[] | Record<string, unknown>;
  matched_skills: string[] | Record<string, unknown>;
  missing_skills: string[] | Record<string, unknown>;
  score: number;
  recommendation?: string | null;
  explanation?: Record<string, unknown> | string | null;
  created_at: string;
}

export interface ScreeningResult {
  analysis_id: string;
  application_id: string;
  candidate_id: string;
  job_id: string;
  analysis_status: string;
  score: number;
  ai_score?: number | null;
  recommendation?: string | null;
  matched_skills: string[];
  missing_skills: string[];
  extracted_skills: string[];
  explanation: Record<string, unknown>;
}

export interface Interview {
  id: string;
  application_id: string;
  candidate_name: string;
  job_title: string;
  scheduled_at: string;
  interviewer_id?: string | null;
  interviewer_name?: string | null;
  status: "scheduled" | "completed" | "cancelled" | "no_show";
  notes?: string | null;
  created_at?: string | null;
  updated_at: string;
}

export interface RecruitmentReportRow {
  job_id: string;
  job_title: string;
  total_candidates: number;
  shortlisted: number;
  rejected: number;
  pending: number;
  average_ai_score?: number | null;
}

export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  current_status?: string | null;
  created_at: string;
}

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  attendance_date: string;
  check_in_time?: string | null;
  check_out_time?: string | null;
  work_duration_minutes?: number | null;
  attendance_status_id: string;
  status_name: string;
  created_at?: string;
}

export interface MonthlyAttendanceSummary {
  employee_id: string;
  year: number;
  month: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  half_days: number;
  total_working_days: number;
  total_hours: number;
}

export interface DailyAttendanceEmployee {
  employee_id: string;
  employee_code: string;
  full_name: string;
  department_name: string;
  status_name: string;
  check_in_time?: string | null;
  check_out_time?: string | null;
  record_id?: string | null;
}

export interface DailyAttendance {
  date: string;
  present_count: number;
  absent_count: number;
  late_count: number;
  employees: DailyAttendanceEmployee[];
}

export interface AttendanceCorrection {
  id: string;
  attendance_record_id: string;
  requested_by: string;
  reason: string;
  correction_status: string;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface AttendanceReportRow {
  record_id: string;
  employee_id: string;
  employee_code: string;
  full_name: string;
  department_name: string;
  attendance_date: string;
  status_name: string;
  check_in_time?: string | null;
  check_out_time?: string | null;
  work_duration_minutes?: number | null;
}

export interface AttendanceStatus {
  id: string;
  name: string;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_name: string;
  leave_type_id: string;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  status: "pending" | "approved" | "rejected" | "cancelled";
  reason?: string | null;
  created_at: string;
  approver_name?: string | null;
  approval_level?: number | null;
  approval_remarks?: string | null;
}

export interface LeaveBalanceItem {
  leave_type_id: string;
  leave_type: string;
  annual_allocation: number;
  current_balance: number;
}

export interface LeaveBalanceResponse {
  employee_id: string;
  balances: LeaveBalanceItem[];
}

export interface InitializedBalanceRecord {
  id: string;
  employee_id: string;
  leave_type_id: string;
  leave_type_name: string;
  balance: number;
}

export interface InitializeLeaveBalanceResponse {
  created: InitializedBalanceRecord[];
}

export interface LeaveType {
  id: string;
  name: string;
  annual_allocation: number;
}

export interface EmployeeSummary {
  id: string;
  employee_code: string;
  full_name: string;
  department_name?: string | null;
}

export type PerformanceCycleStatus = "draft" | "active" | "completed";

export interface PerformanceCycle {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: PerformanceCycleStatus;
}

export interface PerformanceMetric {
  id: string;
  name: string;
  description?: string | null;
}

export interface MetricScore {
  id: string;
  review_id: string;
  metric_id: string;
  metric_name: string;
  score: number;
}

export interface PerformanceFeedback {
  id: string;
  review_id: string;
  feedback_text: string;
  created_by: string;
  author?: EmployeeSummary | null;
  created_at: string;
}

export interface EmployeePerformanceSummary {
  review_id: string;
  cycle: PerformanceCycle;
  employee: EmployeeSummary;
  reviewer: EmployeeSummary;
  rating: number;
  average_metric_score?: number | null;
  metric_scores: MetricScore[];
  feedback_entries: PerformanceFeedback[];
  feedback_count: number;
}

export interface PerformanceReview {
  id: string;
  cycle: PerformanceCycle;
  employee: EmployeeSummary;
  reviewer: EmployeeSummary;
  rating: number;
  comments?: string | null;
  created_at: string;
  average_metric_score?: number | null;
  metric_scores: MetricScore[];
  feedback_entries: PerformanceFeedback[];
}

export interface DepartmentAverageRating {
  department_id: string;
  department_name: string;
  average_rating?: number | null;
}

export interface TopPerformer {
  employee: EmployeeSummary;
  average_rating?: number | null;
}

export interface ScoreDistributionBucket {
  bucket: string;
  count: number;
  percentage: number;
}

export interface PerformanceReportEmployeeRow {
  employee: EmployeeSummary;
  average_rating?: number | null;
  average_score?: number | null;
}

export interface PerformanceReport {
  average_rating_per_department: DepartmentAverageRating[];
  top_performers: TopPerformer[];
  score_distribution: ScoreDistributionBucket[];
  employees: PerformanceReportEmployeeRow[];
  pagination: PaginationMeta;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface AuditLog {
  id: string;
  actor_user_id?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  ip_address: string;
  before_state?: Record<string, unknown> | null;
  after_state?: Record<string, unknown> | null;
  created_at: string;
}

export interface HRDashboardResponse {
  total_employees: number;
  active_employees: number;
  new_hires_last_30_days: number;
  departments_count: number;
  attendance_rate_today: number;
  pending_leave_requests_count: number;
  open_job_postings: number;
  candidates_this_month: number;
}

export interface RecruitmentTopCandidate {
  application_id: string;
  candidate_id: string;
  full_name: string;
  email: string;
  ai_score: number;
}

export interface RecruitmentJobSummary {
  job_id: string;
  title: string;
  open_applications: number;
  shortlisted_applications: number;
  rejected_applications: number;
  pending_screening_applications: number;
  average_ai_score?: number | null;
  top_candidates: RecruitmentTopCandidate[];
}

export interface RecruitmentDashboardResponse {
  open_jobs: number;
  total_candidates: number;
  shortlisted_candidates: number;
  rejected_candidates: number;
  pending_screening_candidates: number;
  average_ai_score?: number | null;
  jobs: RecruitmentJobSummary[];
}

export interface AttendanceTrendPoint {
  date: string;
  present_count: number;
  absent_count: number;
}

export interface AttendanceTopAbsentDepartment {
  department_id: string;
  department_name: string;
  absent_count: number;
}

export interface AttendanceDashboardResponse {
  today_date: string;
  present_count: number;
  absent_count: number;
  late_count: number;
  attendance_rate_today: number;
  weekly_trend: AttendanceTrendPoint[];
  top_absent_departments: AttendanceTopAbsentDepartment[];
}

export interface PerformanceTopPerformerDashboardRow {
  employee_id: string;
  employee_code: string;
  full_name: string;
  department_name?: string | null;
  rating: number;
}

export interface PerformanceDashboardResponse {
  active_cycle_id?: string | null;
  active_cycle_name?: string | null;
  average_rating?: number | null;
  top_performers: PerformanceTopPerformerDashboardRow[];
  employees_without_review: number;
}

export interface EmployeeMonthlyAttendanceSummaryDashboardRow {
  present_days: number;
  total_hours: number;
}

export interface EmployeeLeaveBalanceDashboardRow {
  leave_type_id: string;
  leave_type_name: string;
  balance: number;
}

export interface EmployeeDashboardResponse {
  attendance_this_month?: EmployeeMonthlyAttendanceSummaryDashboardRow | null;
  leave_balances: EmployeeLeaveBalanceDashboardRow[];
  latest_performance_rating?: number | null;
  unread_notifications_count: number;
  upcoming_interviews: Array<Record<string, unknown>>;
}

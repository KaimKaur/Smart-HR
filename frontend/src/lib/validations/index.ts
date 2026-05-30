import { z } from "zod";

export const loginSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export const forgotPasswordSchema = z.object({
  email: z.email("Enter a valid email address"),
});

export const resetPasswordSchema = z
  .object({
    token: z.string().min(1, "Missing reset token"),
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(8, "Password must be at least 8 characters"),
  })
  .refine((value) => value.new_password === value.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export const createEmployeeSchema = z.object({
  employee_code: z.string().min(1).max(50),
  first_name: z.string().min(1).max(100),
  last_name: z.string().min(1).max(100),
  email: z.email(),
  phone: z.string().max(30).optional(),
  department_id: z.uuid(),
  designation_id: z.uuid(),
  employment_status_id: z.uuid(),
  manager_id: z.uuid().optional(),
  salary: z.number().nonnegative().optional(),
  join_date: z.iso.date(),
});

export const updateEmployeeSchema = createEmployeeSchema.partial();

export const departmentSchema = z.object({
  name: z.string().min(1).max(150),
  description: z.string().optional(),
});

export const designationSchema = z.object({
  title: z.string().min(1).max(150),
  description: z.string().optional(),
});

export const leaveRequestSchema = z
  .object({
    leave_type_id: z.uuid(),
    start_date: z.iso.date(),
    end_date: z.iso.date(),
    reason: z.string().min(1).max(5000).optional(),
  })
  .refine((value) => value.end_date >= value.start_date, {
    message: "end_date must be on or after start_date",
    path: ["end_date"],
  });

export const createJobSchema = z.object({
  title: z.string().min(1).max(200),
  department_id: z.uuid().optional(),
  description: z.string().min(10, "Description must be at least 10 characters"),
  skills: z.array(z.string().min(1)),
});

export const updateJobSchema = createJobSchema.partial();

export const createCandidateSchema = z.object({
  full_name: z.string().min(1).max(200),
  email: z.email(),
  phone: z.string().max(50).optional(),
  job_id: z.uuid().optional(),
});

export const scheduleInterviewSchema = z.object({
  application_id: z.uuid(),
  scheduled_at: z.string().min(1),
  interviewer_id: z.uuid().optional(),
  notes: z.string().max(5000).optional(),
});

export const createNoteSchema = z.object({
  note: z.string().min(1).max(5000),
});

export const correctionRequestSchema = z.object({
  reason: z.string().min(10, "Reason must be at least 10 characters"),
});

export const reviewCorrectionSchema = z.object({
  status: z.enum(["approved", "rejected"]),
  remarks: z.string().optional(),
});

export const performanceCycleSchema = z
  .object({
    name: z.string().min(1).max(150),
    start_date: z.iso.date(),
    end_date: z.iso.date(),
  })
  .refine((value) => value.end_date >= value.start_date, {
    message: "end_date must be on or after start_date",
    path: ["end_date"],
  });

export const performanceReviewSchema = z.object({
  cycle_id: z.uuid(),
  employee_id: z.uuid(),
  rating: z.number().min(1).max(5),
  comments: z.string().max(5000).optional(),
});

export const performanceMetricSchema = z.object({
  name: z.string().min(1).max(150),
  description: z.string().max(5000).optional(),
});

export const performanceFeedbackSchema = z.object({
  feedback_text: z.string().min(1).max(5000),
});

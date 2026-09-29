import { z } from "zod";

export const LoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
});
export type LoginResponse = z.infer<typeof LoginResponseSchema>;

export const CriterionSchema = z.object({
  id: z.string().min(1, "ID is required"),
  description: z.string().min(1, "Description is required"),
  weight: z.number().positive("Weight must be positive"),
  depends_on: z.array(z.string()),
});
export type Criterion = z.infer<typeof CriterionSchema>;

export const RubricSchema = z.object({
  id: z.string(),
  title: z.string().min(1, "Title is required"),
  criteria: z.array(CriterionSchema),
});
export type Rubric = z.infer<typeof RubricSchema>;

export const CreateRubricRequestSchema = z.object({
  title: z.string().min(1, "Title is required"),
  criteria: z.array(CriterionSchema),
});
export type CreateRubricRequest = z.infer<typeof CreateRubricRequestSchema>;

export const JobSchema = z.object({
  job_id: z.string(),
  status: z.string(),
  error: z.string().nullable(),
  doc_id: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  events: z.array(z.any()),
});
export type Job = z.infer<typeof JobSchema>;

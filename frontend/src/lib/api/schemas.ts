import { z } from "zod";

export const LoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
});
export type LoginResponse = z.infer<typeof LoginResponseSchema>;

export const RubricSchema = z.object({
  id: z.string(),
  title: z.string(),
  criteria: z.array(z.any()),
});
export type Rubric = z.infer<typeof RubricSchema>;

export const JobSchema = z.object({
  job_id: z.string(),
  status: z.string(),
  error: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  events: z.array(z.any()),
});
export type Job = z.infer<typeof JobSchema>;

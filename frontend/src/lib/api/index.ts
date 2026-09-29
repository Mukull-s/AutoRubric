import { apiClient } from "./client";
import { LoginResponse, Rubric, Job } from "./schemas";

export async function login(data: any): Promise<LoginResponse> {
  return apiClient<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getRubrics(): Promise<Rubric[]> {
  return apiClient<Rubric[]>("/rubrics");
}

export async function getJob(jobId: string): Promise<Job> {
  return apiClient<Job>(`/jobs/${jobId}`);
}

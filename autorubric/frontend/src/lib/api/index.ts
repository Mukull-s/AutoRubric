import { apiClient } from "./client";
import { LoginResponse, Rubric, Job, CreateRubricRequest } from "./schemas";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function login(data: Record<string, unknown>): Promise<LoginResponse> {
  return apiClient<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getRubrics(): Promise<Rubric[]> {
  return apiClient<Rubric[]>("/rubrics");
}

export async function getRubric(id: string): Promise<Rubric> {
  return apiClient<Rubric>(`/rubrics/${id}`);
}

export async function createRubric(data: CreateRubricRequest): Promise<Rubric> {
  return apiClient<Rubric>("/rubrics", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getJob(jobId: string): Promise<Job> {
  return apiClient<Job>(`/jobs/${jobId}`);
}

export async function submitSingle(formData: FormData): Promise<{ job_id: string, status: string }> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const res = await fetch(`${API_URL}/submissions`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitBatch(formData: FormData): Promise<{ cohort_id: string, jobs: { job_id: string, file_name: string }[] }> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const res = await fetch(`${API_URL}/submissions/batch`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCohort(id: string): Promise<unknown> {
  return apiClient<unknown>(`/cohorts/${id}`);
}

export async function retryJob(jobId: string): Promise<unknown> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const res = await fetch(`${API_URL}/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getResult(docId: string): Promise<unknown> {
  return apiClient<unknown>(`/results/${docId}`);
}

export async function verifyResult(docId: string): Promise<unknown> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const res = await fetch(`${API_URL}/results/${docId}/verify`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getResultPdf(docId: string): Promise<Blob> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const res = await fetch(`${API_URL}/results/${docId}/pdf`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch PDF');
  }
  
  return res.blob();
}

export async function getCollusion(cohortId: string): Promise<unknown> {
  return apiClient<unknown>(`/cohorts/${cohortId}/collusion`);
}

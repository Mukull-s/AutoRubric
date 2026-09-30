import { apiClient } from "./client";
import { LoginResponse, Rubric, Job } from "./schemas";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function login(data: any): Promise<LoginResponse> {
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

export async function createRubric(data: any): Promise<Rubric> {
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

export async function getCohort(id: string): Promise<any> {
  return apiClient<any>(`/cohorts/${id}`);
}

export async function retryJob(jobId: string): Promise<any> {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  const res = await fetch(`${API_URL}/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getResult(docId: string): Promise<any> {
  return apiClient<any>(`/results/${docId}`);
}

export async function verifyResult(docId: string): Promise<any> {
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

export async function getCollusion(cohortId: string): Promise<any> {
  return apiClient<any>(`/cohort/${cohortId}/collusion`);
}

import { apiClient } from "./client";
import { LoginResponse, Rubric, Job, CreateRubricRequest } from "./schemas";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '');


export async function login(data: Record<string, unknown>): Promise<LoginResponse> {
  return apiClient<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function register(data: Record<string, unknown>): Promise<LoginResponse> {
  return apiClient<LoginResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMe(): Promise<unknown> {
  return apiClient<unknown>("/auth/me");
}

export async function getRubrics(): Promise<Rubric[]> {
  return apiClient<Rubric[]>("/rubrics");
}

export async function getRubric(id: string): Promise<Rubric> {
  return apiClient<Rubric>(`/rubrics/${id}`);
}

export async function createRubric(data: CreateRubricRequest): Promise<Rubric> {
  const totalWeight = data.criteria.reduce((sum, c) => sum + (c.weight || 0), 0);
  const fullPayload = {
    id: `r-${Date.now().toString(36)}`,
    title: data.title,
    criteria: data.criteria,
    credit_map: {
      FULL_CREDIT: 1.0,
      PARTIAL_CREDIT: 0.5,
      NO_CREDIT: 0.0,
      MISCONCEPTION: 0.0,
    },
    max_score: totalWeight,
  };
  return apiClient<Rubric>("/rubrics", {
    method: "POST",
    body: JSON.stringify(fullPayload),
  });
}

export async function deleteRubric(id: string): Promise<{ status: string, message: string }> {
  return apiClient<{ status: string, message: string }>(`/rubrics/${id}`, {
    method: "DELETE",
  });
}

export async function getJob(jobId: string): Promise<Job> {
  return apiClient<Job>(`/jobs/${jobId}`);
}

export async function submitSingle(formData: FormData): Promise<{ job_id: string, status: string }> {
  const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || sessionStorage.getItem('token')) : null;
  if (!token) {
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Please sign in before submitting assignments.');
  }
  const res = await fetch(`${API_URL}/submissions`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    const errorText = await res.text();
    let msg = errorText;
    try {
      const parsed = JSON.parse(errorText);
      msg = parsed.detail || parsed.message || errorText;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function submitBatch(formData: FormData): Promise<{ cohort_id: string, jobs: { job_id: string, file_name: string }[] }> {
  const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || sessionStorage.getItem('token')) : null;
  if (!token) {
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Please sign in before submitting assignments.');
  }
  const res = await fetch(`${API_URL}/submissions/batch`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    const errorText = await res.text();
    let msg = errorText;
    try {
      const parsed = JSON.parse(errorText);
      msg = parsed.detail || parsed.message || errorText;
    } catch {}
    throw new Error(msg);
  }
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

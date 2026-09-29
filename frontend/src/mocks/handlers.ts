import { http, HttpResponse, delay } from 'msw'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const handlers = [
  http.post(`${API_URL}/auth/login`, async () => {
    await delay(500);
    return HttpResponse.json({
      access_token: "fake-super-secret-token",
      token_type: "bearer"
    })
  }),

  http.get(`${API_URL}/rubrics`, async () => {
    return HttpResponse.json([
      { id: "r1", title: "Test Rubric", criteria: [] }
    ])
  }),

  http.post(`${API_URL}/submissions`, async () => {
    await delay(1000);
    return HttpResponse.json({
      doc_id: "doc123",
      job_id: "job123"
    })
  }),

  http.post(`${API_URL}/submissions/batch`, async () => {
    await delay(1000);
    return HttpResponse.json([
      { doc_id: "doc123", job_id: "job123", success: true }
    ])
  }),

  http.get(`${API_URL}/jobs/:id`, async ({ params }) => {
    return HttpResponse.json({
      job_id: params.id,
      status: "DONE", // we will add a way to simulate later
      error: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      events: []
    })
  }),
]

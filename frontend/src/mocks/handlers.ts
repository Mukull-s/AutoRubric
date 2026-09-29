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

  http.post(`${API_URL}/rubrics`, async ({ request }) => {
    const data = await request.json() as any;
    return HttpResponse.json({
      id: "r" + Math.floor(Math.random() * 1000),
      title: data.title,
      criteria: data.criteria,
      credit_map: { FULL_CREDIT: 1.0, PARTIAL_CREDIT: 0.5, NO_CREDIT: 0.0, MISCONCEPTION: 0.0 },
      max_score: data.criteria.reduce((sum: number, c: any) => sum + c.weight, 0)
    });
  }),

  http.get(`${API_URL}/rubrics/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      title: "Test Rubric",
      criteria: [
        { id: "c1", description: "First criteria", weight: 1, depends_on: [] },
        { id: "c2", description: "Second criteria", weight: 2, depends_on: ["c1"] },
      ],
      credit_map: { FULL_CREDIT: 1.0, PARTIAL_CREDIT: 0.5, NO_CREDIT: 0.0, MISCONCEPTION: 0.0 },
      max_score: 3.0
    });
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
    // Simulate a job moving through statuses
    const statuses = ['QUEUED', 'EXTRACTING', 'EVALUATING', 'AUDITING', 'SCORING', 'DONE'];
    const timeSinceStart = Date.now() % 30000; // loop every 30s for demo
    const statusIndex = Math.min(Math.floor(timeSinceStart / 5000), statuses.length - 1);
    
    let status = statuses[statusIndex];
    let doc_id = undefined;
    if (status === 'DONE') doc_id = "doc-" + params.id;
    
    return HttpResponse.json({
      job_id: params.id,
      status: status,
      error: null,
      doc_id: doc_id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
  }),

  http.get(`${API_URL}/cohorts/:id`, async ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: "Mock Cohort",
      jobs: [
        { job_id: "j1", status: "DONE", file_name: "submission1.pdf", doc_id: "doc-j1" },
        { job_id: "j2", status: "EVALUATING", file_name: "submission2.pdf" },
        { job_id: "j3", status: "FAILED", error: "Extraction failed", file_name: "submission3.pdf" },
        { job_id: "j4", status: "NEEDS_REVIEW", file_name: "submission4.pdf", doc_id: "doc-j4" },
      ]
    });
  }),

  http.get(`${API_URL}/results/:doc_id`, async ({ params }) => {
    return HttpResponse.json({
      doc_id: params.doc_id,
      rubric_id: "r1",
      per_criterion: [
        {
          criterion_id: "c1",
          label: "FULL_CREDIT",
          credit: 1.0,
          marks: 2.0,
          evidence_bboxes: [{"x": 10.5, "y": 20.0, "w": 100.0, "h": 12.0, "page": 1}],
          trusted: true,
          flags: []
        },
        {
          criterion_id: "c2",
          label: "PARTIAL_CREDIT",
          credit: 0.5,
          marks: 1.0,
          evidence_bboxes: [{"x": 50, "y": 50, "w": 50, "h": 50, "page": 1}],
          trusted: false,
          flags: [{ code: "HIDDEN_TEXT", reason: "Found invisible text" }]
        }
      ],
      total: 3.0,
      max_total: 4.0,
      needs_review: true,
      review_reasons: ["Untrusted classification in c2"]
    });
  }),

  http.post(`${API_URL}/results/:doc_id/verify`, async () => {
    return HttpResponse.json({
      match: true,
      differences: null
    });
  }),
]

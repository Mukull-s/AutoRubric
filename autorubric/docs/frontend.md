# Frontend Architecture & Issues

## Mismatches between mocks and reality
- **Missing response schemas in OpenAPI:** Endpoints like `GET /results/{doc_id}`, `GET /jobs/{job_id}`, and `GET /cohorts/{id}` return `unknown` in the OpenAPI schema because they lack explicit response models in the FastAPI router decorators. We generated types via `openapi-typescript` but they are mostly `unknown` for GET requests.
- **Action for P1:** Please add `response_model` definitions to all endpoints in `autorubric/backend/src/autorubric/api/routers/` (especially jobs, submissions, and results) so the frontend can strictly type the responses. Currently using hand-written schemas as a fallback.

## Missing Endpoints
- **GET /results/{doc_id}/propositions**: The critic needs to display proposition text instead of just IDs, but this endpoint is still not available.
- **Action for P1:** Please implement the proposals in `docs/contract-change-proposals.md` and expose propositions in the results payload.

## State and Data Flow
- We use TanStack Query for data fetching and polling (e.g. for job status).
- Auth token is stored in memory and `sessionStorage` fallback (to persist across reloads). Wait, this is a trade-off since it's vulnerable to XSS compared to HttpOnly cookies, but it allows for easier integration with the generic fetch wrapper for now.
- `NEXT_PUBLIC_USE_MOCKS` controls whether `MSW` mock service worker starts. For day 3, we set `NEXT_PUBLIC_USE_MOCKS=false` to use the real API.

## How to run tests
- `npm run test` for Vitest component tests.
- `npx playwright test` for E2E tests.

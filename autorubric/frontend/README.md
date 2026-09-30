# AutoRubric Frontend (Module 5)

**Owner:** P5

This is the Next.js App Router dashboard for AutoRubric, providing functionality to upload submissions, track jobs, and review results with annotated PDFs.

## Environment Variables
- `NEXT_PUBLIC_API_URL`: The URL of the backend API (default: `http://localhost:8000`).
- `NEXT_PUBLIC_USE_MOCKS`: Set to `true` to use MSW mocks, or `false` to hit the real API.

## How to run
1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the development server (runs with MSW mocks by default if `NEXT_PUBLIC_USE_MOCKS=true`):
   ```bash
   npm run dev
   ```
3. Build for production:
   ```bash
   npm run build
   ```
4. Run tests:
   ```bash
   npm run test
   ```

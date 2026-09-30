import { test } from '@playwright/test';

test('capture screenshots', async ({ page }) => {
  // Start mock server in dev mode if NEXT_PUBLIC_USE_MOCKS is true
  // For screenshots, we assume the server is running on http://localhost:3000

  // 1. Login
  await page.goto('http://localhost:3000/login');
  await page.screenshot({ path: '../docs/screenshots/1-login.png' });
  
  // Login to proceed
  await page.fill('input[type="email"]', 'admin@example.com');
  await page.fill('input[type="password"]', 'admin');
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:3000/');

  // 2. Rubric Builder
  await page.goto('http://localhost:3000/rubrics/new');
  await page.screenshot({ path: '../docs/screenshots/2-rubric-builder.png' });

  // 3. Upload
  await page.goto('http://localhost:3000/upload');
  await page.screenshot({ path: '../docs/screenshots/3-upload.png' });

  // 4. Cohort Progress
  // Assuming cohort ID 'c1' exists in mock data
  await page.goto('http://localhost:3000/cohorts/c1');
  await page.screenshot({ path: '../docs/screenshots/4-cohort-progress.png' });

  // 5. Result Page & 6. Needs-Review Result & 7. Annotated PDF
  // Assuming result ID 'd1' exists in mock data (benign)
  await page.goto('http://localhost:3000/results/d1');
  await page.screenshot({ path: '../docs/screenshots/5-result-page.png', fullPage: true });

  // Assuming result ID 'd2' is needs-review
  await page.goto('http://localhost:3000/results/d2');
  await page.screenshot({ path: '../docs/screenshots/6-needs-review.png', fullPage: true });

  // (The PDF is embedded in the result page, so the above covers 7 as well)

  // 8. Collusion List & 9. Heatmap
  await page.goto('http://localhost:3000/cohorts/c1/collusion');
  await page.screenshot({ path: '../docs/screenshots/8-9-collusion-heatmap.png', fullPage: true });
});

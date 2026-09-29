import { test, expect } from '@playwright/test';

test.describe('End-to-End Flow', () => {
  test('upload -> cohort polling -> results -> collusion', async ({ page }) => {
    // 1. Mock API Responses
    await page.route('**/rubrics', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'r1', title: 'Biology Basics', max_score: 10, criteria: [] }
        ])
      });
    });

    await page.route('**/submissions/batch', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ cohort_id: 'c1', jobs: [{ job_id: 'j1', file_name: 'test.pdf' }] })
      });
    });

    await page.route('**/cohorts/c1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'c1',
          name: 'Batch Upload',
          jobs: [{ job_id: 'j1', file_name: 'test.pdf', status: 'DONE', doc_id: 'd1' }]
        })
      });
    });

    await page.route('**/results/d1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          doc_id: 'd1',
          rubric_id: 'r1',
          total: 8,
          max_total: 10,
          per_criterion: [
            { criterion_id: 'c1', marks: 2, credit: 1.0, label: 'FULL_CREDIT', trusted: true }
          ]
        })
      });
    });

    await page.route('**/results/d1/pdf', async route => {
      // Mock an empty PDF blob
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from('%PDF-1.4\n%EOF\n')
      });
    });

    await page.route('**/cohort/c1/collusion', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          cohort_id: 'c1',
          doc_pairs: [
            { a: 'd1', b: 'd2', similarity: 0.95, matching_props: ['test::test'] }
          ]
        })
      });
    });

    // 2. Start at Dashboard
    await page.goto('http://localhost:3000');
    await expect(page.locator('text=Biology Basics')).toBeVisible();

    // 3. Navigate to Upload
    await page.click('text=Upload Submission');
    await expect(page.locator('text=Submit Assignment')).toBeVisible();

    // 4. Submit Batch
    // Create a dummy file buffer
    const fileBuffer = Buffer.from('dummy pdf content');
    await page.setInputFiles('input[type="file"]', {
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: fileBuffer
    });
    await page.selectOption('select', 'r1');
    await page.click('button:has-text("Submit as Batch")');

    // 5. Check Cohort page
    await expect(page.locator('text=Cohort: Batch Upload')).toBeVisible();
    await expect(page.locator('text=test.pdf')).toBeVisible();
    await expect(page.locator('text=DONE')).toBeVisible();
    
    // Save screenshot of cohort
    await page.screenshot({ path: '../docs/screenshots/cohort.png' });

    // 6. Navigate to Results
    await page.click('text=View Result');
    await expect(page.locator('text=Result for d1')).toBeVisible();
    await expect(page.locator('text=Annotated PDF')).toBeVisible();
    
    // Save screenshot of result
    await page.screenshot({ path: '../docs/screenshots/result.png', fullPage: true });

    // 7. Go back to Cohort and check Collusion
    await page.goto('http://localhost:3000/cohorts/c1');
    await page.click('text=View Collusion Report');
    await expect(page.locator('text=Collusion Report for Cohort c1')).toBeVisible();
    await expect(page.locator('text=Pair Similarity: 95.0%')).toBeVisible();
    
    // Save screenshot of collusion
    await page.screenshot({ path: '../docs/screenshots/collusion.png' });
  });
});

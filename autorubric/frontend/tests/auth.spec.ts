import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  const testUser = {
    email: `test_user_${Date.now()}@example.com`,
    password: 'Password123!'
  };

  test('register a new user, land on dashboard, log out, log in again', async ({ page }) => {
    // 1. Register a new user
    await page.goto('/register');
    
    // Fill out registration form
    await page.fill('input[name="full_name"]', 'Test User');
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirm_password"]', testUser.password);
    
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Dashboard').first()).toBeVisible();

    // 2. Log out
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL('/login');

    // 3. Log in again
    await page.fill('input[placeholder="name@example.com"]', testUser.email);
    await page.fill('input[type="password"]', testUser.password);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard again
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Dashboard').first()).toBeVisible();
  });
});

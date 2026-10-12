import { expect, test } from '@playwright/test';

test('a signed-out visitor is sent to login from a protected page', async ({ page }) => {
  await page.route('**/api/v1/admin/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Not authenticated' }),
    }),
  );

  await page.goto('/reports/');

  await expect(page).toHaveURL(/\/login\/?$/);
  await expect(page.getByText('Welcome back')).toBeVisible();
});

test('a failed login shows the API error without opening the portal', async ({ page }) => {
  await page.route('**/api/v1/admin/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Not authenticated' }),
    }),
  );
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Invalid credentials' }),
    }),
  );

  await page.goto('/login/');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('incorrect-password');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByText('Invalid credentials')).toBeVisible();
  await expect(page).toHaveURL(/\/login\/?$/);
});

test('a patient account cannot enter the administration portal', async ({ page }) => {
  let loginSucceeded = false;
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) {
      loginSucceeded = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: 'synthetic-test-token' }),
      });
    }
    if (path.endsWith('/admin/me')) {
      return route.fulfill({
        status: loginSucceeded ? 200 : 401,
        contentType: 'application/json',
        body: JSON.stringify(loginSucceeded
          ? { id: 'test-patient', email: 'patient@example.com', role: 'patient' }
          : { detail: 'Not authenticated' }),
      });
    }
    return route.abort();
  });

  await page.goto('/login/');
  await page.getByLabel('Email').fill('patient@example.com');
  await page.getByLabel('Password').fill('synthetic-password');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByText('Unauthorized. Only administrators can access this portal.')).toBeVisible();
  await expect(page).toHaveURL(/\/login\/?$/);
});

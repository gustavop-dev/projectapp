/**
 * E2E tests for platform collection accounts (list, project list, detail).
 *
 * @flow:platform-collection-accounts-list
 * @flow:platform-collection-account-detail
 * @flow:platform-project-collection-accounts
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PLATFORM_COLLECTION_ACCOUNTS_LIST,
  PLATFORM_COLLECTION_ACCOUNT_DETAIL,
  PLATFORM_PROJECT_COLLECTION_ACCOUNTS,
} from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockRow = {
  id: 42,
  title: 'Invoice Q1',
  public_number: 'CA-2026-001',
  commercial_status: 'issued',
  is_overdue: false,
  currency: 'COP',
  total: '100000.00',
  due_date: '2026-04-15',
};

const mockDetail = {
  id: 42,
  title: 'Invoice Q1',
  public_number: 'CA-2026-001',
  commercial_status: 'issued',
  is_overdue: false,
  currency: 'COP',
  subtotal: '84000.00',
  tax_total: '16000.00',
  total: '100000.00',
  items: [
    {
      id: 1,
      description: 'Development sprint',
      quantity: 1,
      unit_price: '84000.00',
      line_total: '84000.00',
    },
  ],
  collection_account: null,
};

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });

function setupCollectionAccountsMocks(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    if (apiPath === 'accounts/collection-accounts/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockRow]) };
    }
    if (apiPath === 'accounts/projects/1/collection-accounts/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockRow]) };
    }
    if (apiPath === 'accounts/collection-accounts/42/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDetail) };
    }
    if (apiPath === 'accounts/collection-accounts/42/pdf/' && method === 'GET') {
      return { status: 200, contentType: 'application/pdf', body: '%PDF-e2e-collection-account' };
    }
    return null;
  });
}

test.describe('Platform collection accounts', () => {
  test.setTimeout(60_000);

  test('client sees global list with Open link to detail', {
    tag: [...PLATFORM_COLLECTION_ACCOUNTS_LIST, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupCollectionAccountsMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/collection-accounts', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /my collection accounts/i })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText('Invoice Q1')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Open' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /new collection account/i })).not.toBeVisible();
  });

  test('admin sees global list and new collection account control', {
    tag: [...PLATFORM_COLLECTION_ACCOUNTS_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupCollectionAccountsMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/collection-accounts', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /^collection accounts$/i })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole('button', { name: /new collection account/i })).toBeVisible();
  });

  test('user sees project-scoped collection account list', {
    tag: [...PLATFORM_PROJECT_COLLECTION_ACCOUNTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupCollectionAccountsMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/collection-accounts', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /^collection accounts$/i })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText('Invoice Q1')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Open' })).toBeVisible();
  });

  test('detail page shows totals and download PDF triggers request', {
    tag: [...PLATFORM_COLLECTION_ACCOUNT_DETAIL, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupCollectionAccountsMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/collection-accounts/42', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Invoice Q1' })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText('Total COP 100000.00')).toBeVisible();
    const pdfWait = page.waitForResponse(
      (res) => res.url().includes('collection-accounts/42/pdf/') && res.status() === 200,
    );
    await page.getByRole('button', { name: /download pdf/i }).click();
    await pdfWait;
  });
});

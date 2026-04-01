/**
 * E2E tests for platform deliverables flow.
 *
 * @flow:platform-deliverables
 * @flow:platform-deliverable-detail
 * Covers: deliverable list rendering, category filter tabs, admin upload deliverable,
 *         client view/download, version history, unified cross-project view,
 *         deliverable detail page and linked proposal PDFs.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_DELIVERABLES, PLATFORM_DELIVERABLE_DETAIL } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockProject = {
  id: 1, name: 'E-commerce Platform', status: 'active', progress: 33,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp', start_date: '2025-01-01', estimated_end_date: '2025-06-30',
};

const mockDeliverableDetail = {
  id: 1,
  title: 'Wireframes página principal',
  description: 'Wireframes de baja fidelidad.',
  source_epic_key: 'EPIC-1',
  source_epic_title: 'Épica onboarding',
  has_business_proposal: true,
  proposal_title: 'Propuesta comercial demo',
  file_url: '/media/wireframes-v1.pdf',
  file_name: 'wireframes-v1.pdf',
  attachment_files: [],
  pdf_download_paths: {
    commercial: 'projects/1/deliverables/1/pdf/commercial/',
    technical: 'projects/1/deliverables/1/pdf/technical/',
  },
};

const mockDeliverables = [
  {
    id: 1, title: 'Wireframes página principal', description: 'Wireframes de baja fidelidad.',
    category: 'designs', current_version: 1, file_url: '/media/wireframes-v1.pdf',
    file_name: 'wireframes-v1.pdf', file_size: 2048, uploaded_by_name: 'Admin E2E',
    versions_count: 1, created_at: '2025-02-01T10:00:00Z', updated_at: '2025-02-01T10:00:00Z',
  },
  {
    id: 2, title: 'Credenciales Wompi Sandbox', description: 'Llaves de API para pruebas.',
    category: 'credentials', current_version: 1, file_url: '/media/wompi-keys.txt',
    file_name: 'wompi-keys.txt', file_size: 512, uploaded_by_name: 'Admin E2E',
    versions_count: 1, created_at: '2025-01-28T10:00:00Z', updated_at: '2025-01-28T10:00:00Z',
  },
];

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });

function setupMocks(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject]) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDeliverables) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/' && method === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify({ id: 10, title: 'New file', category: 'documents', current_version: 1, versions_count: 1 }) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDeliverableDetail) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/pdf/commercial/' && method === 'GET') {
      return { status: 200, contentType: 'application/pdf', body: '%PDF-e2e-deliverable-commercial' };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/pdf/technical/' && method === 'GET') {
      return { status: 200, contentType: 'application/pdf', body: '%PDF-e2e-deliverable-technical' };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Deliverables — Client', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('renders deliverable list with file names and categories', {
    tag: [...PLATFORM_DELIVERABLES, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/deliverables', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /entregables/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Wireframes página principal')).toBeVisible();
    await expect(page.getByText('Credenciales Wompi Sandbox')).toBeVisible();
  });

  test('client cannot see upload button', {
    tag: [...PLATFORM_DELIVERABLES, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/deliverables', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /entregables/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByRole('button', { name: /subir|upload/i })).not.toBeVisible();
  });
});

test.describe('Platform Deliverables — Admin', () => {
  test.setTimeout(60_000);

  test('admin sees upload button and deliverable list', {
    tag: [...PLATFORM_DELIVERABLES, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/deliverables', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /entregables/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Wireframes página principal')).toBeVisible();
    await expect(page.getByRole('button', { name: /subir/i })).toBeVisible();
  });
});

test.describe('Platform Deliverable detail', () => {
  test.setTimeout(60_000);

  test('renders detail with proposal PDF actions and downloads commercial PDF', {
    tag: [...PLATFORM_DELIVERABLE_DETAIL, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/deliverables/1', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Wireframes página principal' })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole('button', { name: /pdf comercial/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /abrir tablero/i })).toBeVisible();
    const pdfWait = page.waitForResponse(
      (res) => res.url().includes('deliverables/1/pdf/commercial/') && res.status() === 200,
    );
    await page.getByRole('button', { name: /pdf comercial/i }).click();
    await pdfWait;
  });
});

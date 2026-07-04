/**
 * E2E tests for the MCPs panel section (superuser-only).
 *
 * FLOW: admin-mcps
 * Covers: connector card rendering, token generation one-time modal,
 *         active toggle, and superuser gating redirect.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_MCPS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const CONNECTOR = {
  slug: 'blog',
  name: 'Blog Publisher',
  description: 'Permite a Claude crear, programar, editar y consultar posts del blog.',
  is_active: false,
  has_token: false,
  token_prefix: '',
  last_used_at: null,
  connection_status: 'error',
  recent_events: [
    {
      event: 'origin_rejected',
      ok: false,
      detail: 'https://evil.example',
      created_at: '2026-07-03T10:00:00-05:00',
    },
    {
      event: 'handshake',
      ok: true,
      detail: 'initialize OK',
      created_at: '2026-07-03T09:58:00-05:00',
    },
  ],
  tools: [
    { name: 'get_blog_template', description: 'Template JSON del blog.' },
    { name: 'create_blog_post', description: 'Crea un post.' },
  ],
};

const TOKEN_RESPONSE = {
  connector_url: 'https://projectapp.co/api/mcp/blog/e2e-token-abc123/',
  token_prefix: 'e2e-toke',
};

function buildHandler({ isSuperuser = true } = {}) {
  return ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: isSuperuser },
        }),
      };
    }
    if (apiPath === 'mcp-connectors/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([CONNECTOR]),
      };
    }
    if (apiPath === 'mcp-connectors/blog/generate-token/' && method === 'POST') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(TOKEN_RESPONSE),
      };
    }
    if (apiPath === 'mcp-connectors/blog/' && method === 'PATCH') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...CONNECTOR, is_active: true }),
      };
    }
    return null;
  };
}

test.describe('Panel MCPs', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('renders the blog connector card with its tools', {
    tag: [...ADMIN_MCPS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByText('Blog Publisher')).toBeVisible();
    await expect(page.getByText('sin generar')).toBeVisible();

    // Compact card: tools are NOT on the card anymore (they live in the modal)
    await expect(page.getByText('create_blog_post')).not.toBeVisible();

    // Collapsible step-by-step connection guide (native <details>) is present.
    await expect(page.getByTestId('mcps-guide')).toBeVisible();
    await expect(page.getByText('¿Cómo conectar un conector a Claude?')).toBeVisible();

    // Clicking the card opens the detail modal with connection status,
    // activity trail and available tools.
    await page.getByTestId('mcp-card-blog').click();
    await expect(page.getByTestId('mcp-detail-modal')).toBeVisible();

    await expect(page.getByTestId('mcp-connection-blog')).toContainText('Error de conexión');
    await expect(page.getByTestId('mcp-connection-blog')).toContainText('https://evil.example');

    await expect(page.getByTestId('mcp-activity-list-blog')).toContainText('Origin rechazado');
    await expect(page.getByTestId('mcp-activity-list-blog')).toContainText('Conexión (initialize)');
    await expect(page.getByText('create_blog_post')).toBeVisible();
  });

  test('generates a token and shows the one-time connector URL modal', {
    tag: [...ADMIN_MCPS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-generate-token-blog').click();

    await expect(page.getByTestId('mcp-token-modal')).toBeVisible();
    await expect(page.getByTestId('mcp-token-url')).toContainText('/api/mcp/blog/');

    await page.getByTestId('mcp-token-close').click();
    await expect(page.getByTestId('mcp-token-modal')).not.toBeVisible();
  });

  test('activates the connector via the toggle', {
    tag: [...ADMIN_MCPS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-toggle-blog').click();
    await expect(page.getByTestId('mcp-toggle-blog')).toHaveAttribute('aria-checked', 'true');
  });

  test('staff non-superuser is redirected away from /panel/mcps', {
    tag: [...ADMIN_MCPS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ isSuperuser: false }));
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page).not.toHaveURL(/\/panel\/mcps/, { timeout: 25_000 });
  });
});

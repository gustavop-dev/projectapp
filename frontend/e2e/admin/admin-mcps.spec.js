/**
 * E2E tests for the MCPs panel section (superuser-only).
 *
 * FLOW: admin-mcps
 * Covers: connector inventory, one-time secrets, active toggle, scoped
 *         credential lifecycle and superuser gating redirect.
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
  tool_count: 2,
  risk_counts: { read: 1, write: 1, sensitive: 0 },
  is_legacy: true,
  credentials: [
    {
      id: 7,
      label: 'Auditoría',
      token_prefix: 'scope123',
      allowed_tools: ['get_blog_template'],
      actor: 'mcp_blog',
      is_usable: true,
      expires_at: null,
      revoked_at: null,
      last_used_at: null,
    },
  ],
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
      credential_prefix: 'scope123',
      request_id: '123e4567-e89b-12d3-a456-426614174000',
      duration_ms: 12,
      object_refs: [{ field: 'post_id', value: 8 }],
      created_at: '2026-07-03T09:58:00-05:00',
    },
  ],
  tools: [
    { name: 'get_blog_template', description: 'Template JSON del blog.', risk: 'read' },
    { name: 'create_blog_post', description: 'Crea un post.', risk: 'write' },
  ],
};

const TOKEN_RESPONSE = {
  connector_url: 'https://projectapp.co/api/mcp/blog/e2e-token-abc123/',
  token_prefix: 'e2e-toke',
};

const SCOPED_TOKEN_RESPONSE = {
  id: 7,
  label: 'Auditoría',
  connector_url: 'https://projectapp.co/api/mcp/blog/e2e-scoped-token/',
  token_prefix: 'e2e-scop',
  allowed_tools: ['get_blog_template'],
};

function buildHandler({ isSuperuser = true, credentialCreateError = false } = {}) {
  const connector = JSON.parse(JSON.stringify(CONNECTOR));
  return ({ route, apiPath, method }) => {
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
        body: JSON.stringify([connector]),
      };
    }
    if (apiPath === 'mcp-connectors/blog/generate-token/' && method === 'POST') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(TOKEN_RESPONSE),
      };
    }
    if (apiPath === 'mcp-connectors/blog/credentials/' && method === 'POST') {
      if (credentialCreateError) {
        return {
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({ label: 'Ya existe una credencial con esa etiqueta.' }),
        };
      }
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(SCOPED_TOKEN_RESPONSE),
      };
    }
    if (apiPath === 'mcp-connectors/blog/credentials/7/' && method === 'PATCH') {
      const payload = route.request().postDataJSON();
      connector.credentials[0] = {
        ...connector.credentials[0],
        allowed_tools: payload.allowed_tools,
        expires_at: payload.expires_at,
      };
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(connector),
      };
    }
    if (apiPath === 'mcp-connectors/blog/credentials/7/rotate/' && method === 'POST') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...SCOPED_TOKEN_RESPONSE,
          connector_url: 'https://projectapp.co/api/mcp/blog/e2e-replacement-token/',
        }),
      };
    }
    if (apiPath === 'mcp-connectors/blog/credentials/7/' && method === 'DELETE') {
      connector.credentials[0] = {
        ...connector.credentials[0],
        is_usable: false,
        revoked_at: '2026-09-02T12:00:00Z',
      };
      return { status: 204, body: '' };
    }
    if (apiPath === 'mcp-connectors/blog/' && method === 'PATCH') {
      connector.is_active = true;
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(connector),
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
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:display', '@responsive:mcp'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/blog', { waitUntil: 'domcontentloaded' });
    await page
      .getByRole('navigation', { name: 'Navegación del panel' })
      .getByRole('link', { name: 'MCPs', exact: true })
      .click();

    await expect(page).toHaveURL(/\/panel\/mcps/);
    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByText('Blog Publisher')).toBeVisible();

    // Collapsed accordion row: token, status and tools live in the body and
    // are hidden until the row is expanded.
    await expect(page.getByText('sin generar')).not.toBeVisible();
    await expect(page.getByText('create_blog_post')).not.toBeVisible();

    // Collapsible step-by-step connection guide (native <details>) is present.
    await expect(page.getByTestId('mcps-guide')).toBeVisible();
    await expect(page.getByText('¿Cómo conectar un conector a Claude?')).toBeVisible();

    // Expanding the row reveals the detail body: token, connection status,
    // and the activity/tools sub-accordions.
    await page.getByTestId('mcp-card-header-blog').click();
    await expect(page.getByTestId('mcp-detail-blog')).toBeVisible();
    await expect(page.getByText('sin generar')).toBeVisible();

    await expect(page.getByTestId('mcp-connection-blog')).toContainText('Error de conexión');
    await expect(page.getByTestId('mcp-connection-blog')).toContainText('https://evil.example');
    await expect(page.getByTestId('mcp-risk-summary-blog')).toContainText('Lectura 1');
    await expect(page.getByTestId('mcp-risk-summary-blog')).toContainText('Edición 1');

    // Recent activity sub-accordion expands with the event trail.
    await page.getByTestId('mcp-activity-toggle-blog').click();
    await expect(page.getByTestId('mcp-activity-list-blog')).toContainText('Origin rechazado');
    await expect(page.getByTestId('mcp-activity-list-blog')).toContainText('Conexión (initialize)');
    await expect(page.getByTestId('mcp-activity-list-blog')).toContainText('Credencial scope123');
    await expect(page.getByTestId('mcp-activity-list-blog')).toContainText('post_id=8');

    // Available tools sub-accordion expands with the tool list.
    await page.getByTestId('mcp-tools-toggle-blog').click();
    await expect(page.getByText('create_blog_post')).toBeVisible();
  });

  test('generates a token and shows the one-time connector URL modal', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    // The generate-token button lives in the expanded body, so open the row first.
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-generate-token-blog').click();

    await expect(page.getByTestId('mcp-token-modal')).toBeVisible();
    await expect(page.getByTestId('mcp-token-url')).toContainText('/api/mcp/blog/');

    await page.getByTestId('mcp-token-close').click();
    await expect(page.getByTestId('mcp-token-modal')).not.toBeVisible();
  });

  test('activates the connector via the toggle', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-toggle-blog').click();
    await expect(page.getByTestId('mcp-toggle-blog')).toHaveAttribute('aria-checked', 'true');
  });

  test('creates a read-only credential and reveals its URL once', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-create-credential-blog').click();
    await expect(page.getByTestId('mcp-credential-modal')).toBeVisible();
    await page.getByTestId('mcp-credential-label').fill('Lectura externa');
    await page.getByTestId('mcp-credential-save').click();

    await expect(page.getByTestId('mcp-token-modal')).toBeVisible();
    await expect(page.getByTestId('mcp-token-url')).toContainText('e2e-scoped-token');
  });

  test('edits the scope of an existing credential', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-credentials-toggle-blog').click();
    await page.getByTestId('mcp-credential-edit-7').click();
    await page.getByTestId('mcp-credential-scope').selectOption('all');
    await page.getByTestId('mcp-credential-save').click();

    await expect(page.getByTestId('mcp-credential-modal')).not.toBeVisible();
    await expect(page.getByTestId('mcp-credential-7')).toContainText('Todas las funciones');
  });

  test('rotates one credential and reveals only the replacement URL', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-credentials-toggle-blog').click();
    await page.getByTestId('mcp-credential-rotate-7').click();

    await expect(page.getByTestId('mcp-token-modal')).toBeVisible();
    await expect(page.getByTestId('mcp-token-url')).toContainText('e2e-replacement-token');
  });

  test('revokes one credential after operator confirmation', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-credentials-toggle-blog').click();
    await page.getByTestId('mcp-credential-revoke-7').click();
    await expect(page.getByTestId('confirm-modal-confirm')).toHaveText('Revocar');
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByTestId('mcp-credential-7')).toContainText('No disponible');
    await expect(page.getByTestId('mcp-credential-revoke-7')).toHaveCount(0);
  });

  test('rejects a custom credential scope with no selected tools', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-create-credential-blog').click();
    await page.getByTestId('mcp-credential-label').fill('Sin alcance');
    await page.getByTestId('mcp-credential-scope').selectOption('custom');
    await page.getByTestId('mcp-credential-save').click();

    await expect(page.getByTestId('mcp-credential-modal')).toContainText(
      'Selecciona al menos una función',
    );
  });

  test('keeps the credential form open when creation is rejected', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ credentialCreateError: true }));
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('mcp-card-blog')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-create-credential-blog').click();
    await page.getByTestId('mcp-credential-label').fill('Auditoría');
    await page.getByTestId('mcp-credential-save').click();

    await expect(page.getByTestId('mcp-credential-modal')).toBeVisible();
    await expect(page.getByTestId('mcp-credential-modal')).toContainText(
      'Ya existe una credencial con esa etiqueta.',
    );
  });

  test('staff non-superuser is redirected away from /panel/mcps', {
    tag: [...ADMIN_MCPS, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ isSuperuser: false }));
    await page.goto('/panel/mcps', { waitUntil: 'domcontentloaded' });

    await expect(page).toHaveURL(
      /\/(?:[a-z]{2}(?:-[a-z]{2})?\/)?panel\/?(?:[?#].*)?$/,
      { timeout: 25_000 },
    );
  });
});

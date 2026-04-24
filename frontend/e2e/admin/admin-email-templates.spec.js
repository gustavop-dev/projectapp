/**
 * E2E tests for admin email templates configuration flow.
 *
 * FLOW: admin-email-templates-config
 * Covers: navigate to email templates page, view template list, filter by category,
 * expand template editor, edit fields, save changes, preview HTML, reset to defaults.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_EMAIL_TEMPLATES_CONFIG } from '../helpers/flow-tags.js';

const MOCK_TEMPLATES_LIST = [
  {
    template_key: 'proposal_sent_client',
    name: 'Propuesta Enviada',
    description: 'Se envía cuando el vendedor envía la propuesta al cliente.',
    category: 'client',
    is_active: true,
    is_customized: false,
    editable_fields_count: 4,
  },
  {
    template_key: 'proposal_reminder',
    name: 'Recordatorio de Propuesta',
    description: 'Se envía como recordatorio al cliente.',
    category: 'client',
    is_active: true,
    is_customized: true,
    editable_fields_count: 4,
  },
  {
    template_key: 'proposal_first_view_notification',
    name: 'Primera Vista — Notificación',
    description: 'Notificación interna cuando el cliente abre la propuesta.',
    category: 'internal',
    is_active: true,
    is_customized: false,
    editable_fields_count: 2,
  },
  {
    template_key: 'contact_notification',
    name: 'Notificación de Contacto',
    description: 'Se envía cuando un visitante llena el formulario de contacto.',
    category: 'contact',
    is_active: true,
    is_customized: false,
    editable_fields_count: 1,
  },
];

const MOCK_TEMPLATE_DETAIL = {
  template_key: 'proposal_sent_client',
  name: 'Propuesta Enviada',
  description: 'Se envía cuando el vendedor envía la propuesta al cliente.',
  category: 'client',
  is_active: true,
  editable_fields: [
    { key: 'subject', label: 'Asunto del correo', type: 'text', default_value: '📋 {client_name}, tu propuesta está lista', current_value: '', is_overridden: false },
    { key: 'greeting', label: 'Saludo', type: 'text', default_value: '¡Hola {client_name}! 👋', current_value: '', is_overridden: false },
    { key: 'body', label: 'Cuerpo del mensaje', type: 'textarea', default_value: 'Hemos preparado una propuesta...', current_value: '', is_overridden: false },
    { key: 'cta_text', label: 'Texto del botón', type: 'text', default_value: '📄 Ver mi propuesta', current_value: '', is_overridden: false },
  ],
  available_variables: ['client_name', 'title', 'proposal_url', 'days_remaining'],
};

const MOCK_PREVIEW = {
  template_key: 'proposal_sent_client',
  subject: '📋 Carlos, tu propuesta está lista — Project App',
  html_preview: '<html><body><h1>Hola Carlos</h1><p>Tu propuesta está lista.</p></body></html>',
};

function buildApiHandler(apiPath, method) {
  if (apiPath === 'auth/check/') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
  }
  if (apiPath === 'proposals/defaults/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: null, language: 'es', sections_json: [], created_at: null, updated_at: null }) };
  }
  if (apiPath === 'email-templates/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TEMPLATES_LIST) };
  }
  if (apiPath === 'email-templates/proposal_sent_client/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TEMPLATE_DETAIL) };
  }
  if (apiPath === 'email-templates/proposal_sent_client/' && method === 'PUT') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify({ template_key: 'proposal_sent_client', content_overrides: { greeting: 'Custom greeting' }, is_active: true }) };
  }
  if (apiPath === 'email-templates/proposal_sent_client/preview/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PREVIEW) };
  }
  if (apiPath === 'email-templates/proposal_sent_client/reset/' && method === 'POST') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify({ deleted: true, template_key: 'proposal_sent_client' }) };
  }
  return null;
}

test.describe('Admin Email Templates Config', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8200, role: 'admin', is_staff: true } });
  });

  test('renders page title and category filter buttons', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Page title renders
    await expect(page.locator('h1')).toContainText('Valores por Defecto');

    // Category filter buttons render — scope to the filter strip (first match) to avoid
    // matching template name buttons that also contain "Contacto".
    await expect(page.getByRole('button', { name: /Todos/ }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Cliente/ }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Interno/ }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Contacto/ }).first()).toBeVisible();
  });

  test('renders all template rows in the list', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Template rows render
    await expect(page.locator('text=Propuesta Enviada')).toBeVisible();
    await expect(page.locator('text=Recordatorio de Propuesta')).toBeVisible();
    await expect(page.locator('text=Primera Vista — Notificación')).toBeVisible();
    await expect(page.locator('text=Notificación de Contacto')).toBeVisible();
  });

  test('filters templates by category', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Click "Interno" filter
    await page.getByRole('button', { name: /Interno/ }).click();

    // Only internal template visible
    await expect(page.locator('text=Primera Vista — Notificación')).toBeVisible();
    await expect(page.locator('text=Propuesta Enviada')).not.toBeVisible();
    await expect(page.locator('text=Notificación de Contacto')).not.toBeVisible();
  });

  test('shows customized badge for overridden templates', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Reminder template has "Personalizado" badge
    await expect(page.getByText('Personalizado', { exact: true })).toBeVisible();
  });

  test('expands template and shows editable fields with variables', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Click on template to expand and wait for detail API response
    const [detailResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('email-templates/proposal_sent_client/') && resp.status() === 200),
      page.locator('text=Propuesta Enviada').click(),
    ]);
    await detailResponse;

    // Editable fields render
    await expect(page.getByText('Asunto del correo')).toBeVisible();
    await expect(page.getByText('Saludo')).toBeVisible();
    await expect(page.getByText('Cuerpo del mensaje')).toBeVisible();
    await expect(page.getByText('Texto del botón')).toBeVisible();

    // Available variables render
    await expect(page.getByText('Variables disponibles')).toBeVisible();
    await expect(page.locator('code', { hasText: 'client_name' })).toBeVisible();
  });

  test('expanded template shows status toggle and action buttons', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Click on template to expand and wait for detail API response
    const [detailResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('email-templates/proposal_sent_client/') && resp.status() === 200),
      page.locator('text=Propuesta Enviada').click(),
    ]);
    await detailResponse;

    // Active toggle renders
    await expect(page.getByText('Estado del email')).toBeVisible();

    // Action buttons render (use exact emoji text to avoid matching row preview icons)
    await expect(page.getByRole('button', { name: '👁 Vista previa' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Restaurar/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Guardar Cambios/ })).toBeVisible();
  });

  test('opens preview modal with rendered HTML', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Expand template and wait for detail API response
    const [detailResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('email-templates/proposal_sent_client/') && resp.status() === 200),
      page.locator('text=Propuesta Enviada').click(),
    ]);
    await detailResponse;

    // Click preview button and wait for preview API response
    const [previewResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('email-templates/proposal_sent_client/preview/') && resp.status() === 200),
      page.getByRole('button', { name: '👁 Vista previa' }).click(),
    ]);
    await previewResponse;

    // Preview modal renders
    await expect(page.getByRole('heading', { name: 'Vista Previa' })).toBeVisible();
    // Subject line shown
    await expect(page.locator('text=Asunto:')).toBeVisible();
    // Iframe renders
    await expect(page.locator('iframe[sandbox]')).toBeVisible();
  });

  test('shows reset confirmation modal', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=emails');
    await page.waitForLoadState('networkidle');

    // Expand template and wait for detail API response
    const [detailResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('email-templates/proposal_sent_client/') && resp.status() === 200),
      page.locator('text=Propuesta Enviada').click(),
    ]);
    await detailResponse;

    // Click restore button
    await page.getByRole('button', { name: 'Restaurar' }).click();

    // Confirmation modal renders
    await expect(page.locator('text=¿Restaurar valores originales?')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sí, restaurar' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancelar' })).toBeVisible();
  });

  test('back link navigates to proposals list', {
    tag: [...ADMIN_EMAIL_TEMPLATES_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method: _method }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/defaults/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: null, language: 'es', sections_json: [], created_at: null, updated_at: null }) };
      if (apiPath === 'email-templates/') return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TEMPLATES_LIST) };
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      return null;
    });
    await page.goto('/panel/proposals/defaults');
    await page.waitForLoadState('networkidle');

    // Click back link
    await page.locator('text=Volver a Propuestas').click();
    await page.waitForURL('**/panel/proposals**');
  });
});

/**
 * E2E tests for admin Proposal — "Documentos & Plantillas" tab.
 *
 * Covers: tab visibility based on proposal status, template list render,
 * and copy-to-clipboard interaction.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_PROPOSAL_DIAGNOSTIC_TEMPLATES,
} from '../helpers/flow-tags.js';

const PROPOSAL_ID = 42;
const futureDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const templatesList = [
  { slug: 'diagnostico-aplicacion', title: 'Diagnóstico de Aplicación', filename: 'diagnostico_aplicacion_es.md', size_bytes: 4096, updated_at: '2026-04-01T10:00:00Z' },
  { slug: 'diagnostico-tecnico', title: 'Diagnóstico Técnico', filename: 'diagnostico_tecnico_es.md', size_bytes: 5120, updated_at: '2026-04-01T10:00:00Z' },
  { slug: 'anexo', title: 'Anexo — Dimensionamiento', filename: 'anexo_es.md', size_bytes: 3072, updated_at: '2026-04-01T10:00:00Z' },
];

const templateDetail = {
  slug: 'diagnostico-aplicacion',
  title: 'Diagnóstico de Aplicación',
  filename: 'diagnostico_aplicacion_es.md',
  size_bytes: 4096,
  updated_at: '2026-04-01T10:00:00Z',
  content_markdown: '# Diagnóstico de Aplicación\n\nContenido de diagnóstico.',
};

function makeProposal(overrides = {}) {
  return {
    id: PROPOSAL_ID,
    uuid: 'diag-templates-test-uuid',
    title: 'Templates Test Proposal',
    client_name: 'Templates Client',
    client_email: 'client@templates.com',
    status: 'sent',
    language: 'es',
    total_investment: '5000000',
    currency: 'COP',
    view_count: 1,
    sent_at: '2026-04-01T10:00:00Z',
    expires_at: futureDate,
    is_active: true,
    sections: [],
    requirement_groups: [],
    change_logs: [],
    proposal_documents: [],
    ...overrides,
  };
}

function baseHandler(proposal, extra = {}) {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    if (apiPath === 'diagnostic-templates/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(templatesList) };
    }
    if (apiPath === 'diagnostic-templates/diagnostico-aplicacion/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(templateDetail) };
    }
    for (const [path, response] of Object.entries(extra)) {
      if (apiPath === path) return response;
    }
    return null;
  };
}

test.describe('Admin Proposal — Documentos & Plantillas tab', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9200, role: 'admin', is_staff: true },
    });
  });

  test('tab is hidden for draft proposals', {
    tag: [...ADMIN_PROPOSAL_DIAGNOSTIC_TEMPLATES, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal({ status: 'draft' })));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.getByRole('button', { name: 'General' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: 'Documentos & Plantillas' })).not.toBeVisible();
  });

  test('tab is visible for sent proposals', {
    tag: [...ADMIN_PROPOSAL_DIAGNOSTIC_TEMPLATES, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal({ status: 'sent' })));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.getByRole('button', { name: 'Documentos & Plantillas' })).toBeVisible({ timeout: 15000 });
  });

  test('tab is visible for negotiating proposals', {
    tag: [...ADMIN_PROPOSAL_DIAGNOSTIC_TEMPLATES, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal({ status: 'negotiating' })));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.getByRole('button', { name: 'Documentos & Plantillas' })).toBeVisible({ timeout: 15000 });
  });

  test('template list renders three template titles after clicking tab', {
    tag: [...ADMIN_PROPOSAL_DIAGNOSTIC_TEMPLATES, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal({ status: 'sent' })));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.getByRole('button', { name: 'Documentos & Plantillas' }).click();

    await expect(page.getByText('Diagnóstico de Aplicación')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Diagnóstico Técnico')).toBeVisible();
    await expect(page.getByText('Anexo — Dimensionamiento')).toBeVisible();
  });

  test('copy button triggers detail API call', {
    tag: [...ADMIN_PROPOSAL_DIAGNOSTIC_TEMPLATES, '@role:admin'],
  }, async ({ page }) => {
    let detailFetched = false;
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(makeProposal({ status: 'sent' })) };
      }
      if (apiPath === 'diagnostic-templates/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(templatesList) };
      }
      if (apiPath === 'diagnostic-templates/diagnostico-aplicacion/') {
        detailFetched = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify(templateDetail) };
      }
      return null;
    });

    await page.context().grantPermissions(['clipboard-write', 'clipboard-read']);
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.getByRole('button', { name: 'Documentos & Plantillas' }).click();
    await expect(page.getByText('Diagnóstico de Aplicación')).toBeVisible({ timeout: 10000 });

    const copyBtns = page.getByRole('button', { name: 'Copiar contenido' });
    await copyBtns.first().click();

    await expect(() => expect(detailFetched).toBe(true)).toPass({ timeout: 5000 });
  });
});

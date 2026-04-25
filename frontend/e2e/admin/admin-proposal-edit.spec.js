/**
 * E2E tests for admin proposal edit flow.
 *
 * Covers: page heading, tab rendering, General tab form fields.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_EDIT } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Propuesta E2E',
  client_name: 'Cliente Edit E2E',
  client_email: 'edit@e2e.com',
  client_phone: '+573001234567',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  heat_score: 5,
  sent_at: null,
  is_active: true,
  created_at: '2026-01-01T12:00:00Z',
  sections: [],
  requirement_groups: [],
};

function buildMockHandler() {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    if (apiPath === 'proposals/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProposal]) };
    }
    return null;
  };
}

const baseTechnicalContent = {
  purpose: 'Definir el alcance técnico del proyecto y sus decisiones principales.',
  stack: [{ layer: 'Frontend', technology: 'Nuxt 3', rationale: 'SSR y DX' }],
  architecture: {
    summary: 'Arquitectura por capas con separación entre panel, APIs y vista pública.',
    patterns: [],
    diagramNote: 'Diagrama disponible en el anexo interno.',
  },
  dataModel: {
    summary: 'Modelo basado en propuestas, secciones y documentos asociados.',
    relationships: 'Una propuesta tiene muchas secciones y documentos.',
    entities: [],
  },
  growthReadiness: { summary: 'Preparado para crecer por módulos.', strategies: [] },
  epics: [
    {
      epicKey: 'portal-cliente',
      title: 'Portal del cliente',
      description: 'Panel principal para administrar contenido y seguimiento.',
      linked_module_ids: [],
      requirements: [
        {
          flowKey: 'panel-inicio',
          title: 'Dashboard inicial',
          priority: 'high',
          description: 'Resumen general del estado del proyecto.',
          configuration: 'Visible para administradores y editores.',
          usageFlow: 'Login -> Dashboard -> Navegación por módulos',
          linked_module_ids: [],
        },
      ],
    },
  ],
  apiSummary: 'La API se organiza por dominios del negocio.',
  apiDomains: [],
  integrations: { included: [], excluded: [], notes: 'SMTP\nAnalytics' },
  environmentsNote: 'Staging y producción separados.',
  environments: [],
  security: [],
  performanceQuality: { metrics: [], practices: [] },
  backupsNote: 'Backups diarios con retención semanal.',
  quality: { dimensions: [], testTypes: [], criticalFlowsNote: 'Validar login, dashboard y subida de archivos.' },
  decisions: [],
};

const baseExportJson = {
  general: { clientName: 'Client' },
  executiveSummary: { title: 'Resumen' },
  contextDiagnostic: { title: 'Diagnóstico' },
  conversionStrategy: { title: 'Estrategia' },
  designUX: { title: 'Diseño UX' },
  creativeSupport: { title: 'Acompañamiento' },
  developmentStages: { title: 'Etapas' },
  processMethodology: { title: 'Metodología' },
  functionalRequirements: { title: 'Requerimientos' },
  timeline: { title: 'Cronograma' },
  investment: { title: 'Inversión', totalInvestment: '5000000', currency: 'COP' },
  proposalSummary: { title: 'Resumen final' },
  finalNote: { title: 'Cierre' },
  nextSteps: { title: 'Siguientes pasos' },
  technicalDocument: baseTechnicalContent,
};

const baseProposal = {
  id: 1,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Edit Test',
  client_name: 'Client',
  client_email: 'client@example.com',
  client_phone: '+57 300 000 0000',
  language: 'es',
  status: 'draft',
  total_investment: 5000000,
  currency: 'COP',
  hosting_percent: 30,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  discount_percent: 5,
  reminder_days: 10,
  urgency_reminder_days: 15,
  automations_paused: false,
  view_count: 0,
  sent_at: null,
  expires_at: null,
  updated_at: '2026-04-22T10:30:00Z',
  sections: [
    {
      id: 201,
      section_type: 'technical_document',
      title: 'Detalle técnico',
      order: 14,
      is_enabled: true,
      content_json: baseTechnicalContent,
    },
  ],
  requirement_groups: [],
};


test.describe('Admin Proposal Edit', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8200, role: 'admin', is_staff: true } });
  });

  test('renders proposal title in page heading', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
  });

  test('renders General and Secciones navigation tabs', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole('button', { name: 'General' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Secciones' })).toBeVisible();
  });

  test('shows client name field pre-filled in General tab', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('input[type="text"][required]').nth(1)).toHaveValue('Cliente Edit E2E');
  });

  test('shows expiry days number input beside Fecha de expiración field', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('input[type="number"][min="1"][max="365"]')).toBeVisible();
  });

  test('shows success toast after saving proposal changes', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath === 'proposals/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProposal]) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/update/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
    await page.locator('[data-testid="proposal-edit-submit"]').click();
    await expect(page.getByText('Propuesta actualizada.')).toBeVisible({ timeout: 10_000 });
  });

  test('keeps financial fields in the right column and submits the same payload keys', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;

    await page.setViewportSize({ width: 1600, height: 1200 });

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }

      if (apiPath === 'proposals/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(baseProposal) };
      }

      if (apiPath === 'proposals/1/update/' && method === 'PATCH') {
        capturedPayload = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...baseProposal, ...capturedPayload }),
        };
      }

      return null;
    });

    await page.goto('/panel/proposals/1/edit');

    const financeSidebar = page.getByTestId('general-finance-sidebar');
    await expect(financeSidebar).toBeVisible();
    await expect(page.getByTestId('general-finance-investment-card')).toBeVisible();
    await expect(page.getByTestId('general-finance-hosting-card')).toBeVisible();
    await expect(page.getByTestId('general-finance-discounts-card')).toBeVisible();

    await financeSidebar.getByTestId('general-finance-total-investment').fill('7500000');
    await financeSidebar.getByTestId('general-finance-currency').selectOption('USD');
    await financeSidebar.getByTestId('general-finance-hosting-percent').fill('35');
    await financeSidebar.getByTestId('general-finance-quarterly-discount').fill('12');
    await financeSidebar.getByTestId('general-finance-semiannual-discount').fill('22');
    await page.getByTestId('general-finance-general-discount').fill('8');

    await page.getByRole('button', { name: 'Guardar Cambios' }).click();

    await expect(page.getByText('Propuesta actualizada.')).toBeVisible();
    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.total_investment).toBe(7500000);
    expect(capturedPayload.currency).toBe('USD');
    expect(capturedPayload.hosting_percent).toBe(35);
    expect(capturedPayload.hosting_discount_quarterly).toBe(12);
    expect(capturedPayload.hosting_discount_semiannual).toBe(22);
    expect(capturedPayload.discount_percent).toBe(8);
  });

  test('shows JSON stats and aligns textarea heights for proposal and technical JSON views', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }

      if (apiPath === 'proposals/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(baseProposal) };
      }

      if (apiPath === 'proposals/1/export-json/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(baseExportJson) };
      }

      return null;
    });

    await page.goto('/panel/proposals/1/edit');

    await page.getByRole('button', { name: 'JSON' }).click();
    await expect(page.getByTestId('proposal-json-stats')).toContainText('Secciones:');
    await expect(page.getByTestId('proposal-json-stats')).toContainText('Progreso:');
    await expect(page.getByTestId('proposal-json-stats')).toContainText('Tamaño del JSON:');
    await expect(page.getByTestId('proposal-json-stats')).toContainText('Última actualización:');
    await expect(page.getByTestId('proposal-export-json-textarea')).toHaveAttribute('rows', '18');
    await expect(page.getByTestId('proposal-import-json-textarea')).toHaveAttribute('rows', '18');

    await page.getByRole('button', { name: 'Det. técnico' }).click();
    await expect(page.getByTestId('technical-purpose-textarea')).toBeVisible();
    await expect(page.getByTestId('technical-epic-description-textarea').first()).toBeVisible();
    await expect(page.getByTestId('technical-req-description-textarea').first()).toBeVisible();

    await page.getByTestId('technical-json-subtab').click();
    await expect(page.getByTestId('technical-json-stats')).toContainText('Secciones:');
    await expect(page.getByTestId('technical-json-stats')).toContainText('Progreso:');
    await expect(page.getByTestId('technical-json-stats')).toContainText('Tamaño del JSON:');
    await expect(page.getByTestId('technical-json-stats')).toContainText('Última actualización:');
    await expect(page.getByTestId('technical-json-textarea')).toHaveAttribute('rows', '18');
  });
});

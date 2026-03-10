/**
 * E2E tests for the functional requirements detail modal in the proposal viewer.
 *
 * Covers: clicking a requirement group card opens modal with items,
 * closing modal, navigating between groups.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_FUNCTIONAL_REQUIREMENTS_MODAL } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Requirements Modal Test',
  client_name: 'Test Client',
  status: 'sent',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: '👋 Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Test Client', inspirationalQuote: '' },
    },
    {
      id: 2,
      section_type: 'functional_requirements',
      title: '📋 Requerimientos',
      order: 1,
      is_enabled: true,
      content_json: {
        index: '2',
        title: 'Requerimientos funcionales',
        intro: 'A continuación se detallan los requerimientos.',
        groups: [
          {
            id: 'views',
            icon: '🖥️',
            title: 'Vistas',
            description: 'Páginas principales del sitio.',
            items: [
              { icon: '🏠', name: 'Home', description: 'Página principal con hero y servicios' },
              { icon: '📞', name: 'Contacto', description: 'Formulario de contacto' },
            ],
          },
          {
            id: 'components',
            icon: '🧩',
            title: 'Componentes',
            description: 'Elementos reutilizables.',
            items: [
              { icon: '📱', name: 'Navbar', description: 'Barra de navegación responsive' },
            ],
          },
        ],
        additionalModules: [],
      },
    },
  ],
  requirement_groups: [],
};

async function navigateToRequirements(page) {
  await page.goto(`/proposal/${MOCK_UUID}`);
  await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 3000 });
  await nextBtn.click();

  await expect(page.getByText('Requerimientos funcionales')).toBeVisible({ timeout: 5000 });
}

test.describe('Proposal Functional Requirements Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('clicking a group card opens detail modal with items', {
    tag: [...PROPOSAL_FUNCTIONAL_REQUIREMENTS_MODAL, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await navigateToRequirements(page);

    // Both group cards should be visible
    await expect(page.getByText('Vistas')).toBeVisible();
    await expect(page.getByText('Componentes')).toBeVisible();

    // Click the Vistas group card using the "Ver detalle" link inside it
    const vistasCard = page.locator('.overview-card').filter({ hasText: 'Vistas' });
    await vistasCard.click();

    // Modal should show group items
    await expect(page.getByText('Página principal con hero y servicios')).toBeVisible({ timeout: 3000 });
  });

  test('clicking a different group card shows its items', {
    tag: [...PROPOSAL_FUNCTIONAL_REQUIREMENTS_MODAL, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await navigateToRequirements(page);

    // Click the Componentes group card
    const componentesCard = page.locator('.overview-card').filter({ hasText: 'Componentes' });
    await componentesCard.click();

    // Modal should show Componentes items
    await expect(page.getByText('Navbar')).toBeVisible({ timeout: 3000 });
    await expect(page.getByText('Barra de navegación responsive')).toBeVisible();
  });
});

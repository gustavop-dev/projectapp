/**
 * E2E tests for the per-proposal hourly rate tab («Tarifa por hora»).
 *
 * Covers: reading the catalog rate in automatic mode, overriding it manually
 * for one proposal, the live preview recalculating, the save payload, and the
 * manual value surviving a switch back to automatic.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { ADMIN_PROPOSAL_HOUR_RATE } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;

const CATALOG = [
  {
    id: 7, nationality: 'COL', currency: 'COP', name_es: 'Pro', name_en: 'Pro',
    note_es: '', note_en: '', hours: 60, hourly_rate: '30000',
    discount_percent: 10, is_active: true, order: 1,
  },
  {
    id: 8, nationality: 'COL', currency: 'COP', name_es: 'Ágil', name_en: 'Agile',
    note_es: 'nota', note_en: 'note', hours: 20, hourly_rate: '30000',
    discount_percent: 0, is_active: true, order: 2,
  },
];

function buildProposal(conditionsContent = {}) {
  return {
    id: PROPOSAL_ID,
    uuid: '11111111-1111-1111-1111-111111111111',
    title: 'E2E Hour Rate',
    client_name: 'Rate Client',
    client_email: 'rate@test.com',
    language: 'es',
    nationality: 'COL',
    status: 'draft',
    total_investment: '5000000',
    currency: 'COP',
    view_count: 0,
    sent_at: null,
    expires_at: null,
    sections: [{
      id: 113,
      section_type: 'commercial_conditions',
      title: '📋 Condiciones comerciales',
      order: 12,
      is_enabled: true,
      is_wide_panel: false,
      content_json: {
        index: '12',
        title: 'Condiciones comerciales',
        packagesTitle: 'Paquetes de horas',
        hourlyRate: 30000,
        currency: 'COP',
        packages: [
          { id: 7, name: 'Pro', hours: 60, discountPercent: 10, note: '', hourlyRate: 30000 },
          { id: 8, name: 'Ágil', hours: 20, discountPercent: 0, note: 'nota', hourlyRate: 30000 },
        ],
        effortBadge: '',
        scopeTitle: 'Alcance',
        scopeParagraphs: ['p1'],
        ...conditionsContent,
      },
    }],
  };
}

async function openTab(page, { proposal, captured = [] } = {}) {
  const data = proposal || buildProposal();
  await mockApi(page, async ({ route, apiPath }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
      };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(data) };
    }
    if (apiPath.startsWith('hour-packages/admin/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(CATALOG) };
    }
    const sectionMatch = apiPath.match(/^proposals\/sections\/(\d+)\/update\/$/);
    if (sectionMatch) {
      captured.push(route.request().postDataJSON());
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ section: { ...data.sections[0] } }),
      };
    }
    return null;
  });

  await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, {
    waitUntil: 'domcontentloaded',
  });
  // Reach the tab the way an admin does, so the tab itself stays covered.
  await page.getByRole('tab', { name: 'Tarifa por hora' }).click();
  await page.getByTestId('hour-rate-preview').waitFor({ state: 'visible' });
  return { captured, data };
}

test.describe('Admin — proposal hourly rate', () => {
  test.setTimeout(60_000);

  test('automatic mode prices the packages from the catalog', {
    tag: [...ADMIN_PROPOSAL_HOUR_RATE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (openTab enters through the proposal edit page
    // and clicks the tab; only /edit itself is a direct goto, and navigating
    // to that page is covered by admin-proposal-edit)
    await openTab(page);

    await expect(page.getByTestId('hour-rate-mode-hint')).toContainText('catálogo');
    // Pro: 30.000 with 10% off → 27.000/h over 60h → 1.620.000
    await expect(page.getByTestId('hour-rate-rate-7')).toContainText('27.000');
    await expect(page.getByTestId('hour-rate-total-7')).toContainText('1.620.000');
    // The manual input only exists in manual mode.
    await expect(page.getByTestId('hour-rate-manual-input')).toHaveCount(0);
  });

  test('manual mode recalculates every package and saves only the rate keys', {
    tag: [...ADMIN_PROPOSAL_HOUR_RATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const { captured } = await openTab(page);

    await page.getByTestId('hour-rate-mode-manual').click();
    await page.getByTestId('hour-rate-manual-input').fill('60.000');

    // Live preview: 60.000 with 10% off → 54.000/h over 60h → 3.240.000
    await expect(page.getByTestId('hour-rate-rate-7')).toContainText('54.000');
    await expect(page.getByTestId('hour-rate-total-7')).toContainText('3.240.000');

    await page.getByTestId('hour-rate-save').click();
    await expect(page.getByTestId('hour-rate-save')).toBeDisabled();

    expect(captured).toHaveLength(1);
    const cj = captured[0].content_json;
    expect(cj.hourPackagesMode).toBe('manual');
    expect(cj.manualHourlyRate).toBe(60000);
    expect(cj.manualCurrency).toBe('COP');
    // The catalog keeps owning the structure.
    expect(cj.hourlyRate).toBe(30000);
    expect(cj.packages).toHaveLength(2);
  });

  test('a per-package rate overrides the base rate for that package only', {
    tag: [...ADMIN_PROPOSAL_HOUR_RATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const { captured } = await openTab(page, {
      proposal: buildProposal({
        hourPackagesMode: 'manual', manualHourlyRate: 60000, manualCurrency: 'COP',
      }),
    });

    await page.getByTestId('hour-rate-override-8').fill('100.000');
    await expect(page.getByTestId('hour-rate-rate-8')).toContainText('100.000');
    await expect(page.getByTestId('hour-rate-rate-7')).toContainText('54.000');

    await page.getByTestId('hour-rate-save').click();
    await expect(page.getByTestId('hour-rate-save')).toBeDisabled();

    expect(captured[0].content_json.manualPackageRates).toEqual([
      { packageId: 8, hourlyRate: 100000 },
    ]);
  });

  test('the manual rate is kept when switching back to automatic', {
    tag: [...ADMIN_PROPOSAL_HOUR_RATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await openTab(page, {
      proposal: buildProposal({
        hourPackagesMode: 'manual', manualHourlyRate: 60000, manualCurrency: 'COP',
      }),
    });
    await expect(page.getByTestId('hour-rate-rate-8')).toContainText('60.000');

    await page.getByTestId('hour-rate-mode-auto').click();
    await expect(page.getByTestId('hour-rate-rate-8')).toContainText('30.000');

    await page.getByTestId('hour-rate-mode-manual').click();
    await expect(page.getByTestId('hour-rate-manual-input')).toHaveValue('60.000');
    await expect(page.getByTestId('hour-rate-rate-8')).toContainText('60.000');
  });

  test('restoring the catalog values undoes the manual rates without leaving manual', {
    tag: [...ADMIN_PROPOSAL_HOUR_RATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const { captured } = await openTab(page, {
      proposal: buildProposal({
        hourPackagesMode: 'manual', manualHourlyRate: 60000, manualCurrency: 'COP',
        manualPackageRates: [{ packageId: 8, hourlyRate: 100000 }],
      }),
    });
    await expect(page.getByTestId('hour-rate-rate-8')).toContainText('100.000');

    await page.getByTestId('hour-rate-reset-catalog').click();

    // Every row back on the catalog rate: Pro 30.000 −10% → 27.000, Ágil 30.000.
    await expect(page.getByTestId('hour-rate-rate-7')).toContainText('27.000');
    await expect(page.getByTestId('hour-rate-rate-8')).toContainText('30.000');
    await expect(page.getByTestId('hour-rate-manual-input')).toHaveValue('30.000');
    // Restoring does not flip the proposal back to automatic.
    await expect(page.getByTestId('hour-rate-mode-hint')).toContainText('su propia tarifa');
    // Nothing left to restore, so the action disables itself.
    await expect(page.getByTestId('hour-rate-reset-catalog')).toBeDisabled();

    await page.getByTestId('hour-rate-save').click();
    await expect(page.getByTestId('hour-rate-save')).toBeDisabled();

    const cj = captured[0].content_json;
    expect(cj.hourPackagesMode).toBe('manual');
    expect(cj.manualHourlyRate).toBe(30000);
    expect(cj.manualPackageRates).toBeUndefined();
  });

  test('a proposal without the section is offered to create it', {
    tag: [...ADMIN_PROPOSAL_HOUR_RATE, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const data = buildProposal();
    data.sections = [];
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
        };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(data) };
      }
      if (apiPath.startsWith('hour-packages/admin/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(CATALOG) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, {
      waitUntil: 'domcontentloaded',
    });
    await page.getByRole('tab', { name: 'Tarifa por hora' }).click();

    await expect(page.getByTestId('hour-rate-no-section'))
      .toContainText('todavía no tiene la sección');
    await expect(page.getByTestId('hour-rate-create-section')).toHaveText('Crear la sección');
    // Nothing to price yet, so no preview table is rendered at all.
    await expect(page.getByTestId('hour-rate-preview')).toHaveCount(0);
  });
});

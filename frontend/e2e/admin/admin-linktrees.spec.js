/**
 * E2E tests for the Linktrees panel module.
 *
 * Covers flow: admin-linktrees
 *   - Creating a linktree (name + handle) lands on the editor.
 *   - Saving buttons that violate tier cardinality surfaces the backend error.
 *   - Deleting a linktree after confirmation.
 *   - Assigning a linktree as a QR card destination.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_LINKTREES } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const TREE_ID = '11111111-1111-1111-1111-111111111111';

const existingTree = {
  id: TREE_ID,
  handle: 'gustavo',
  name: 'Gustavo',
  kind: 'personal',
  display_name: 'Gustavo Pérez',
  role: 'Co Founder & CEO',
  bio: '',
  avatar: null,
  claim_line_1: '',
  claim_line_2: '',
  badge_text: '',
  footer_tagline: 'DISEÑO · CÓDIGO · RESULTADOS',
  show_brand_header: true,
  pwa_enabled: true,
  pwa_title: 'Guarda la tarjeta en tu teléfono',
  pwa_description: 'Queda como un ícono en tu pantalla de inicio.',
  vcard_first_name: 'Gustavo',
  vcard_last_name: 'Pérez',
  vcard_org: 'ProjectApp.',
  vcard_email: 'team@projectapp.co',
  vcard_tel: '+573238122373',
  vcard_url: 'https://projectapp.co',
  is_active: true,
  public_path: '/lk/@gustavo',
  buttons_count: 1,
  buttons: [
    {
      id: 1, tier: 'primary', action: 'linkedin', label: 'Conectemos en LinkedIn',
      href: 'https://linkedin.com/in/x', icon: '', resolved_icon: 'linkedin',
      kind: 'url', is_pending: false, order: 0, is_active: true,
    },
  ],
  created_at: '2026-08-12T10:00:00Z',
  updated_at: '2026-08-12T10:00:00Z',
};

function countActivePrimaries(buttons) {
  return (buttons || []).filter((b) => (b.is_active ?? true) && b.tier === 'primary').length;
}

function setupLinktreesMock(page, { trees = [] } = {}) {
  let store = [...trees];
  return mockApi(page, async ({ apiPath, route }) => {
    const method = route.request().method();
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'linktrees/admin/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(store) };
    }
    if (apiPath === 'linktrees/admin/create/' && method === 'POST') {
      const payload = route.request().postDataJSON();
      const created = {
        ...existingTree,
        id: '22222222-2222-2222-2222-222222222222',
        buttons: [],
        buttons_count: 0,
        ...payload,
        handle: String(payload.handle || '').replace(/^@/, '').toLowerCase(),
      };
      created.public_path = `/lk/@${created.handle}`;
      store = [created, ...store];
      return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
    }
    if (apiPath.match(/^linktrees\/admin\/[^/]+\/update\/$/) && method === 'PATCH') {
      const payload = route.request().postDataJSON();
      if (payload.buttons && payload.buttons.length && countActivePrimaries(payload.buttons) !== 1) {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ buttons: ['Debe haber exactamente 1 botón principal (tier primary).'] }),
        };
      }
      const id = apiPath.split('/')[2];
      store = store.map((t) => (t.id === id ? { ...t, ...payload } : t));
      const updated = store.find((t) => t.id === id) || { ...existingTree, ...payload };
      return { status: 200, contentType: 'application/json', body: JSON.stringify(updated) };
    }
    if (apiPath.match(/^linktrees\/admin\/[^/]+\/delete\/$/) && method === 'DELETE') {
      const id = apiPath.split('/')[2];
      store = store.filter((t) => t.id !== id);
      return { status: 204, contentType: 'application/json', body: '' };
    }
    if (apiPath.match(/^linktrees\/admin\/[^/]+\/$/) && method === 'GET') {
      const id = apiPath.split('/')[2];
      const tree = store.find((t) => t.id === id) || existingTree;
      return { status: 200, contentType: 'application/json', body: JSON.stringify(tree) };
    }
    return null;
  });
}

test.describe('Admin Linktrees', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8900, role: 'admin', is_staff: true } });
  });

  test('creates a linktree and lands on the editor', {
    tag: [...ADMIN_LINKTREES, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-deep-link (admin panel E2E specs enter routes directly; sidebar navigation is covered by layout specs)
    await setupLinktreesMock(page, { trees: [] });
    await page.goto('/panel/linktrees');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId('linktree-new').click();
    await page.getByTestId('linktree-name-input').fill('Gustavo');
    await page.getByTestId('linktree-handle-input').fill('@Gustavo');
    await page.getByTestId('linktree-save').click();

    await expect(page).toHaveURL(/\/panel\/linktrees\/.+\/edit/);
    await expect(page.getByTestId('linktree-public-link')).toContainText('/lk/@gustavo');
  });

  test('violating the one-primary rule surfaces the backend error', {
    tag: [...ADMIN_LINKTREES, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await setupLinktreesMock(page, { trees: [existingTree] });
    await page.goto(`/panel/linktrees/${TREE_ID}/edit`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByTestId('linktree-button-row-0')).toBeVisible();
    await page.getByTestId('linktree-add-button').click();
    await page.locator('#lt-btn-tier-1').selectOption('primary');
    await page.getByTestId('linktree-button-label-1').fill('Segundo principal');
    await page.getByTestId('linktree-save').click();

    await expect(page.getByTestId('linktree-buttons-error')).toContainText('exactamente 1 botón principal');
  });

  test('confirming the delete removes the linktree', {
    tag: [...ADMIN_LINKTREES, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupLinktreesMock(page, { trees: [existingTree] });
    await page.goto('/panel/linktrees');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId(`linktree-delete-${TREE_ID}`).click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Sin linktrees todavía')).toBeVisible();
    await expect(page.getByTestId(`linktree-row-${TREE_ID}`)).not.toBeVisible();
  });

  test('assigns a linktree as QR card destination', {
    tag: [...ADMIN_LINKTREES, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const card = {
      id: '33333333-3333-3333-3333-333333333333',
      name: 'Tarjeta evento X',
      destination_url: '',
      destination_type: 'url',
      linktree: null,
      linktree_handle: null,
      linktree_name: null,
      is_active: true,
      created_at: '2026-08-01T10:00:00Z',
    };
    let cards = [card];
    await mockApi(page, async ({ apiPath, route }) => {
      const method = route.request().method();
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'linktrees/admin/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([existingTree]) };
      }
      if (apiPath === 'qr-cards/admin/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(cards) };
      }
      if (apiPath.match(/^qr-cards\/admin\/[^/]+\/update\/$/) && method === 'PATCH') {
        const payload = route.request().postDataJSON();
        cards = cards.map((c) => (c.id === card.id ? {
          ...c,
          ...payload,
          linktree_handle: payload.linktree ? existingTree.handle : null,
          linktree_name: payload.linktree ? existingTree.name : null,
        } : c));
        return { status: 200, contentType: 'application/json', body: JSON.stringify(cards[0]) };
      }
      return null;
    });

    await page.goto('/panel/qr-cards');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId(`qr-card-edit-${card.id}`).click();
    await page.getByTestId('qr-card-destination-type').getByRole('tab', { name: 'Linktree' }).click();
    await page.getByTestId('qr-card-linktree-select').selectOption(TREE_ID);
    await page.getByTestId('qr-card-save').click();

    await expect(page.getByText('Linktree: @gustavo')).toBeVisible();
  });
});

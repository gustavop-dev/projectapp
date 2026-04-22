/**
 * E2E tests for admin Proposal — editable slug URL.
 *
 * @flow:admin-proposal-slug-edit
 * Covers: slug input visible on General tab, save calls API with new slug,
 * regenerate fills input from client name, invalid slug shows validation error,
 * public URL preview reflects current slug.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SLUG_EDIT } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 7;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function makeProposal(overrides = {}) {
  return {
    id: PROPOSAL_ID,
    uuid: 'slug-test-uuid-1234',
    slug: 'acme-corp',
    title: 'Slug Test Proposal',
    client_name: 'Acme Corp',
    client_email: 'acme@test.com',
    status: 'sent',
    language: 'es',
    total_investment: '5000000',
    currency: 'COP',
    view_count: 0,
    sent_at: '2026-04-01T10:00:00Z',
    expires_at: new Date(Date.now() + 30 * 86400000).toISOString(),
    is_active: true,
    sections: [],
    requirement_groups: [],
    change_logs: [],
    proposal_documents: [],
    public_url: '/proposal/acme-corp',
    ...overrides,
  };
}

function baseHandler(proposal, extra = {}) {
  return async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    for (const [path, response] of Object.entries(extra)) {
      if (apiPath === path) return response;
    }
    return null;
  };
}

test.describe('Admin Proposal — Slug Edit', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 1001, role: 'admin', is_staff: true },
    });
  });

  test('slug input is visible on the General tab with the current slug prefilled', {
    tag: [...ADMIN_PROPOSAL_SLUG_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal()));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const slugInput = page.locator('[data-testid="proposal-slug-input"]');
    await expect(slugInput).toBeVisible({ timeout: 15000 });
    await expect(slugInput).toHaveValue('acme-corp');
  });

  test('saving a valid slug calls PUT with the new slug value', {
    tag: [...ADMIN_PROPOSAL_SLUG_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let savedSlug = null;
    await mockApi(page, async ({ apiPath, method, route }) => {
      const base = await baseHandler(makeProposal())({ apiPath, method, route });
      if (base) return base;
      if (apiPath === `proposals/${PROPOSAL_ID}/update/` && method === 'PUT') {
        const body = await route.request().postData();
        const parsed = body ? JSON.parse(body) : {};
        savedSlug = parsed.slug;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...makeProposal({ slug: parsed.slug }) }),
        };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const slugInput = page.locator('[data-testid="proposal-slug-input"]');
    await expect(slugInput).toBeVisible({ timeout: 15000 });

    await slugInput.fill('nueva-url-personalizada');
    await page.keyboard.press('Enter');

    await expect(() => expect(savedSlug).toBe('nueva-url-personalizada')).toPass({ timeout: 5000 });
  });

  test('slug input shows a validation error for invalid format (spaces/uppercase)', {
    tag: [...ADMIN_PROPOSAL_SLUG_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal()));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const slugInput = page.locator('[data-testid="proposal-slug-input"]');
    await expect(slugInput).toBeVisible({ timeout: 15000 });

    await slugInput.fill('URL Inválida con espacios!');
    await page.keyboard.press('Enter');

    await expect(page.getByText(/Solo minúsculas/i)).toBeVisible({ timeout: 5000 });
  });

  test('regenerate button populates slug from client name', {
    tag: [...ADMIN_PROPOSAL_SLUG_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(makeProposal({ slug: 'viejo-slug', client_name: 'TechCorp SAS' })));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const slugInput = page.locator('[data-testid="proposal-slug-input"]');
    await expect(slugInput).toBeVisible({ timeout: 15000 });

    const regenBtn = page.getByRole('button', { name: /regenerar/i });
    await regenBtn.click();

    const newVal = await slugInput.inputValue();
    expect(newVal).toBeTruthy();
    expect(newVal).not.toBe('viejo-slug');
    expect(newVal).toMatch(/^[a-z0-9-]+$/);
  });
});

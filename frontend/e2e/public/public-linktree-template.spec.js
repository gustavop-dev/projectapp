/**
 * E2E test for the public Linktree HTML-template handoff.
 *
 * This catches the regression where a published template URL is ignored and
 * visitors keep seeing the legacy Vue card instead of the template runtime.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PUBLIC_LINKTREE_VIEW } from '../helpers/flow-tags.js';

const TEMPLATE_RUNTIME_PATH = '/api/linktrees/public/gustavo/template/';

test('hands a published template URL to the public template runtime', {
  tag: [...PUBLIC_LINKTREE_VIEW, '@role:visitor', '@outcome:success'],
}, async ({ page }, testInfo) => {
  // quality: allow-deep-link (a visitor reaches a Linktree from its external QR or short-link entry point)
  // quality: allow-no-interaction (the handoff happens automatically on public-route entry; no page control exists before it)
  await mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'linktrees/public/gustavo/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ handle: 'gustavo', template_url: TEMPLATE_RUNTIME_PATH }),
      };
    }
    if (apiPath === 'linktrees/public/gustavo/template/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'text/html',
        body: '<main data-testid="template-runtime">Runtime de plantilla Gustavo</main>',
      };
    }
    return null;
  });

  const templateRuntimeUrl = new URL(TEMPLATE_RUNTIME_PATH, testInfo.project.use.baseURL).href;
  await page.goto('/lk/@gustavo', { waitUntil: 'domcontentloaded' });
  await page.waitForURL(templateRuntimeUrl);

  await expect(page).toHaveURL(templateRuntimeUrl);
  await expect(page.getByTestId('template-runtime')).toHaveText('Runtime de plantilla Gustavo');
});

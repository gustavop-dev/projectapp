/**
 * E2E tests for the public home page.
 *
 * The home flow is a guest landing: it must render and its interactive
 * elements must work. The FAQ accordion is the page's primary in-page
 * interaction, so it carries the flow's behavioral coverage.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_HOME } from '../helpers/flow-tags.js';

test.describe('Home Page', () => {
  test('toggling a FAQ item reveals then hides its answer', {
    tag: [...PUBLIC_HOME, '@role:guest'],
  }, async ({ page }) => {
    // Fails if the FAQ accordion stops opening/closing on click (broken
    // <details> binding or a regression in the section markup).
    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // quality: allow-fragile-selector (identical FAQ accordions; the first exercises the same toggle)
    const firstFaq = page.locator('details.faq-item').first();
    await firstFaq.locator('summary').scrollIntoViewIfNeeded();
    const answer = firstFaq.locator('p[itemprop="text"]');

    // Closed on first render.
    await expect(firstFaq).not.toHaveAttribute('open', /.*/);
    await expect(answer).toBeHidden();

    // Opening reveals the answer.
    await firstFaq.locator('summary').click();
    await expect(firstFaq).toHaveAttribute('open', /.*/);
    await expect(answer).toBeVisible();

    // Clicking again collapses it.
    await firstFaq.locator('summary').click();
    await expect(firstFaq).not.toHaveAttribute('open', /.*/);
  });
});

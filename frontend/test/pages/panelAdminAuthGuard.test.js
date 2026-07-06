/**
 * Guard test: every page under pages/panel/ must opt into the `admin-auth`
 * middleware explicitly. Nuxt middleware here are named (not global), so a
 * page that forgets the meta ships unprotected — this test makes that a
 * failing build instead of a silent hole (see the /panel/emails regression).
 */
const fs = require('fs');
const path = require('path');

const PANEL_PAGES_DIR = path.resolve(__dirname, '../../pages/panel');

// Pages intentionally outside the admin-auth boundary.
const ADMIN_AUTH_ALLOWLIST = new Set([
  'login.vue', // static bounce page to the Django admin login
]);

function collectVueFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return collectVueFiles(full);
    return entry.name.endsWith('.vue') ? [full] : [];
  });
}

describe('panel pages admin-auth guard', () => {
  const pages = collectVueFiles(PANEL_PAGES_DIR).map((file) => ({
    file,
    relative: path.relative(PANEL_PAGES_DIR, file),
    source: fs.readFileSync(file, 'utf8'),
  }));

  it('finds panel pages to audit', () => {
    expect(pages.length).toBeGreaterThan(30);
  });

  it('every panel page declares definePageMeta', () => {
    const missing = pages
      .filter(({ source }) => !/definePageMeta\s*\(/.test(source))
      .map(({ relative }) => relative);
    expect(missing).toEqual([]);
  });

  it("every panel page (except allowlist) opts into the 'admin-auth' middleware", () => {
    const unprotected = pages
      .filter(({ relative }) => !ADMIN_AUTH_ALLOWLIST.has(relative))
      .filter(({ source }) => !/['"]admin-auth['"]/.test(source))
      .map(({ relative }) => relative);
    expect(unprotected).toEqual([]);
  });
});

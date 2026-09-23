/**
 * E2E tests for the Linktree HTML-template editor.
 *
 * These tests catch regressions where a validated package cannot be published,
 * upload diagnostics disappear, a failed library request cannot recover, or a
 * historical preview executes markup outside its sandbox.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_LINKTREE_TEMPLATES } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const TREE_ID = '11111111-1111-1111-1111-111111111111';
const VALID_VERSION_ID = 'version-2026-09-valid';
const HISTORICAL_VERSION_ID = 'version-2026-08-archived';
const LIBRARY_TEMPLATE_ID = 'library-template-2026';
const TEMPLATES_PATH = `linktrees/admin/${TREE_ID}/templates/`;

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const existingTree = {
  id: TREE_ID,
  handle: 'gustavo',
  name: 'Tarjeta de Gustavo',
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
  buttons_count: 0,
  buttons: [],
  created_at: '2026-09-01T10:00:00Z',
  updated_at: '2026-09-01T10:00:00Z',
};

const validVersion = {
  id: VALID_VERSION_ID,
  name: 'Tarjeta corporativa',
  status: 'valid',
  active: false,
  issues: [],
  preview_url: '/api/linktrees/public/gustavo/template-preview/valid/',
  screenshots: {
    320: '/template-captures/valid-320.png',
    375: '/template-captures/valid-375.png',
    430: '/template-captures/valid-430.png',
  },
  created_at: '2026-09-15T10:00:00Z',
};

const activeVersion = {
  ...validVersion,
  id: 'version-2026-09-active',
  name: 'Tarjeta publicada actual',
  active: true,
  published_at: '2026-09-16T10:00:00Z',
};

const historicalVersion = {
  ...validVersion,
  id: HISTORICAL_VERSION_ID,
  name: 'Tarjeta archivada validada',
  active: false,
  published_at: '2026-08-20T10:00:00Z',
  preview_url: '/api/linktrees/public/gustavo/template-preview/archived/',
  screenshots: {
    320: '/template-captures/archived-320.png',
    375: '/template-captures/archived-375.png',
    430: '/template-captures/archived-430.png',
  },
};

function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

async function setupTemplateEditorMock(page, {
  initialVersions = [],
  initialActiveVersionId = null,
  invalidUpload = false,
  failFirstLibraryLoad = false,
  templates = [],
} = {}) {
  let versions = [...initialVersions];
  let activeVersionId = initialActiveVersionId;
  let libraryLoads = 0;
  let refreshedActiveVersionId = null;

  await mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/' && method === 'GET') return authCheck;
    if (apiPath === 'linktrees/admin/' && method === 'GET') return json([existingTree]);
    if (apiPath === `linktrees/admin/${TREE_ID}/` && method === 'GET') return json(existingTree);

    if (apiPath === TEMPLATES_PATH && method === 'GET') {
      libraryLoads += 1;
      if (failFirstLibraryLoad && libraryLoads === 1) return json({ detail: 'Servicio no disponible.' }, 500);
      refreshedActiveVersionId = activeVersionId;
      return json({
        templates,
        versions,
        active_version_id: activeVersionId,
        next_offset: null,
        can_share: false,
      });
    }

    if (apiPath === TEMPLATES_PATH && method === 'POST') {
      if (invalidUpload) {
        return json({
          issues: [{ severity: 'error', message: 'El manifest debe declarar spec: "1.0".', file: 'manifest.json', line: 1 }],
        }, 400);
      }
      versions = [validVersion];
      activeVersionId = null;
      return json(validVersion, 201);
    }

    if (apiPath === `${TEMPLATES_PATH}${VALID_VERSION_ID}/publish/` && method === 'POST') {
      activeVersionId = VALID_VERSION_ID;
      versions = versions.map((version) => ({ ...version, active: version.id === VALID_VERSION_ID }));
      return json({ ...validVersion, active: true, published_at: '2026-09-23T10:00:00Z' });
    }

    return null;
  });

  return {
    getRefreshedActiveVersionId: () => refreshedActiveVersionId,
  };
}

async function openTemplateEditor(page, mockOptions) {
  const fixture = await setupTemplateEditorMock(page, mockOptions);
  await page.goto('/panel/linktrees', { waitUntil: 'domcontentloaded' });
  await expect(page.getByTestId(`linktree-row-${TREE_ID}`)).toContainText('Tarjeta de Gustavo');
  await page.getByTestId(`linktree-actions-${TREE_ID}`).click();
  await page.getByTestId(`linktree-edit-${TREE_ID}`).click();
  await expect(page.getByTestId('linktree-template-editor')).toContainText('Plantilla HTML');
  return fixture;
}

test.describe('Admin Linktree HTML templates', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-template-admin-token',
      userAuth: { id: 8900, role: 'admin', is_staff: true },
    });
  });

  test('publishes a package after its HTML-template validation succeeds', {
    tag: [...ADMIN_LINKTREE_TEMPLATES, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the Linktrees list is setup; the editor is reached through its real Edit action)
    const fixture = await openTemplateEditor(page);

    await page.getByTestId('template-file-input').setInputFiles([
      {
        name: 'template.html',
        mimeType: 'text/html',
        buffer: Buffer.from('<main><h1>{{name}}</h1>{{#links}}<a data-link href="{{url}}">{{label}}</a>{{/links}}</main>'),
      },
      {
        name: 'manifest.json',
        mimeType: 'application/json',
        buffer: Buffer.from('{"spec":"1.0","fonts":[],"slots":{},"assets":[],"editable_assets":[],"motion":false}'),
      },
    ]);
    await page.getByTestId('template-upload-validate').click();
    await expect(page.getByTestId('template-valid')).toHaveText('La plantilla pasó la validación. Revisa las tres capturas antes de publicar.');

    await page.getByTestId('template-publish').click();
    await expect(page.getByRole('status')).toHaveText('Plantilla publicada. La URL de la tarjeta se conserva.');
    await expect(page.getByTestId('template-version-select')).toHaveValue(VALID_VERSION_ID);
    await expect.poll(fixture.getRefreshedActiveVersionId).toBe(VALID_VERSION_ID);
  });

  test('shows the manifest location when a package is malformed', {
    tag: [...ADMIN_LINKTREE_TEMPLATES, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the Linktrees list is setup; the editor is reached through its real Edit action)
    await openTemplateEditor(page, { invalidUpload: true });

    await page.getByTestId('template-file-input').setInputFiles([
      { name: 'template.html', mimeType: 'text/html', buffer: Buffer.from('<main>Sin manifiesto válido</main>') },
      { name: 'manifest.json', mimeType: 'application/json', buffer: Buffer.from('{}') },
    ]);
    await page.getByTestId('template-upload-validate').click();

    await expect(page.getByTestId('template-upload-errors')).toHaveText('El manifest debe declarar spec: "1.0". (manifest.json:1)');
  });

  test('retries a failed template-library request and restores its library', {
    tag: [...ADMIN_LINKTREE_TEMPLATES, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the Linktrees list is setup; the editor is reached through its real Edit action)
    await openTemplateEditor(page, {
      failFirstLibraryLoad: true,
      templates: [{ id: LIBRARY_TEMPLATE_ID, name: 'Biblioteca de septiembre', is_shared: false }],
    });

    await expect(page.getByTestId('template-request-error')).toHaveText('No se pudo cargar la biblioteca de plantillas.');
    await page.getByRole('button', { name: 'Reintentar carga' }).click();

    await expect(page.getByTestId('template-library-select')).toHaveValue(LIBRARY_TEMPLATE_ID);
    await expect(page.getByTestId('template-library-select')).toContainText('Biblioteca de septiembre');
  });

  test('inspects a historical validated version through sandboxed captures', {
    tag: [...ADMIN_LINKTREE_TEMPLATES, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the Linktrees list is setup; the historical version is reached through its real Edit action)
    await openTemplateEditor(page, {
      initialVersions: [activeVersion, historicalVersion],
      initialActiveVersionId: activeVersion.id,
    });

    await page.getByTestId('template-version-select').selectOption(HISTORICAL_VERSION_ID);
    const preview = page.getByTestId('template-sandbox-preview');
    await expect(preview).toHaveAttribute('sandbox', '');
    await expect(preview).toHaveAttribute('title', 'Plantilla a 320 px');
    await expect(page.getByTestId('template-screenshots').getByAltText('Captura validada a 320 px')).toHaveAttribute('src', '/template-captures/archived-320.png');
    await expect(page.getByTestId('template-screenshots').getByAltText('Captura validada a 375 px')).toHaveAttribute('src', '/template-captures/archived-375.png');
    await expect(page.getByTestId('template-screenshots').getByAltText('Captura validada a 430 px')).toHaveAttribute('src', '/template-captures/archived-430.png');
  });
});

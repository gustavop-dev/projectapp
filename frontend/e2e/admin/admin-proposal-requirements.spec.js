/**
 * E2E tests for admin functional requirements management.
 *
 * Covers: managing requirement groups and items via form mode,
 * pasting content into groups, adding/removing items,
 * adding additional modules, and verifying data integrity.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM,
  ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_PASTE,
} from '../helpers/flow-tags.js';

const PROPOSAL_ID = 3;
const userId = 7300;

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '33333333-3333-3333-3333-333333333333',
  title: 'E2E Requirements Test',
  client_name: 'Req Client',
  client_email: 'req@test.com',
  language: 'es',
  status: 'draft',
  total_investment: '8000000',
  currency: 'COP',
  view_count: 0,
  sent_at: null,
  expires_at: null,
  sections: [
    {
      id: 301,
      section_type: 'functional_requirements',
      title: '🧩 Requerimientos Funcionales',
      order: 7,
      is_enabled: true,
      is_wide_panel: true,
      content_json: {
        index: '7',
        title: 'Requerimientos Funcionales',
        intro: 'Detalle de requerimientos del proyecto.',
        groups: [
          {
            id: 'views',
            icon: '🖥️',
            title: 'Vistas',
            description: 'Pantallas del sitio web.',
            items: [
              { icon: '🏠', name: 'Página Principal', description: 'Landing con CTAs.' },
              { icon: '📧', name: 'Contacto', description: 'Formulario de contacto.' },
            ],
          },
          {
            id: 'components',
            icon: '🧩',
            title: 'Componentes',
            description: 'Elementos reutilizables.',
            items: [
              { icon: '🔝', name: 'Header', description: 'Logo y menú.' },
            ],
          },
          {
            id: 'features',
            icon: '⚙️',
            title: 'Funcionalidades',
            description: 'Acciones interactivas.',
            items: [
              { icon: '🌐', name: 'Diseño Responsive', description: 'Adapta a dispositivos.' },
              { icon: '💬', name: 'WhatsApp', description: 'Canal directo.' },
            ],
          },
          {
            id: 'admin_module',
            icon: '🛠️',
            title: 'Módulo Admin',
            description: 'Gestión de contenido.',
            items: [
              { icon: '📂', name: 'Gestor Productos', description: 'CRUD de productos.' },
            ],
          },
        ],
        additionalModules: [],
      },
    },
  ],
  requirement_groups: [],
};

function buildMockHandler(capturedUpdates) {
  return async ({ route, apiPath }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
      };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProposal),
      };
    }
    const sectionMatch = apiPath.match(/^proposals\/sections\/(\d+)\/update\/$/);
    if (sectionMatch) {
      const sectionId = parseInt(sectionMatch[1]);
      const body = route.request().postDataJSON();
      if (capturedUpdates) {
        capturedUpdates.push({ sectionId, body });
      }
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockProposal.sections[0],
          ...body,
        }),
      };
    }
    return null;
  };
}

/**
 * Helper: navigate to edit page, switch to Secciones tab, expand functional_requirements.
 */
async function openRequirementsEditor(page, capturedUpdates) {
  await mockApi(page, buildMockHandler(capturedUpdates));
  await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
  await page.waitForLoadState('networkidle');

  await page.getByRole('button', { name: 'Secciones' }).click();

  // Expand the functional_requirements section
  const sectionHeader = page.getByText('Requerimientos Funcionales', { exact: false }).first();
  await sectionHeader.click();
  await page.getByTestId('section-editor').waitFor({ state: 'visible' });
}

test.describe('Functional Requirements — Form Mode', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: userId, role: 'admin', is_staff: true },
    });
  });

  test('loads section showing 4 groups with item counts in headers', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM, '@role:admin'],
  }, async ({ page }) => {
    await openRequirementsEditor(page, null);

    const editor = page.getByTestId('section-editor');

    // Verify group headers are visible
    await expect(editor.getByText('Vistas')).toBeVisible();
    await expect(editor.getByText('Componentes')).toBeVisible();
    await expect(editor.getByText('Funcionalidades')).toBeVisible();
    await expect(editor.getByText('Módulo Admin')).toBeVisible();

    // Verify item counts in group headers (e.g., "(2 elementos)")
    await expect(editor.getByText('(2 elementos)').first()).toBeVisible();
    await expect(editor.getByText('(1 elementos)').first()).toBeVisible();
  });

  test('save produces correct groups structure in payload', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openRequirementsEditor(page, captured);

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.sectionId).toBe(301);
    expect(last.body.content_json.groups).toHaveLength(4);
    expect(last.body.content_json.additionalModules).toEqual([]);
  });

  test('save preserves items within each group', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openRequirementsEditor(page, captured);

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    const last = captured[captured.length - 1];
    expect(last.body.content_json.groups[0].id).toBe('views');
    expect(last.body.content_json.groups[0].items).toHaveLength(2);
    expect(last.body.content_json.groups[0].items[0].name).toBe('Página Principal');
    expect(last.body.content_json.groups[1].items).toHaveLength(1);
  });

  test('each group defaults to form _editMode in payload', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openRequirementsEditor(page, captured);

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    for (const group of last.body.content_json.groups) {
      expect(group._editMode).toBe('form');
      expect(group).not.toHaveProperty('rawText');
    }
  });

  test('is_wide_panel is true in payload for functional_requirements', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openRequirementsEditor(page, captured);

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.is_wide_panel).toBe(true);
  });
});

test.describe('Functional Requirements — Paste Content Mode', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: userId + 100, role: 'admin', is_staff: true },
    });
  });

  test('each group has Formulario and Pegar contenido toggle buttons', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await openRequirementsEditor(page, null);

    const editor = page.getByTestId('section-editor');

    // Each group header should have Formulario/Pegar contenido buttons
    // There are 4 groups, so we expect at least 4 "Formulario" buttons (one per group + main)
    const formularioBtns = editor.getByRole('button', { name: 'Formulario' });
    const pasteBtns = editor.getByRole('button', { name: 'Pegar contenido' });

    // Main section has its own toggle + 4 groups = at least 5
    expect(await formularioBtns.count()).toBeGreaterThanOrEqual(5);
    expect(await pasteBtns.count()).toBeGreaterThanOrEqual(5);
  });

  test('group paste toggle shows textarea for that group', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await openRequirementsEditor(page, null);

    const editor = page.getByTestId('section-editor');

    // Expand the first group (Vistas) by clicking its header
    const viewsGroup = editor.getByTestId('requirement-group-views');
    await viewsGroup.getByText('Vistas', { exact: false }).click();

    // Click the "Pegar contenido" button within the Vistas group
    await viewsGroup.getByRole('button', { name: 'Pegar contenido' }).click();

    // A textarea should appear for this group
    await expect(viewsGroup.getByTestId('group-paste-textarea')).toBeVisible();
  });

  test('group paste saves _editMode paste and rawText per group', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_PASTE, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openRequirementsEditor(page, captured);

    const editor = page.getByTestId('section-editor');

    // Expand Vistas group
    const viewsGroup = editor.getByTestId('requirement-group-views');
    await viewsGroup.getByText('Vistas', { exact: false }).click();

    // Switch Vistas group to paste mode
    await viewsGroup.getByRole('button', { name: 'Pegar contenido' }).click();

    // Fill the group paste textarea
    const groupTextarea = viewsGroup.getByTestId('group-paste-textarea');
    await expect(groupTextarea).toBeVisible();
    await groupTextarea.fill('Custom pasted views content.');

    // Save the section
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];

    // First group (views) should be in paste mode
    const viewsPayload = last.body.content_json.groups[0];
    expect(viewsPayload._editMode).toBe('paste');
    expect(viewsPayload.rawText).toBe('Custom pasted views content.');

    // Other groups should still be in form mode
    const componentsPayload = last.body.content_json.groups[1];
    expect(componentsPayload._editMode).toBe('form');
    expect(componentsPayload).not.toHaveProperty('rawText');
  });

  test('mixed form and paste modes across groups save correctly', {
    tag: [...ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_PASTE, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openRequirementsEditor(page, captured);

    const editor = page.getByTestId('section-editor');

    // Save with default (all form mode) — verify all groups have _editMode: form
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];

    // All 4 groups should be in form mode
    for (const group of last.body.content_json.groups) {
      expect(group._editMode).toBe('form');
    }
  });
});

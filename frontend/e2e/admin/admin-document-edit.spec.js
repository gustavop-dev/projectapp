/**
 * E2E tests for admin document edit flow.
 *
 * @flow:admin-document-edit
 * Covers: edit form pre-filled with existing document data, save updates document,
 *         private fixed/custom notes (including read-only copy), status change,
 *         back link navigation, download PDF action, copy/paste markdown content
 *         toolbar buttons, template style switch (Amigable/Profesional) toggling
 *         the preview theme, and the dual-style PDF download dropdown.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_EDIT } from '../helpers/flow-tags.js';
import { viewportUse } from '../helpers/viewports.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDocument = {
  id: 1, title: 'Contrato de Servicios', status: 'draft',
  content: '# Contrato\n\nEste es el contenido del contrato.',
  client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
};

const legalHeaderTitle = 'Carta jurídica dirigida a la Superintendencia de Industria y Comercio sobre la respuesta al requerimiento de información del expediente 2026-004817';
const legalHeaderClient = 'Grupo Empresarial de Soluciones Jurídicas y Administrativas del Caribe S.A.S.';
const longHeaderDocument = {
  ...mockDocument,
  title: legalHeaderTitle,
  client: 57,
  client_display_name: legalHeaderClient,
};

const issuedCollectionAccount = {
  ...mockDocument,
  document_type_code: 'collection_account',
  commercial_status: 'issued',
  client_email_subject: 'Cuenta emitida',
  client_custom_notes: [
    { title: 'Conciliación', content: 'Pago pendiente de confirmar.' },
  ],
};

async function mockResponsiveHeaderApi(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([longHeaderDocument]) };
    }
    if (apiPath === 'documents/1/detail/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(longHeaderDocument) };
    }
    if (apiPath === 'document-folders/' || apiPath === 'document-tags/' || apiPath === 'accounting/projects/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === 'proposals/client-profiles/status-counts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ all: 0, active: 0, orphans: 0, inactive: 0 }) };
    }
    if (apiPath === 'proposals/client-profiles/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

async function readResponsiveHeaderLayout(page) {
  await mockResponsiveHeaderApi(page);
  await page.goto('/en-us/panel/documents/1/edit', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/\/en-us\/panel\/documents\/1\/edit$/);

  const title = page.getByTestId('doc-editor-title');
  const metadata = page.getByTestId('doc-editor-metadata');
  const actions = page.getByTestId('doc-header-actions');
  const actionTrigger = page.getByTestId('doc-document-actions-trigger');
  const cancel = page.getByTestId('doc-cancel');
  const save = page.getByTestId('doc-save');

  await expect(title).toBeVisible();
  await expect(title).toHaveText(legalHeaderTitle);
  await expect(title).toHaveAttribute('title', legalHeaderTitle);
  await expect(metadata.getByTitle(legalHeaderClient)).toHaveCount(1);
  await expect(actionTrigger).toContainText('Acciones');

  // This click catches the regression where the action group was visually
  // present but squeezed enough that the document-output choices were unusable.
  await actionTrigger.click();
  await expect(page.getByRole('menuitem', { name: 'Descargar PDF · Amigable', exact: true })).toHaveText('Descargar PDF · Amigable');
  await expect(page.getByRole('menuitem', { name: 'Descargar PDF · Profesional', exact: true })).toHaveText('Descargar PDF · Profesional');

  const layout = await page.evaluate(() => {
    const getBox = (testId) => {
      const element = document.querySelector(`[data-testid="${testId}"]`);
      const box = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return {
        x: box.x,
        y: box.y,
        right: box.right,
        bottom: box.bottom,
        width: box.width,
        height: box.height,
        whiteSpace: style.whiteSpace,
        scrollWidth: element.scrollWidth,
        clientWidth: element.clientWidth,
      };
    };
    const titleElement = document.querySelector('[data-testid="doc-editor-title"]');
    const titleStyle = getComputedStyle(titleElement);
    const titleBox = titleElement.getBoundingClientRect();
    return {
      pageScrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      title: {
        ...getBox('doc-editor-title'),
        lineClamp: titleStyle.webkitLineClamp,
        lineHeight: Number.parseFloat(titleStyle.lineHeight),
        lineCount: Math.round(titleBox.height / Number.parseFloat(titleStyle.lineHeight)),
      },
      metadata: getBox('doc-editor-metadata'),
      actions: getBox('doc-header-actions'),
      actionTrigger: getBox('doc-document-actions-trigger'),
      cancel: getBox('doc-cancel'),
      save: getBox('doc-save'),
    };
  });

  expect(layout.pageScrollWidth).toBeLessThanOrEqual(layout.viewportWidth);
  expect(layout.title.lineClamp).toBe('2');
  expect(layout.title.lineCount).toBeLessThanOrEqual(2);
  expect(layout.actionTrigger.scrollWidth).toBeLessThanOrEqual(layout.actionTrigger.clientWidth);
  expect(layout.cancel.whiteSpace).toBe('nowrap');
  expect(layout.save.whiteSpace).toBe('nowrap');
  expect(layout.cancel.scrollWidth).toBeLessThanOrEqual(layout.cancel.clientWidth);
  expect(layout.save.scrollWidth).toBeLessThanOrEqual(layout.save.clientWidth);
  expect(layout.actions.right).toBeLessThanOrEqual(layout.viewportWidth);

  return layout;
}

test.describe('Admin Document Edit', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test.describe('responsive document header', () => {
    test.describe('compact', { tag: ['@viewport:compact'] }, () => {
      test.use(viewportUse('compact'));

      // R-canvas-01: a long legal title pushed the output and edit controls past a phone viewport.
      test('compact header prevents a legal title from overflowing action controls', {
        tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display', '@responsive:canvas'],
      }, async ({ page }) => {
        // quality: allow-duplicate (per-viewport contract: admin-document-edit @ 412px)
        // quality: allow-deep-link (the editor header is the documented display surface; route navigation is covered separately)
        const layout = await readResponsiveHeaderLayout(page);

        expect(layout.actions.y).toBeGreaterThanOrEqual(layout.metadata.bottom);
      });
    });

    test.describe('portrait', { tag: ['@viewport:portrait'] }, () => {
      test.use(viewportUse('portrait'));

      // R-canvas-02: a tablet portrait layout let the action labels wrap under a long title.
      test('portrait header prevents a legal title from overflowing action controls', {
        tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display', '@responsive:canvas'],
      }, async ({ page }) => {
        // quality: allow-duplicate (per-viewport contract: admin-document-edit @ 835px)
        // quality: allow-deep-link (the editor header is the documented display surface; route navigation is covered separately)
        const layout = await readResponsiveHeaderLayout(page);

        expect(layout.actions.y).toBeGreaterThanOrEqual(layout.metadata.bottom);
      });
    });

    test.describe('landscape', { tag: ['@viewport:landscape'] }, () => {
      test.use(viewportUse('landscape'));

      // R-canvas-03: a wide editor gave the title all available width and squeezed the action group.
      test('landscape header reserves an action track beside a legal title', {
        tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display', '@responsive:canvas'],
      }, async ({ page }) => {
        // quality: allow-duplicate (per-viewport contract: admin-document-edit @ 1195px)
        // quality: allow-deep-link (the editor header is the documented display surface; route navigation is covered separately)
        const layout = await readResponsiveHeaderLayout(page);

        expect(layout.title.right).toBeLessThanOrEqual(layout.actions.x);
        expect(layout.actions.right).toBeGreaterThan(layout.actions.x);
      });
    });

    test.describe('desktop', { tag: ['@viewport:desktop'] }, () => {
      test.use(viewportUse('desktop'));

      // R-canvas-04: desktop action controls lost their own width when a legal title grew.
      test('desktop header reserves an action track beside a legal title', {
        tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display', '@responsive:canvas'],
      }, async ({ page }) => {
        // quality: allow-duplicate (per-viewport contract: admin-document-edit @ 1440px)
        // quality: allow-deep-link (the editor header is the documented display surface; route navigation is covered separately)
        const layout = await readResponsiveHeaderLayout(page);

        expect(layout.title.right).toBeLessThanOrEqual(layout.actions.x);
        expect(layout.actions.right).toBeGreaterThan(layout.actions.x);
      });
    });

    test.describe('wide', { tag: ['@viewport:wide'] }, () => {
      test.use(viewportUse('wide'));

      // R-canvas-05: an ultra-wide editor regressed to an unconstrained title despite available space.
      test('wide header keeps a legal title clamped beside its action track', {
        tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display', '@responsive:canvas'],
      }, async ({ page }) => {
        // quality: allow-duplicate (per-viewport contract: admin-document-edit @ 2560px)
        // quality: allow-deep-link (the editor header is the documented display surface; route navigation is covered separately)
        const layout = await readResponsiveHeaderLayout(page);

        expect(layout.title.right).toBeLessThanOrEqual(layout.actions.x);
        expect(layout.actions.right).toBeGreaterThan(layout.actions.x);
      });
    });
  });

  test('renders edit form pre-filled with existing document data', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    const documentWithNote = {
      ...mockDocument,
      client_email_subject: 'Contrato listo para revisión',
      client_email_body: 'Hola Ana,\n\nEl contrato está listo para tu revisión.',
      client_whatsapp_message: 'Hola Ana, te envié el contrato para revisión.',
      client_custom_notes: [
        { title: 'Seguimiento', content: 'Confirmar recepción el viernes.' },
      ],
    };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([mockDocument]) };
      }
      if (apiPath === 'document-folders/' || apiPath === 'document-tags/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithNote) };
      }
      return null;
    });
    await page.goto('/panel/documents');
    await page.getByTestId('document-open-1').click();

    await expect(page.getByRole('textbox', { name: /^Título$/i })).toHaveValue('Contrato de Servicios');
    const noteButton = page.getByTestId('doc-client-note-open');
    await expect(noteButton).toHaveAccessibleName('Editar notas');
    await noteButton.click();
    await expect(page.getByTestId('client-note-subject')).toHaveValue('Contrato listo para revisión');
    await expect(page.getByTestId('client-note-email')).toHaveValue('Hola Ana,\n\nEl contrato está listo para tu revisión.');
    await expect(page.getByTestId('client-note-whatsapp')).toHaveValue('Hola Ana, te envié el contrato para revisión.');
    await expect(page.getByTestId('client-note-custom-title-0')).toHaveValue('Seguimiento');
    await expect(page.getByTestId('client-note-custom-content-0'))
      .toHaveValue('Confirmar recepción el viernes.');
  });

  test('an issued collection account keeps the Ver notas action', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (/panel/documents is the module entry; from
    // there this test follows the real list → editor → note interaction)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([issuedCollectionAccount]) };
      }
      if (apiPath === 'document-folders/' || apiPath === 'document-tags/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(issuedCollectionAccount) };
      }
      return null;
    });
    await page.goto('/panel/documents');
    await page.getByTestId('document-open-1').click();

    const noteButton = page.getByTestId('doc-client-note-open');
    await expect(noteButton).toHaveText('Ver notas');
    await noteButton.click();
    await expect(page.getByTestId('client-note-subject')).toHaveValue('Cuenta emitida');
    await expect(page.getByTestId('client-note-subject')).toBeDisabled();
    await expect(page.getByTestId('client-note-custom-content-0')).toBeDisabled();
    await expect(page.getByTestId('client-note-submit')).toHaveCount(0);
    await expect(page.getByTestId('client-note-add-custom')).toHaveCount(0);
  });

  test('copies a custom note from an issued collection account', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([issuedCollectionAccount]) };
      }
      if (apiPath === 'document-folders/' || apiPath === 'document-tags/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(issuedCollectionAccount) };
      }
      return null;
    });
    await page.goto('/panel/documents');
    await page.getByTestId('document-open-1').click();
    await page.getByTestId('doc-client-note-open').click();

    const copyButton = page.getByTestId('client-note-custom-copy-content-0');
    await expect(copyButton).toHaveAttribute('data-panel-action', 'copy');
    await expect(copyButton).toHaveAccessibleName('Copiar contenido de la nota 1');
    await copyButton.click();
    await expect(copyButton).toHaveAccessibleName('Copiado: contenido de la nota 1');
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText()))
      .toBe('Pago pendiente de confirmar.');
  });

  test('back link navigates to documents list', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocument) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const backLink = page.getByRole('link', { name: /Volver a documentos/i });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', /\/panel\/documents/);
  });

  test('saving changes shows success feedback after the PATCH response', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocument) };
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDocument, title: 'Contrato Actualizado' }) };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const titleInput = page.getByRole('textbox', { name: /^Título$/i });
    await titleInput.fill('Contrato Actualizado');
    const requestPromise = page.waitForRequest(
      (request) => request.url().includes('/api/documents/1/update/')
        && request.method() === 'PATCH',
    );
    // Por testid: el aviso de cambios sin guardar aporta su propio "Guardar
    // ahora", así que un match por rol dejó de identificar un solo botón.
    await page.getByTestId('doc-save').click();
    const request = await requestPromise;

    expect(request.postDataJSON().title).toBe('Contrato Actualizado');
    await expect(page.getByText('Documento guardado', { exact: true })).toBeVisible();
  });

  test('saves edited notes', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const documentWithNote = {
      ...mockDocument,
      content_markdown: '# Contrato\n\nEste es el contenido del contrato.',
      client_email_subject: 'Contrato listo',
      client_email_body: 'Hola Ana,\n\nEl contrato está listo.',
      client_whatsapp_message: 'Hola Ana, revisa el contrato en tu correo.',
      client_custom_notes: [
        { title: 'Seguimiento', content: 'Llamar el viernes.' },
      ],
    };
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithNote) };
      }
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        const body = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...documentWithNote, ...body }),
        };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    await page.getByTestId('doc-client-note-open').click();
    await expect(page.getByTestId('client-note-subject')).toHaveValue('Contrato listo');
    await page.getByTestId('client-note-email').fill('Hola Ana,\n\nAdjunto el contrato final.');
    await page.getByTestId('client-note-custom-content-0').fill('Llamar el lunes.');
    const requestPromise = page.waitForRequest(
      (request) => request.url().includes('/api/documents/1/update/')
        && request.method() === 'PATCH',
    );
    await expect(page.getByTestId('client-note-submit')).toHaveText('Guardar cambios');
    await page.getByTestId('client-note-submit').click();
    const request = await requestPromise;
    const patchBody = request.postDataJSON();

    expect(patchBody).toEqual({
      client_email_subject: 'Contrato listo',
      client_email_body: 'Hola Ana,\n\nAdjunto el contrato final.',
      client_whatsapp_message: 'Hola Ana, revisa el contrato en tu correo.',
      client_custom_notes: [{ title: 'Seguimiento', content: 'Llamar el lunes.' }],
    });
    await expect(page.getByText('Notas guardadas', { exact: true })).toBeVisible();
    await expect(page.getByTestId('document-client-note-modal')).toHaveCount(0);
    await expect(page.getByTestId('doc-save')).toBeDisabled();
  });

  test('keeps unrelated document edits pending after saving notes', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocument) };
      }
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        const body = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockDocument, ...body }),
        };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');
    await page.getByLabel(/T[ií]tulo/i).fill('Título todavía pendiente');
    await page.getByTestId('doc-client-note-open').click();
    await page.getByTestId('client-note-subject').fill('Notas ya persistidas');

    const responsePromise = page.waitForResponse(
      (response) => response.url().includes('/api/documents/1/update/'),
    );
    await page.getByTestId('client-note-submit').click();
    await responsePromise;

    await expect(page.getByLabel(/T[ií]tulo/i)).toHaveValue('Título todavía pendiente');
    await expect(page.getByTestId('doc-unsaved-notice')).toContainText('Título sin guardar');
    await expect(page.getByTestId('doc-save')).toBeEnabled();
  });

  test('deletes a custom note from the saved document', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const documentWithCustomNote = {
      ...mockDocument,
      content_markdown: '# Contrato',
      client_custom_notes: [
        { title: 'Temporal', content: 'Eliminar después de revisar.' },
      ],
    };
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithCustomNote) };
      }
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        const body = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...documentWithCustomNote, ...body }),
        };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');
    await page.getByTestId('doc-client-note-open').click();
    await page.getByTestId('client-note-custom-delete-0').click();
    const requestPromise = page.waitForRequest(
      (request) => request.url().includes('/api/documents/1/update/')
        && request.method() === 'PATCH',
    );
    await page.getByTestId('client-note-submit').click();
    const request = await requestPromise;

    expect(request.postDataJSON().client_custom_notes).toEqual([]);
  });

  test('rejected notes keep the modal draft', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    const documentWithMarkdown = {
      ...mockDocument,
      content_markdown: '# Contrato\n\nContenido.',
    };
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      }
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ client_email_subject: ['Revisa el asunto.'] }),
        };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');
    await page.getByTestId('doc-client-note-open').click();
    await page.getByTestId('client-note-subject').fill('Asunto rechazado');
    const responsePromise = page.waitForResponse(
      (response) => response.url().includes('/api/documents/1/update/'),
    );
    await page.getByTestId('client-note-submit').click();
    await responsePromise;

    await expect(page.getByText('client_email_subject: Revisa el asunto.')).toBeVisible();
    await expect(page.getByTestId('client-note-subject')).toHaveValue('Asunto rechazado');
    await expect(page.getByTestId('document-client-note-modal')).toBeVisible();
  });

  test('a server failure preserves the edited notes', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const documentWithMarkdown = {
      ...mockDocument,
      content_markdown: '# Contrato\n\nContenido.',
    };
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      }
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        return {
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Servicio temporalmente no disponible.' }),
        };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');
    await page.getByTestId('doc-client-note-open').click();
    await page.getByTestId('client-note-whatsapp').fill('Mensaje que debe sobrevivir.');
    const responsePromise = page.waitForResponse(
      (response) => response.url().includes('/api/documents/1/update/'),
    );
    await page.getByTestId('client-note-submit').click();
    await responsePromise;

    await expect(page.getByTestId('client-note-whatsapp'))
      .toHaveValue('Mensaje que debe sobrevivir.');
  });

  test('copies the markdown content to the clipboard', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const documentWithMarkdown = { ...mockDocument, content_markdown: '# Contrato\n\nEste es el contenido del contrato.' };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    await page.getByRole('button', { name: /^Copiar$/i }).click();

    await expect(page.getByRole('button', { name: /^Copiado$/i })).toBeVisible({ timeout: 5000 });
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toBe(documentWithMarkdown.content_markdown);
  });

  test('selecting professional style applies its preview heading color', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    const documentWithMarkdown = {
      ...mockDocument,
      content_markdown: '# Contrato\n\nEste es el contenido del contrato.',
      template_style: 'friendly',
    };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const previewHeading = page.getByRole('heading', { name: 'Contrato', level: 1, exact: true });
    await expect(previewHeading).toBeVisible();
    await page.getByTestId('doc-style-professional').click();
    await expect(previewHeading).toHaveCSS('color', 'rgb(0, 41, 33)');
  });

  test('pastes clipboard content into the markdown textarea', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const documentWithMarkdown = { ...mockDocument, content_markdown: '# Contrato\n\nEste es el contenido del contrato.' };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const textarea = page.locator('#edit-markdown');
    await textarea.click();
    await page.keyboard.press('Control+End');
    await page.evaluate((text) => navigator.clipboard.writeText(text), '\n\nTexto pegado desde el portapapeles.');

    await page.getByRole('button', { name: /^Pegar$/i }).click();

    await expect(page.getByRole('button', { name: /^Pegado$/i })).toBeVisible({ timeout: 5000 });
    await expect(textarea).toHaveValue(`${documentWithMarkdown.content_markdown}\n\nTexto pegado desde el portapapeles.`);
  });

  test('the saved association links back to its client and project', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the editor is reached by URL across this whole
    // spec; the subject is the association block it renders after loading)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockDocument,
            client: 7, client_display_name: 'Kore SAS',
            project: 11, project_name: 'Kore - Diseño',
          }),
        };
      }
      // El proyecto 11 tiene que estar en la lista de SU cliente: el backend
      // valida esa pertenencia al escribir, así que un par ya persistido
      // siempre aparece acá. Con la lista vacía el picker lo daba por ajeno y
      // lo soltaba, y el documento quedaba con un cambio pendiente que nadie
      // pidió — algo que ahora el aviso de cambios sin guardar hace visible.
      if (apiPath === 'accounting/projects/') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [{
              id: 11, name: 'Kore - Diseño', status: 'active', status_label: 'Activo',
              client_profile_id: 7, client_display_name: 'Kore SAS',
            }],
          }),
        };
      }
      if (apiPath === 'document-folders/' || apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: '[]' };
      if (apiPath.startsWith('accounts/saved-filter-tabs')) return { status: 200, contentType: 'application/json', body: '[]' };
      if (apiPath === 'proposals/client-profiles/status-counts/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ all: 0, active: 0, orphans: 0, inactive: 0 }) };
      }
      if (apiPath === 'proposals/client-profiles/') return { status: 200, contentType: 'application/json', body: '[]' };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    // La relación sirve en las dos direcciones: del documento a su cliente
    // (ficha expandida vía ?highlight=) y a su proyecto.
    await expect(page.getByTestId('doc-client-autocomplete')).toHaveValue('Kore SAS');
    await expect(page.getByTestId('document-project-link'))
      .toHaveAttribute('href', /\/panel\/projects\?highlight=11/);

    // Seguir el enlace prueba la vuelta: aterriza en /panel/clients con el
    // ?highlight= que expande la ficha de ese cliente.
    await page.getByTestId('document-client-link').click();
    await expect(page).toHaveURL(/\/panel\/clients/, { timeout: 30_000 });
  });
});

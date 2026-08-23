/**
 * E2E tests for the unsaved-changes guard rolled out across the panel editors,
 * using /panel/emails as the representative case.
 *
 * @flow:admin-panel-unsaved-guard
 * Covers: the shared guard on a page whose state lives in loose refs rather
 *         than a form object; that switching tabs — a same-route query
 *         navigation — does NOT trip the leave guard; and that leaving the
 *         page with pending changes offers to save, discard or stay.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PANEL_UNSAVED_GUARD } from '../helpers/flow-tags.js';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const authCheck = json({ user: { username: 'admin', is_staff: true } });

const defaultsPayload = {
  defaults: { greeting: 'Hola', footer: 'Un abrazo', signer: 'gustavo' },
  config: { greeting: 'Hola', footer: 'Un abrazo', signer: 'gustavo' },
  signers: [{ value: 'gustavo', label: 'Gustavo' }],
  variables: [],
};

function baseHandler(extra = () => null) {
  return async (ctx) => {
    const { apiPath } = ctx;
    const fromExtra = await extra(ctx);
    if (fromExtra) return fromExtra;
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'emails/defaults/') return json(defaultsPayload);
    if (apiPath.startsWith('emails/history')) return json({ results: [], has_next: false });
    return null;
  };
}

const notice = (page) => page.getByTestId('emails-defaults-unsaved-notice');
const greetingField = (page) => page.getByPlaceholder('Hola {client_name}');

test.describe('Admin Panel — Unsaved Changes Guard', () => {
  test.setTimeout(90_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('editing a default value raises a warning that names that field', {
    tag: [...ADMIN_PANEL_UNSAVED_GUARD, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (la pestaña de valores por defecto se alcanza por query)
    await mockApi(page, baseHandler());
    await page.goto('/panel/emails?tab=defaults');
    await expect(greetingField(page)).toHaveValue('Hola');

    await greetingField(page).fill('Buenas');

    await expect(notice(page)).toContainText('Saludo sin guardar');
  });

  // Cambiar de pestaña hace router.replace({ query }) sobre la MISMA ruta. Vue
  // Router reutiliza el componente y no dispara el guard de salida — pero eso
  // se prueba, no se asume: si lo disparara, navegar entre pestañas quedaría
  // bloqueado por un modal en cuanto el formulario tuviera algo pendiente.
  test('switching tabs with pending changes does not interrupt', {
    tag: [...ADMIN_PANEL_UNSAVED_GUARD, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    // quality: allow-deep-link (la pestaña de valores por defecto se alcanza por query)
    await mockApi(page, baseHandler());
    await page.goto('/panel/emails?tab=defaults');
    await greetingField(page).fill('Buenas');
    await expect(notice(page)).toBeVisible();

    await page.getByRole('tab', { name: 'Redactar' }).click();

    // La página borra el `?tab=` del modo por defecto a propósito, así que lo
    // que se afirma es que ya no está en la pestaña de valores y que nadie
    // interpuso un modal.
    await expect(page).not.toHaveURL(/tab=defaults/);
    await expect(page.getByTestId('confirm-modal-confirm')).toBeHidden();

    // Y lo pendiente sigue ahí al volver: cambiar de pestaña no descarta nada.
    await page.getByRole('tab', { name: 'Configuración' }).click();
    await expect(greetingField(page)).toHaveValue('Buenas');
  });

  test('leaving the page offers to save the pending defaults', {
    tag: [...ADMIN_PANEL_UNSAVED_GUARD, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let saved = false;
    // quality: allow-deep-link (la pestaña de valores por defecto se alcanza por query)
    await mockApi(page, baseHandler(async ({ apiPath, method }) => {
      if (apiPath === 'emails/defaults/' && method === 'PUT') {
        saved = true;
        return json({ ...defaultsPayload, config: { ...defaultsPayload.config, greeting: 'Buenas' } });
      }
      return null;
    }));
    await page.goto('/panel/emails?tab=defaults');
    await greetingField(page).fill('Buenas');
    await expect(notice(page)).toBeVisible();

    await page.getByRole('link', { name: /ProjectApp/i }).first().click();
    await expect(page.getByTestId('confirm-modal-confirm')).toContainText('Guardar y salir');
    await page.getByTestId('confirm-modal-confirm').click();

    // Anclado a la raíz del panel: una alternancia más laxa daría por buena la
    // propia URL de partida y el test pasaría aunque no se hubiera navegado.
    await expect(page).toHaveURL(/\/panel\/?$/, { timeout: 60_000 });
    expect(saved).toBe(true);
  });
});

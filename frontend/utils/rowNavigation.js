/**
 * How a pointer gesture on a navigable listing row resolves.
 *
 * The panel used to put the whole row behind a JS handler, and each listing
 * reimplemented a fraction of what an <a href> does for free — proposals and
 * diagnostics branched on ctrlKey to call window.open, documents did not branch
 * at all, so ctrl+click opened in the same tab. The rule is inverted now: the
 * <a> in the title cell is the real navigation, and the row handler is only a
 * convenience for the plain click.
 *
 * This module answers the one question that handler has to get right — is this
 * gesture the row's at all, and if so does it mean same tab or new tab?
 *
 * SELECTION: ctrl/cmd is claimed for "new tab" because no listing uses it to
 * extend a selection — multi-select is checkbox-only (see useRowSelection) and
 * shiftKey appears nowhere in listing code.
 *
 * SHIFT and ALT are deliberately NOT claimed. On a real anchor the browser
 * opens a new window with shift, which window.open cannot reproduce faithfully;
 * shift+click also extends a text selection, and these tables show phone
 * numbers, amounts and emails people copy by hand. Hijacking those gestures
 * into a same-tab navigation would be the very bug this module exists to fix,
 * so the row stays out of the way and lets the browser have them.
 *
 * It also replaces the `@click.stop` scattered cell by cell: instead of every
 * <td> holding a control having to remember to stop the bubble, the row asks
 * where the click was born. A new column with a new control is safe by default.
 */

/**
 * Anything that owns its own click. A gesture starting inside one of these
 * belongs to that control, not to the row: the selection checkbox, the actions
 * kebab, an inline <select> — and the title link itself, whose native behaviour
 * is precisely what we must not double up on.
 */
export const ROW_INTERACTIVE_SELECTOR = 'a, button, input, label, select, textarea, summary,'
  + ' [role="button"], [role="link"], [role="menuitem"], [contenteditable="true"]';

/**
 * ¿Es este el clic que el navegador convertiría en «seguir el enlace acá
 * mismo»? Sirve para el ancla que NO puede navegar sola: la fila de carpeta
 * publica `?folder=` para que el navegador tenga a dónde apuntar, pero entrar a
 * una carpeta pasa por el store (y en modo búsqueda hace algo distinto). El
 * enlace se deja los gestos del navegador y le cede el clic simple a la página.
 *
 * A diferencia de `rowActivationIntent` no mira de dónde nació el clic: acá el
 * oyente ES el enlace.
 *
 * @param {MouseEvent} [event]
 * @returns {boolean}
 */
export function isPlainActivation(event) {
  if (!event) return true;
  const button = typeof event.button === 'number' ? event.button : 0;
  if (button !== 0) return false;
  return !(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey);
}

/** @typedef {'ignore'|'same-tab'|'new-tab'} RowActivationIntent */

/**
 * @param {MouseEvent} [event] Absent for a programmatic call (an action-menu
 *   item, a post-save redirect) — that is plain navigation.
 * @param {{ hasTextSelection?: () => boolean }} [deps]
 * @returns {RowActivationIntent}
 */
export function rowActivationIntent(event, { hasTextSelection } = {}) {
  if (!event) return 'same-tab';

  // Right button and beyond: the native context menu must reach the user
  // untouched — over the title cell that menu is what actually carries
  // "abrir en pestaña nueva" and "copiar dirección del enlace".
  const button = typeof event.button === 'number' ? event.button : 0;
  if (button !== 0 && button !== 1) return 'ignore';

  const target = event.target;
  if (target && typeof target.closest === 'function' && target.closest(ROW_INTERACTIVE_SELECTOR)) {
    return 'ignore';
  }

  if (button === 1 || event.ctrlKey || event.metaKey) return 'new-tab';

  // Reserved for the browser, never repurposed — see the SHIFT/ALT note above.
  if (event.shiftKey || event.altKey) return 'ignore';

  // Releasing a drag-select over the row must not throw the text away.
  if (typeof hasTextSelection === 'function' && hasTextSelection()) return 'ignore';

  return 'same-tab';
}

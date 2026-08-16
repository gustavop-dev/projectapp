/**
 * Tests for utils/rowNavigation.js.
 *
 * `rowActivationIntent` es la regla que decide si un gesto sobre una fila de
 * listado es «abrir el detalle», y de ella depende que ctrl+clic deje de abrir
 * en la misma pestaña: la fila se aparta y el `<a>` del título hace lo suyo.
 */

import { ROW_INTERACTIVE_SELECTOR, rowActivationIntent } from '../../utils/rowNavigation';

/**
 * Dispara un clic real sobre `element` y devuelve el evento tal como lo recibe
 * un manejador de fila — con su `target` de verdad, que es lo que la guarda
 * interroga con `closest`.
 */
function clickOn(element, init = {}) {
  let captured = null;
  const handler = (event) => { captured = event; };
  element.addEventListener('click', handler);
  element.dispatchEvent(new MouseEvent('click', { bubbles: true, ...init }));
  element.removeEventListener('click', handler);
  return captured;
}

function buildRow() {
  document.body.innerHTML = `
    <table><tbody>
      <tr id="row">
        <td><input id="checkbox" type="checkbox" /></td>
        <td><a id="title" href="/panel/documents/1/edit">Contrato</a></td>
        <td id="inert">Cliente Acme</td>
        <td><button id="kebab" type="button">Acciones</button></td>
      </tr>
    </tbody></table>
  `;
  return {
    inert: document.getElementById('inert'),
    title: document.getElementById('title'),
    kebab: document.getElementById('kebab'),
    checkbox: document.getElementById('checkbox'),
  };
}

describe('ROW_INTERACTIVE_SELECTOR', () => {
  it('names every control that owns its own click', () => {
    for (const tag of ['a', 'button', 'input', 'label', 'select', 'textarea', 'summary']) {
      expect(ROW_INTERACTIVE_SELECTOR).toContain(tag);
    }
    expect(ROW_INTERACTIVE_SELECTOR).toContain('[role="button"]');
  });
});

describe('rowActivationIntent', () => {
  it('opens in the same tab on a plain click over inert content', () => {
    const { inert } = buildRow();
    expect(rowActivationIntent(clickOn(inert))).toBe('same-tab');
  });

  it('opens in the same tab when called without an event', () => {
    expect(rowActivationIntent()).toBe('same-tab');
  });

  it('opens a new tab with ctrl', () => {
    const { inert } = buildRow();
    expect(rowActivationIntent(clickOn(inert, { ctrlKey: true }))).toBe('new-tab');
  });

  it('opens a new tab with cmd', () => {
    const { inert } = buildRow();
    expect(rowActivationIntent(clickOn(inert, { metaKey: true }))).toBe('new-tab');
  });

  it('opens a new tab with the wheel button', () => {
    const { inert } = buildRow();
    expect(rowActivationIntent(clickOn(inert, { button: 1 }))).toBe('new-tab');
  });

  it('stays out of the way of the context menu', () => {
    const { inert } = buildRow();
    expect(rowActivationIntent(clickOn(inert, { button: 2 }))).toBe('ignore');
  });

  it('leaves shift and alt to the browser instead of hijacking them', () => {
    const { inert } = buildRow();
    expect(rowActivationIntent(clickOn(inert, { shiftKey: true }))).toBe('ignore');
    expect(rowActivationIntent(clickOn(inert, { altKey: true }))).toBe('ignore');
  });

  it('lets the title link do its own navigating', () => {
    const { title } = buildRow();
    expect(rowActivationIntent(clickOn(title))).toBe('ignore');
  });

  it('lets the actions kebab act without navigating', () => {
    const { kebab } = buildRow();
    expect(rowActivationIntent(clickOn(kebab))).toBe('ignore');
  });

  it('lets the selection checkbox toggle without navigating', () => {
    const { checkbox } = buildRow();
    expect(rowActivationIntent(clickOn(checkbox))).toBe('ignore');
  });

  it('does not navigate when the click releases a text selection', () => {
    const { inert } = buildRow();
    const intent = rowActivationIntent(clickOn(inert), { hasTextSelection: () => true });
    expect(intent).toBe('ignore');
  });

  it('still opens a new tab with ctrl even if text is selected', () => {
    const { inert } = buildRow();
    const intent = rowActivationIntent(
      clickOn(inert, { ctrlKey: true }),
      { hasTextSelection: () => true },
    );
    expect(intent).toBe('new-tab');
  });
});

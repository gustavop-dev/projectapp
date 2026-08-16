/**
 * Tests for the useRowNavigation composable.
 *
 * Es la mitad de comodidad del enlace de fila: el `<a>` del título sigue siendo
 * la navegación de verdad, y esto hace que el RESTO de la fila reaccione a la
 * misma dirección con las mismas reglas — sin volver a inventar `window.open`
 * en cada pantalla.
 */

const TO = '/es-co/panel/documents/1/edit';

let mockRouterPush;
let openSpy;
let useRowNavigation;

beforeEach(() => {
  mockRouterPush = jest.fn();
  global.useRouter = () => ({ push: mockRouterPush });
  openSpy = jest.spyOn(window, 'open').mockImplementation(() => null);

  jest.resetModules();
  ({ useRowNavigation } = require('../../composables/useRowNavigation'));
});

afterEach(() => {
  openSpy.mockRestore();
  document.body.innerHTML = '';
});

function clickOn(element, init = {}) {
  let captured = null;
  const handler = (event) => { captured = event; };
  element.addEventListener('click', handler);
  element.dispatchEvent(new MouseEvent('click', { bubbles: true, ...init }));
  element.removeEventListener('click', handler);
  return captured;
}

function inertCell() {
  document.body.innerHTML = '<table><tbody><tr><td id="cell">Acme</td></tr></tbody></table>';
  return document.getElementById('cell');
}

describe('useRowNavigation', () => {
  it('navigates in the same tab on a plain click', () => {
    const { openRow } = useRowNavigation();

    openRow(TO, clickOn(inertCell()));

    expect(mockRouterPush).toHaveBeenCalledWith(TO);
    expect(openSpy).not.toHaveBeenCalled();
  });

  it('navigates in the same tab when called without an event', () => {
    const { openRow } = useRowNavigation();

    openRow(TO);

    expect(mockRouterPush).toHaveBeenCalledWith(TO);
  });

  it('opens a new tab on ctrl+click', () => {
    const { openRow } = useRowNavigation();

    openRow(TO, clickOn(inertCell(), { ctrlKey: true }));

    expect(openSpy).toHaveBeenCalledWith(TO, '_blank');
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it('opens a new tab on a wheel click', () => {
    const { openRow } = useRowNavigation();

    openRow(TO, clickOn(inertCell(), { button: 1 }));

    expect(openSpy).toHaveBeenCalledWith(TO, '_blank');
  });

  it('lets the controls inside a row act without navigating', () => {
    document.body.innerHTML = '<table><tbody><tr>'
      + '<td id="cell">Acme</td>'
      + '<td><button id="kebab" type="button">Acciones</button></td>'
      + '</tr></tbody></table>';
    const { openRow } = useRowNavigation();

    openRow(TO, clickOn(document.getElementById('cell')));
    openRow(TO, clickOn(document.getElementById('kebab')));

    // El cuerpo de la fila navegó una vez; el kebab no volvió a navegar.
    expect(mockRouterPush).toHaveBeenCalledTimes(1);
    expect(mockRouterPush).toHaveBeenCalledWith(TO);
  });

  it('does nothing when the row has no address', () => {
    const { openRow } = useRowNavigation();
    const cell = inertCell();

    openRow(null, clickOn(cell));
    openRow(TO, clickOn(cell));

    expect(mockRouterPush).toHaveBeenCalledTimes(1);
    expect(mockRouterPush).toHaveBeenCalledWith(TO);
  });

  it('does not navigate when the click releases a live text selection', () => {
    const getSelection = jest.spyOn(window, 'getSelection');
    const { openRow } = useRowNavigation();
    const cell = inertCell();

    getSelection.mockReturnValue({ isCollapsed: false, toString: () => 'Acme' });
    openRow(TO, clickOn(cell));
    getSelection.mockReturnValue({ isCollapsed: true, toString: () => '' });
    openRow(TO, clickOn(cell));

    // Sólo el clic sin selección viva navegó.
    expect(mockRouterPush).toHaveBeenCalledTimes(1);
    expect(mockRouterPush).toHaveBeenCalledWith(TO);
    getSelection.mockRestore();
  });
});

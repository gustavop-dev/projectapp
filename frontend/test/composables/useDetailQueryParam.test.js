/**
 * Tests for the useDetailQueryParam composable.
 *
 * Le da dirección a un detalle que vive en un modal. La URL vista+capa es la
 * que dice la verdad — el detalle ES una capa sobre el listado —, y de paso el
 * contexto del listado (pestaña, filtros) sobrevive porque el parámetro viaja
 * al lado de los que ya estaban.
 *
 * Ojo con el precedente que corrige: `?focus=` no sobrevive a una recarga
 * porque es un ephemeralParam y se borra en el setup.
 */

import { ref } from 'vue';

let route;
let push;
let replace;
let useDetailQueryParam;

beforeEach(() => {
  route = { path: '/es-co/panel/accounting/incomes', query: {} };
  push = jest.fn();
  replace = jest.fn();
  global.useRoute = () => route;
  global.useRouter = () => ({ push, replace });

  jest.resetModules();
  ({ useDetailQueryParam } = require('../../composables/useDetailQueryParam'));
});

describe('useDetailQueryParam', () => {
  it('reads the open detail straight off the URL', () => {
    route.query = { income: '123' };

    const detail = useDetailQueryParam('income');

    expect(detail.openId.value).toBe(123);
    expect(detail.isOpen.value).toBe(true);
  });

  it('stays closed when the param is absent or nonsense', () => {
    const detail = useDetailQueryParam('income');
    expect(detail.isOpen.value).toBe(false);

    route.query = { income: 'banana' };
    expect(detail.openId.value).toBe(null);

    route.query = { income: '-4' };
    expect(detail.openId.value).toBe(null);
  });

  it('addresses the detail alongside the filters already in the URL', () => {
    route.query = { tab: 'expected', client: '7' };

    const { toFor } = useDetailQueryParam('income');

    expect(toFor(123)).toEqual({
      path: '/es-co/panel/accounting/incomes',
      query: { tab: 'expected', client: '7', income: '123' },
    });
  });

  it('opens by pushing, so back closes the detail again', () => {
    const { open } = useDetailQueryParam('income');

    open(123);

    expect(push).toHaveBeenCalledWith({
      path: '/es-co/panel/accounting/incomes',
      query: { income: '123' },
    });
  });

  it('closes by replacing, leaving the rest of the URL untouched', () => {
    route.query = { tab: 'expected', income: '123' };
    const { close } = useDetailQueryParam('income');

    close();

    expect(replace).toHaveBeenCalledWith({
      path: '/es-co/panel/accounting/incomes',
      query: { tab: 'expected' },
    });
  });

  it('resolves the row for the modals that need the object, not just the id', () => {
    route.query = { account: '2' };
    const rows = ref([{ id: 1, name: 'Uno' }, { id: 2, name: 'Dos' }]);

    const { openRow } = useDetailQueryParam('account', { rows });

    expect(openRow.value).toEqual({ id: 2, name: 'Dos' });
  });

  it('re-reads the list through a getter, so a reloaded store is not stale', () => {
    route.query = { hosting: '2' };
    // `reactive` de la MISMA instancia de vue que cargó el composable: tras
    // jest.resetModules() el import de arriba apunta a otra copia, y dos
    // sistemas de reactividad distintos no se ven entre sí.
    const { reactive } = require('vue');
    const store = reactive({ hostings: [{ id: 1, name: 'Uno' }] });

    const { openRow } = useDetailQueryParam('hosting', { rows: () => store.hostings });
    expect(openRow.value).toBe(null);

    // Recargar la lista REEMPLAZA el array del store; el getter la vuelve a
    // leer y el computed se entera porque la lectura pasa por el store.
    store.hostings = [{ id: 2, name: 'Dos' }];
    expect(openRow.value).toEqual({ id: 2, name: 'Dos' });
  });

  it('reports a missing row so the page can decide what to do about it', () => {
    // Recargar con un id filtrado o borrado: la página limpia el parámetro en
    // vez de dejar una capa abierta sobre la nada.
    route.query = { account: '999' };
    const rows = ref([{ id: 1, name: 'Uno' }]);

    const { openId, openRow } = useDetailQueryParam('account', { rows });

    expect(openId.value).toBe(999);
    expect(openRow.value).toBe(null);
  });
});

describe('useDetailQueryParam con resolve', () => {
  it('lets a store that already knows how to find a row do the finding', () => {
    // El store de tareas reparte sus filas entre varios tableros y expone
    // getTaskById: duplicar esa búsqueda acá sería copiarla.
    route.query = { task: '42' };
    const getTaskById = jest.fn((id) => (id === 42 ? { id: 42, title: 'Migrar' } : null));

    const { openRow } = useDetailQueryParam('task', { resolve: getTaskById });

    expect(openRow.value).toEqual({ id: 42, title: 'Migrar' });
    expect(getTaskById).toHaveBeenCalledWith(42);
  });
});

/**
 * Tests para `useSavedFilterTabs` — persistencia en backend de pestañas
 * de filtros guardados (antes vivían en localStorage).
 *
 * Cubre: load inicial, saveTab (incluyendo límite y error), updateTabFilters
 * con debounce, renameTab (optimista + revert), deleteTab (optimista + revert).
 */

jest.mock('~/stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

import { nextTick } from 'vue';

import {
  create_request,
  delete_request,
  get_request,
  patch_request,
} from '~/stores/services/request_http';
import {
  normalizedFilters,
  sameFilters,
  useSavedFilterTabs,
} from '~/composables/useSavedFilterTabs';

function flush() {
  return new Promise((resolve) => Promise.resolve().then(resolve));
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.useRealTimers();
});

describe('loadTabs', () => {
  it('GETs scoped por viewName y popula savedTabs', async () => {
    get_request.mockResolvedValueOnce({
      data: [
        { id: 1, view: 'proposal', name: 'A', filters: {}, order: 0 },
        { id: 2, view: 'proposal', name: 'B', filters: { x: 1 }, order: 1 },
      ],
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    expect(get_request).toHaveBeenCalledWith('accounts/saved-filter-tabs/?view=proposal');
    expect(tabs.savedTabs.value).toHaveLength(2);
    expect(tabs.isReady.value).toBe(true);
    expect(tabs.lastError.value).toBeNull();
  });

  it('si el GET falla, deja savedTabs vacío y registra lastError', async () => {
    const err = new Error('network down');
    get_request.mockRejectedValueOnce(err);

    const tabs = useSavedFilterTabs('client');
    await tabs.loadTabs();

    expect(tabs.savedTabs.value).toEqual([]);
    expect(tabs.lastError.value).toBe(err);
    expect(tabs.isReady.value).toBe(true);
  });
});

describe('saveTab', () => {
  it('POSTea con el payload correcto y agrega la pestaña creada', async () => {
    create_request.mockResolvedValueOnce({
      data: { id: 7, view: 'proposal', name: 'Activos', filters: { s: ['a'] }, order: 0 },
    });

    const tabs = useSavedFilterTabs('proposal');
    const created = await tabs.saveTab('Activos', { s: ['a'] });

    expect(create_request).toHaveBeenCalledWith('accounts/saved-filter-tabs/', {
      view: 'proposal',
      name: 'Activos',
      filters: { s: ['a'] },
    });
    expect(created.id).toBe(7);
    expect(tabs.savedTabs.value).toHaveLength(1);
    expect(tabs.savedTabs.value[0].id).toBe(7);
  });

  it('si el backend rechaza por límite, retorna null y registra lastError', async () => {
    const err = new Error('limit');
    create_request.mockRejectedValueOnce(err);

    const tabs = useSavedFilterTabs('proposal');
    const result = await tabs.saveTab('Overflow', {});

    expect(result).toBeNull();
    expect(tabs.savedTabs.value).toHaveLength(0);
    expect(tabs.lastError.value).toBe(err);
  });

  it('no llama al backend si el límite local ya está alcanzado', async () => {
    get_request.mockResolvedValueOnce({
      data: Array.from({ length: 12 }, (_, i) => ({
        id: i + 1, view: 'proposal', name: `t${i}`, filters: {}, order: i,
      })),
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();
    expect(tabs.isTabLimitReached.value).toBe(true);

    const result = await tabs.saveTab('thirteenth', {});

    expect(result).toBeNull();
    expect(create_request).not.toHaveBeenCalled();
  });
});

describe('updateTabFilters', () => {
  it('aplica el patch optimistamente y dispara PATCH con debounce', async () => {
    jest.useFakeTimers();
    get_request.mockResolvedValueOnce({
      data: [{ id: 5, view: 'proposal', name: 'A', filters: { x: 1 }, order: 0 }],
    });
    patch_request.mockResolvedValueOnce({
      data: { id: 5, view: 'proposal', name: 'A', filters: { x: 2 }, order: 0 },
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    tabs.updateTabFilters(5, { x: 2 });

    // Optimistic: ya está aplicado en savedTabs antes del debounce.
    expect(tabs.savedTabs.value[0].filters).toEqual({ x: 2 });
    expect(patch_request).not.toHaveBeenCalled();

    jest.advanceTimersByTime(500);
    await flush();

    expect(patch_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/5/',
      { filters: { x: 2 } },
    );
  });

  it('coalesce múltiples updates rápidos en un único PATCH', async () => {
    jest.useFakeTimers();
    get_request.mockResolvedValueOnce({
      data: [{ id: 5, view: 'proposal', name: 'A', filters: { x: 1 }, order: 0 }],
    });
    patch_request.mockResolvedValueOnce({
      data: { id: 5, view: 'proposal', name: 'A', filters: { x: 3 }, order: 0 },
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    tabs.updateTabFilters(5, { x: 2 });
    jest.advanceTimersByTime(100);
    tabs.updateTabFilters(5, { x: 3 });
    jest.advanceTimersByTime(500);
    await flush();

    expect(patch_request).toHaveBeenCalledTimes(1);
    expect(patch_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/5/',
      { filters: { x: 3 } },
    );
  });

  it('descarta el update cuando los filtros no cambiaron', async () => {
    jest.useFakeTimers();
    get_request.mockResolvedValueOnce({
      data: [{ id: 5, view: 'proposal', name: 'A', filters: { x: 1 }, order: 0 }],
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    tabs.updateTabFilters(5, { x: 1 });
    jest.advanceTimersByTime(1000);
    await flush();

    expect(patch_request).not.toHaveBeenCalled();
  });
});

describe('renameTab', () => {
  it('rename optimista; revierte si el backend falla', async () => {
    get_request.mockResolvedValueOnce({
      data: [{ id: 9, view: 'proposal', name: 'Viejo', filters: {}, order: 0 }],
    });
    patch_request.mockRejectedValueOnce(new Error('boom'));

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    const pending = tabs.renameTab(9, 'Nuevo');
    expect(tabs.savedTabs.value[0].name).toBe('Nuevo');

    await pending;
    expect(tabs.savedTabs.value[0].name).toBe('Viejo');
    expect(tabs.lastError.value).not.toBeNull();
  });
});

describe('deleteTab', () => {
  it('elimina optimistamente y restaura si DELETE falla', async () => {
    get_request.mockResolvedValueOnce({
      data: [
        { id: 1, view: 'proposal', name: 'A', filters: {}, order: 0 },
        { id: 2, view: 'proposal', name: 'B', filters: {}, order: 1 },
      ],
    });
    delete_request.mockRejectedValueOnce(new Error('forbidden'));

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    const pending = tabs.deleteTab(1);
    expect(tabs.savedTabs.value.map((t) => t.id)).toEqual([2]);

    await pending;
    expect(tabs.savedTabs.value.map((t) => t.id)).toEqual([1, 2]);
    expect(tabs.lastError.value).not.toBeNull();
  });
});

describe('sameFilters / normalizedFilters', () => {
  it('ignora claves inactivas y el orden: el shape expandido equivale a la base sparse', () => {
    const expanded = {
      search: '', kind: 'expected', paymentStatus: 'pending',
      partner: '', ledger: '', periodAfter: '', amountMin: '',
    };
    const sparse = { paymentStatus: 'pending', kind: 'expected' };

    expect(sameFilters(expanded, sparse)).toBe(true);
    expect(normalizedFilters(expanded)).toEqual({
      kind: 'expected', paymentStatus: 'pending',
    });
  });

  it('detecta drift real: valor cambiado, clave activa de más o base perdida', () => {
    const base = { kind: 'expected', paymentStatus: 'pending' };

    expect(sameFilters({ kind: 'expected', paymentStatus: '' }, base)).toBe(false);
    expect(sameFilters(
      { kind: 'expected', paymentStatus: 'pending', partner: 'gustavo' }, base,
    )).toBe(false);
    expect(sameFilters({ kind: 'expected', paymentStatus: 'paid' }, base)).toBe(false);
  });

  it('compara arrays por contenido y trata [] como inactivo', () => {
    expect(sameFilters({ statuses: ['draft'] }, { statuses: ['draft'] })).toBe(true);
    expect(sameFilters({ statuses: [] }, {})).toBe(true);
    expect(sameFilters({ statuses: ['draft'] }, { statuses: ['sent'] })).toBe(false);
  });
});

describe('restoreTab', () => {
  it('PATCHea filters=base_filters y reemplaza la pestaña local', async () => {
    get_request.mockResolvedValueOnce({
      data: [{
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['sent'] },
        base_filters: { statuses: ['draft'] },
      }],
    });
    patch_request.mockResolvedValueOnce({
      data: {
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['draft'] },
        base_filters: { statuses: ['draft'] },
      },
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();
    const updated = await tabs.restoreTab(5);

    expect(patch_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/5/',
      { filters: { statuses: ['draft'] } },
    );
    expect(updated.filters).toEqual({ statuses: ['draft'] });
    expect(tabs.savedTabs.value[0].filters).toEqual({ statuses: ['draft'] });
  });

  it('cancela un auto-guardado con debounce pendiente para no pisar la restauración', async () => {
    jest.useFakeTimers();
    get_request.mockResolvedValueOnce({
      data: [{
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['draft'] },
        base_filters: { statuses: ['draft'] },
      }],
    });
    patch_request.mockResolvedValueOnce({
      data: {
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['draft'] },
        base_filters: { statuses: ['draft'] },
      },
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    tabs.updateTabFilters(5, { statuses: ['sent'] });
    await tabs.restoreTab(5);
    jest.advanceTimersByTime(1000);
    await flush();

    expect(patch_request).toHaveBeenCalledTimes(1);
    expect(patch_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/5/',
      { filters: { statuses: ['draft'] } },
    );
  });

  it('si el PATCH falla, retorna null y registra lastError', async () => {
    const err = new Error('offline');
    get_request.mockResolvedValueOnce({
      data: [{
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['sent'] },
        base_filters: { statuses: ['draft'] },
      }],
    });
    patch_request.mockRejectedValueOnce(err);

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();
    const result = await tabs.restoreTab(5);

    expect(result).toBeNull();
    expect(tabs.lastError.value).toBe(err);
  });
});

describe('rebaseTab', () => {
  it('PATCHea base_filters=filters actuales (fijar como base)', async () => {
    get_request.mockResolvedValueOnce({
      data: [{
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['sent'] },
        base_filters: { statuses: ['draft'] },
      }],
    });
    patch_request.mockResolvedValueOnce({
      data: {
        id: 5, view: 'proposal', name: 'T', order: 0,
        filters: { statuses: ['sent'] },
        base_filters: { statuses: ['sent'] },
      },
    });

    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();
    await tabs.rebaseTab(5);

    expect(patch_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/5/',
      { base_filters: { statuses: ['sent'] } },
    );
    expect(tabs.savedTabs.value[0].base_filters).toEqual({ statuses: ['sent'] });
  });
});

describe('administración de la tira', () => {
  it('updateTab esconde una pestaña sin borrarla', async () => {
    get_request.mockResolvedValueOnce({
      data: [{ id: 3, name: 'De temporada', filters: {}, is_hidden: false }],
    });
    patch_request.mockResolvedValueOnce({
      data: { id: 3, name: 'De temporada', filters: {}, is_hidden: true },
    });
    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    await tabs.updateTab(3, { is_hidden: true });

    expect(patch_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/3/', { is_hidden: true },
    );
    expect(tabs.savedTabs.value[0].is_hidden).toBe(true);
    expect(tabs.savedTabs.value[0].name).toBe('De temporada');
  });

  it('updateTab revierte la fila si el PATCH falla', async () => {
    get_request.mockResolvedValueOnce({
      data: [{ id: 3, name: 'De temporada', filters: {}, is_hidden: false }],
    });
    patch_request.mockRejectedValueOnce(new Error('500'));
    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    await tabs.updateTab(3, { is_hidden: true });

    expect(tabs.savedTabs.value[0].is_hidden).toBe(false);
  });

  it('reorderTabs manda el orden y adopta la lista que vuelve', async () => {
    get_request.mockResolvedValueOnce({
      data: [
        { id: 1, name: 'Uno', order: 0 },
        { id: 2, name: 'Dos', order: 1 },
      ],
    });
    create_request.mockResolvedValueOnce({
      data: [
        { id: 2, name: 'Dos', order: 0 },
        { id: 1, name: 'Uno', order: 1 },
      ],
    });
    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    const ok = await tabs.reorderTabs([2, 1]);

    expect(ok).toBe(true);
    expect(create_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/reorder/',
      { view: 'proposal', ids: [2, 1] },
    );
    expect(tabs.savedTabs.value.map((t) => t.name)).toEqual(['Dos', 'Uno']);
  });

  it('reorderTabs devuelve la lista a su sitio si el servidor la rechaza', async () => {
    // El arrastre ya movio el chip en pantalla. Si la lista vuelve identica,
    // la tira no se entera y el orden rechazado se queda ahi como si se
    // hubiera guardado.
    const loaded = [
      { id: 1, name: 'Uno', order: 0 },
      { id: 2, name: 'Dos', order: 1 },
    ];
    get_request.mockResolvedValueOnce({ data: loaded });
    create_request.mockRejectedValueOnce(new Error('boom'));
    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();
    const before = tabs.savedTabs.value;

    const ok = await tabs.reorderTabs([2, 1]);

    expect(ok).toBe(false);
    expect(tabs.savedTabs.value.map((t) => t.name)).toEqual(['Uno', 'Dos']);
    // Otra identidad de array: es lo que hace que la tira vuelva a leer.
    expect(tabs.savedTabs.value).not.toBe(before);
  });

  it('reorderTabs conserva el lugar de las ocultas que la tira no nombra', async () => {
    // The strip only lists what it shows. Numbering from the visible list
    // alone would hand the hidden tab an order it never asked for.
    get_request.mockResolvedValueOnce({
      data: [
        { id: 1, name: 'Uno', order: 0 },
        { id: 2, name: 'Oculta', order: 1, is_hidden: true },
        { id: 3, name: 'Tres', order: 2 },
      ],
    });
    create_request.mockResolvedValueOnce({ data: [] });
    const tabs = useSavedFilterTabs('proposal');
    await tabs.loadTabs();

    await tabs.reorderTabs([3, 1]);

    expect(create_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/reorder/',
      { view: 'proposal', ids: [3, 2, 1] },
    );
  });

  it('reorderTabs ubica un builtin por su builtin_key', async () => {
    // The strip knows a builtin by its code-level string id; the row holding
    // its order is reached through `builtin_key`.
    get_request.mockResolvedValueOnce({
      data: [
        { id: 10, name: 'Perdidos', order: 0, builtin_key: 'lost' },
        { id: 11, name: 'Líquidos', order: 1 },
      ],
    });
    create_request.mockResolvedValueOnce({ data: [] });
    const tabs = useSavedFilterTabs('accounting_income');
    await tabs.loadTabs();

    await tabs.reorderTabs([11, 'lost']);

    expect(create_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/reorder/',
      { view: 'accounting_income', ids: [11, 10] },
    );
  });

  it('resetTabs adopta lo que el servidor deja, propias incluidas', async () => {
    get_request.mockResolvedValueOnce({ data: [] });
    create_request.mockResolvedValueOnce({
      data: [
        { id: 7, name: 'Fallidos', is_seeded: true },
        { id: 9, name: 'La mía', is_seeded: false },
      ],
    });
    const tabs = useSavedFilterTabs('accounting_history_sends');
    await tabs.loadTabs();

    const ok = await tabs.resetTabs();

    expect(ok).toBe(true);
    expect(create_request).toHaveBeenCalledWith(
      'accounts/saved-filter-tabs/reset/',
      { view: 'accounting_history_sends' },
    );
    expect(tabs.savedTabs.value.map((t) => t.name)).toEqual(['Fallidos', 'La mía']);
  });
});

describe('sameFilters across the move to multi-value dimensions', () => {
  it('reads a scalar and its one-element array as the same cut', () => {
    // A tab saved before the dimension went multi-valued must not report drift
    // against the very definition it was restored from.
    expect(sameFilters({ kind: 'expected' }, { kind: ['expected'] })).toBe(true);
  });

  it('still sees a real difference when a second value was added', () => {
    expect(sameFilters(
      { paymentStatus: ['pending'] },
      { paymentStatus: ['pending', 'partial'] },
    )).toBe(false);
  });

  it('still sees a difference between two different single values', () => {
    expect(sameFilters({ kind: 'expected' }, { kind: ['liquid'] })).toBe(false);
  });
});

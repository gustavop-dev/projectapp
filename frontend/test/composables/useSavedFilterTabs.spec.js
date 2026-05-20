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
import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

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

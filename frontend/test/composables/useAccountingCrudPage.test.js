/**
 * Tests for useAccountingCrudPage: the lastMutatedId row-flash feedback
 * (set on create/update success, expiry after the highlight delay, no-op on
 * failed submits) and the success copy runMutation puts on the toast.
 */
import { computed, nextTick, reactive, ref } from 'vue';
import { useAccountingCrudPage } from '../../composables/useAccountingCrudPage';
import { usePanelNotify } from '../../composables/usePanelNotify';

const labels = {
  created: 'Registro creado',
  updated: 'Registro actualizado',
  deleted: 'Registro eliminado',
  saveErrorTitle: 'No se pudo guardar',
  deleteErrorTitle: 'No se pudo eliminar',
  deleteTitle: 'Eliminar registro',
  deleteMessage: () => 'Se eliminará el registro.',
};

function makePage(store, options = {}) {
  return useAccountingCrudPage({
    entity: 'incomes',
    store,
    labels,
    filteredRecords: computed(() => []),
    ...options,
  });
}

describe('useAccountingCrudPage — lastMutatedId', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('sets lastMutatedId with the created record id', async () => {
    const store = {
      createRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 7 } }),
    };
    const page = makePage(store);

    await page.handleSubmit({ concept: 'Nuevo' });

    expect(page.lastMutatedId.value).toBe(7);
  });

  it('sets lastMutatedId with the edited record id', async () => {
    const store = {
      updateRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 3 } }),
    };
    const page = makePage(store);
    page.editingRecord.value = { id: 3 };

    await page.handleSubmit({ concept: 'Editado' });

    expect(page.lastMutatedId.value).toBe(3);
  });

  it('clears lastMutatedId after the highlight delay', async () => {
    const store = {
      createRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 9 } }),
    };
    const page = makePage(store);

    await page.handleSubmit({ concept: 'Nuevo' });
    expect(page.lastMutatedId.value).toBe(9);

    jest.advanceTimersByTime(2500);
    expect(page.lastMutatedId.value).toBeNull();
  });

  it('does not set lastMutatedId when the submit fails', async () => {
    const store = {
      createRecord: jest.fn().mockResolvedValue({ success: false, message: 'boom' }),
    };
    const page = makePage(store);

    await page.handleSubmit({ concept: 'Nuevo' });

    expect(page.lastMutatedId.value).toBeNull();
  });
});

describe('useAccountingCrudPage — seeded (duplicate) form', () => {
  it('creates instead of editing the record the seed was copied from', async () => {
    const store = {
      createRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 11 } }),
      updateRecord: jest.fn(),
    };
    const page = makePage(store);

    page.openSeededModal({ concept: 'Kore - Hosting anual', kind: 'expected' });
    expect(page.editingRecord.value).toBeNull();
    expect(page.seedRecord.value).toMatchObject({ concept: 'Kore - Hosting anual' });

    await page.handleSubmit({ concept: 'Kore - Hosting anual' });

    expect(store.createRecord).toHaveBeenCalledWith(
      'incomes', { concept: 'Kore - Hosting anual' },
    );
    expect(store.updateRecord).not.toHaveBeenCalled();
  });

  it('drops the seed on close, so the next Nuevo opens empty', () => {
    const page = makePage({});

    page.openSeededModal({ concept: 'Kore - Hosting anual' });
    page.closeModal();

    expect(page.seedRecord.value).toBeNull();
    expect(page.isModalOpen.value).toBe(false);
  });

  it('drops the seed when an edit opens, so the edit is never seeded', () => {
    const page = makePage({});

    page.openSeededModal({ concept: 'Kore - Hosting anual' });
    page.openEditModal({ id: 4, concept: 'Otro' });

    expect(page.seedRecord.value).toBeNull();
    expect(page.editingRecord.value).toMatchObject({ id: 4 });
  });

  describe('success copy', () => {
    const notify = usePanelNotify();

    beforeEach(() => notify.clearAll());
    afterEach(() => notify.clearAll());

    function pageWithDuplicatedCopy(store) {
      return useAccountingCrudPage({
        entity: 'incomes',
        store,
        labels: { ...labels, duplicated: 'Ingreso duplicado' },
        filteredRecords: computed(() => []),
      });
    }

    it('announces a seeded create as a duplicate, not as a plain create', async () => {
      const store = {
        createRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 11 } }),
      };
      const page = pageWithDuplicatedCopy(store);

      page.openSeededModal({ concept: 'Kore - Hosting anual' });
      await page.handleSubmit({ concept: 'Kore - Hosting anual' });

      expect(notify.notifications.value[0]).toMatchObject({
        type: 'success',
        title: 'Ingreso duplicado',
      });
    });

    it('keeps the created wording for a create that was not seeded', async () => {
      const store = {
        createRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 12 } }),
      };
      const page = pageWithDuplicatedCopy(store);

      page.openCreateModal();
      await page.handleSubmit({ concept: 'Nuevo' });

      expect(notify.notifications.value[0]).toMatchObject({
        title: 'Registro creado',
      });
    });

    it('falls back to the created wording when the page defines no duplicate copy', async () => {
      const store = {
        createRecord: jest.fn().mockResolvedValue({ success: true, data: { id: 13 } }),
      };
      const page = makePage(store);

      page.openSeededModal({ concept: 'Kore - Hosting anual' });
      await page.handleSubmit({ concept: 'Kore - Hosting anual' });

      expect(notify.notifications.value[0]).toMatchObject({
        title: 'Registro creado',
      });
    });
  });
});

describe('useAccountingCrudPage — runMutation success copy', () => {
  const notify = usePanelNotify();

  beforeEach(() => notify.clearAll());
  afterEach(() => notify.clearAll());

  it('resolves title and detail against the result so a bulk run can report its real count', async () => {
    const page = makePage({});

    await page.runMutation(
      () => Promise.resolve({ success: true, data: { updated: 3 } }),
      {
        successTitle: 'Cliente asignado',
        successDetail: (result) => `${result.data.updated} de 5 registros actualizados.`,
      },
    );

    expect(notify.notifications.value[0]).toMatchObject({
      type: 'success',
      title: 'Cliente asignado',
      detail: '3 de 5 registros actualizados.',
    });
  });

  it('still takes plain strings, so the existing call sites keep working', async () => {
    const page = makePage({});

    await page.runMutation(
      () => Promise.resolve({ success: true, data: { id: 1 } }),
      { successTitle: 'Registro creado' },
    );

    expect(notify.notifications.value[0]).toMatchObject({
      title: 'Registro creado',
      detail: '',
    });
  });
});

describe('useAccountingCrudPage — field errors', () => {
  const notify = usePanelNotify();

  beforeEach(() => notify.clearAll());
  afterEach(() => notify.clearAll());

  it('leaves serializer field errors to the form when configured', async () => {
    const result = {
      success: false,
      message: 'Elige un cliente válido.',
      fieldErrors: { client_profile_id: 'Elige un cliente válido.' },
    };
    const store = { createRecord: jest.fn().mockResolvedValue(result) };
    const page = makePage(store, { suppressFieldErrorNotification: true });

    expect(await page.handleSubmit({})).toEqual(result);
    expect(notify.notifications.value).toHaveLength(0);
  });

  it('still announces a general failure when field notifications are suppressed', async () => {
    const store = {
      createRecord: jest.fn().mockResolvedValue({
        success: false,
        message: 'Servicio no disponible.',
        fieldErrors: null,
      }),
    };
    const page = makePage(store, { suppressFieldErrorNotification: true });

    await page.handleSubmit({});

    expect(notify.notifications.value[0]).toMatchObject({
      type: 'error',
      detail: 'Servicio no disponible.',
    });
  });
});

describe('useAccountingCrudPage — page position', () => {
  const rows = (n) => Array.from({ length: n }, (_, i) => ({ id: i + 1 }));

  function makePaginatedPage(records, resetPageOn) {
    return useAccountingCrudPage({
      entity: 'incomes',
      store: {},
      labels,
      filteredRecords: records,
      resetPageOn,
    });
  }

  it('goes back to page 1 when the filters narrow the working set', async () => {
    const records = ref(rows(40));
    const filters = reactive({ search: '' });
    const page = makePaginatedPage(records, filters);
    page.goToPage(3);

    filters.search = 'hosting';
    await nextTick();

    expect(page.currentPage.value).toBe(1);
  });

  it('stays on the current page when a mutation only rebuilds the rows', async () => {
    // A delete splices the store list and the page refetches, so the array
    // identity changes on every mutation. Resetting on that dropped the
    // reader on page 1 after deleting a row from page 3.
    const records = ref(rows(40));
    const filters = reactive({ search: '' });
    const page = makePaginatedPage(records, filters);
    page.goToPage(3);

    records.value = rows(39);
    await nextTick();

    expect(page.currentPage.value).toBe(3);
  });

  it('clamps to the last page when the rows shrink past it', async () => {
    const records = ref(rows(40));
    const page = makePaginatedPage(records, reactive({ search: '' }));
    page.goToPage(3);

    records.value = rows(16);
    await nextTick();

    expect(page.currentPage.value).toBe(2);
  });

  it('falls back to the rows trigger for a page that declares no filters', async () => {
    const records = ref(rows(40));
    const page = makePaginatedPage(records, null);
    page.goToPage(3);

    records.value = rows(39);
    await nextTick();

    expect(page.currentPage.value).toBe(1);
  });
});

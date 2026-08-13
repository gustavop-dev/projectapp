/**
 * Tests for useAccountingCrudPage: the lastMutatedId row-flash feedback
 * (set on create/update success, expiry after the highlight delay, no-op on
 * failed submits) and the success copy runMutation puts on the toast.
 */
import { computed } from 'vue';
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

function makePage(store) {
  return useAccountingCrudPage({
    entity: 'incomes',
    store,
    labels,
    filteredRecords: computed(() => []),
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

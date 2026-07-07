/**
 * Tests for the lastMutatedId row-flash feedback in useAccountingCrudPage.
 *
 * Covers: set on create/update success, expiry after the highlight delay,
 * and no-op on failed submits.
 */
import { computed } from 'vue';
import { useAccountingCrudPage } from '../../composables/useAccountingCrudPage';

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

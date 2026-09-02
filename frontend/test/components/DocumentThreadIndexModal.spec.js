import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import DocumentThreadIndexModal from '../../components/panel/documents/DocumentThreadIndexModal.vue';
import { useDocumentThreadStore } from '../../stores/document_threads';

const threadRow = {
  id: 7,
  title: 'Entrega del proyecto',
  document_count: 3,
  first_occurred_on: '2026-08-01',
  last_occurred_on: '2026-08-20',
  latest_item: { document_id: 12, title: 'Aprobación' },
  documents: [
    { document_id: 10, title: 'Acta inicial' },
    { document_id: 11, title: 'Corrección' },
  ],
  documents_truncated: false,
  updated_at: '2026-08-20T10:00:00+00:00',
};

function mountIndex() {
  return mount(DocumentThreadIndexModal, {
    props: { modelValue: true },
    global: {
      stubs: {
        Teleport: true,
        BaseModal: {
          props: ['modelValue'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseAlert: { template: '<div><slot /></div>' },
        BaseBadge: { template: '<span><slot /></span>' },
        BaseEmptyState: {
          props: ['title', 'description'],
          template: '<div>{{ title }} {{ description }}</div>',
        },
        BaseSegmented: {
          props: ['modelValue', 'options'],
          template: '<div />',
        },
        BaseActionButton: { template: '<button />' },
        BasePagination: true,
      },
    },
  });
}

describe('DocumentThreadIndexModal', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDocumentThreadStore();
  });

  it('lists threads with their span and members', async () => {
    jest.spyOn(store, 'fetchThreads').mockImplementation(async () => {
      store.threads = [threadRow];
      store.threadCount = 1;
      return { success: true, data: { count: 1, results: [threadRow] } };
    });

    const wrapper = mountIndex();
    await flushPromises();

    const row = wrapper.get('[data-testid="thread-index-row-7"]');
    expect(row.text()).toContain('Entrega del proyecto');
    expect(row.text()).toContain('Hilo · 3');
    expect(row.text()).toContain('01/08/2026 → 20/08/2026');
    expect(row.text()).toContain('Acta inicial · Corrección');
  });

  it('opens a thread through its first member', async () => {
    jest.spyOn(store, 'fetchThreads').mockImplementation(async () => {
      store.threads = [threadRow];
      store.threadCount = 1;
      return { success: true, data: { count: 1, results: [threadRow] } };
    });

    const wrapper = mountIndex();
    await flushPromises();

    await wrapper.get('[data-testid="thread-index-row-7"]').trigger('click');

    // El workspace de hilo se hidrata desde un documento, no desde el hilo.
    expect(wrapper.emitted('open-thread')[0]).toEqual([
      { id: 10, title: 'Acta inicial' },
    ]);
  });

  it('explains an empty index instead of showing a blank panel', async () => {
    jest.spyOn(store, 'fetchThreads').mockImplementation(async () => {
      store.threads = [];
      store.threadCount = 0;
      return { success: true, data: { count: 0, results: [] } };
    });

    const wrapper = mountIndex();
    await flushPromises();

    expect(wrapper.text()).toContain('No hay hilos');
    expect(wrapper.text()).toContain('Enlaza dos documentos relacionados');
  });

  it('surfaces a load failure', async () => {
    jest.spyOn(store, 'fetchThreads').mockResolvedValue({
      success: false,
      message: 'No se pudieron cargar los hilos.',
    });

    const wrapper = mountIndex();
    await flushPromises();

    expect(wrapper.text()).toContain('No se pudieron cargar los hilos.');
  });
});

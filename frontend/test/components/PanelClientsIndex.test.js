global.useLocalePath = () => (path) => path;
global.definePageMeta = jest.fn();

jest.mock('vue-router', () => ({
  useRoute: () => ({ query: {}, path: '/panel/clients' }),
  useRouter: () => ({ replace: jest.fn() }),
}));

import { mount, flushPromises } from '@vue/test-utils';
import PanelClientsIndex from '../../pages/panel/clients/index.vue';

const mockStore = {
  clients: [],
  isLoading: false,
  isUpdating: false,
  fetchClients: jest.fn(),
  fetchClient: jest.fn(),
  createClient: jest.fn(),
  deleteClient: jest.fn(),
};

jest.mock('../../stores/proposalClients', () => ({
  useProposalClientsStore: () => mockStore,
}));

jest.mock('../../composables/useConfirmModal', () => ({
  useConfirmModal: () => ({
    confirmState: {
      open: false,
      title: '',
      message: '',
    confirmText: 'Confirmar',
    cancelText: 'Cancelar',
    variant: 'warning',
  },
    requestConfirm: jest.fn(),
    handleConfirmed: jest.fn(),
    handleCancelled: jest.fn(),
  }),
}));

function mountPage() {
  return mount(PanelClientsIndex, {
    global: {
      stubs: {
        ConfirmModal: {
          template: '<div />',
        },
        NuxtLink: {
          template: '<a><slot /></a>',
        },
        BaseInput: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          inheritAttrs: false,
          template: '<input v-bind="$attrs" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseButton: {
          inheritAttrs: false,
          template: '<button v-bind="$attrs"><slot /></button>',
        },
      },
    },
  });
}

describe('panel/clients index page', () => {
  beforeEach(() => {
    mockStore.clients = [];
    mockStore.isLoading = false;
    mockStore.isUpdating = false;
    mockStore.fetchClients.mockReset().mockResolvedValue({ success: true, data: [] });
    mockStore.fetchClient.mockReset().mockResolvedValue({ success: true, data: { proposals: [] } });
    mockStore.createClient.mockReset().mockResolvedValue({ success: true });
    mockStore.deleteClient.mockReset().mockResolvedValue({ success: true });
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('loads orphan clients when the Huérfanos tab is selected', async () => {
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-tab-orphans"]').trigger('click');
    await flushPromises();

    expect(mockStore.fetchClients).toHaveBeenNthCalledWith(1, { search: '', orphans: null });
    expect(mockStore.fetchClients).toHaveBeenNthCalledWith(2, { search: '', orphans: true });
  });

  it('submits the create modal payload trimmed and refreshes the list', async () => {
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-new-button"]').trigger('click');
    await wrapper.get('[data-testid="clients-new-name"]').setValue('  Laura Gómez  ');
    await wrapper.get('[data-testid="clients-new-email"]').setValue('  laura@example.com  ');
    await wrapper.get('[data-testid="clients-new-company"]').setValue('  LauraCo  ');
    await wrapper.get('[data-testid="clients-new-submit"]').trigger('submit');
    await flushPromises();

    expect(mockStore.createClient).toHaveBeenCalledWith({
      name: 'Laura Gómez',
      email: 'laura@example.com',
      phone: '',
      company: 'LauraCo',
    });
    expect(mockStore.fetchClients).toHaveBeenCalledTimes(2);
  });

  it('debounces search before refetching clients', async () => {
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-search-input"]').setValue('ana');
    expect(mockStore.fetchClients).toHaveBeenCalledTimes(1);

    jest.advanceTimersByTime(250);
    await flushPromises();

    expect(mockStore.fetchClients).toHaveBeenNthCalledWith(2, { search: 'ana', orphans: null });
  });
});

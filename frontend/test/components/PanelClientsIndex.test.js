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

jest.mock('../../stores/proposal_clients', () => ({
  useProposalClientsStore: () => mockStore,
}));

jest.mock('../../stores/proposals', () => ({
  useProposalStore: () => ({
    deleteProposal: jest.fn().mockResolvedValue({ success: true }),
  }),
}));

jest.mock('../../stores/diagnostics', () => ({
  useDiagnosticsStore: () => ({
    remove: jest.fn().mockResolvedValue({ success: true }),
  }),
}));

jest.mock('../../composables/usePanelRefresh', () => ({
  usePanelRefresh: jest.fn(),
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

    expect(mockStore.fetchClients).toHaveBeenNthCalledWith(1, { search: '', orphans: null, inactive: false, silent: false });
    expect(mockStore.fetchClients).toHaveBeenNthCalledWith(2, { search: '', orphans: true, inactive: false, silent: false });
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
      nit: '',
      billing_code: '',
    });
    expect(mockStore.fetchClients).toHaveBeenCalledTimes(2);
  });

  it('creates a client with its billing identity in one step', async () => {
    // The whole point of the parity fix: NIT and código are on the create form,
    // so a client no longer has to be created and then edited to be complete.
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-new-button"]').trigger('click');
    await wrapper.get('[data-testid="clients-new-name"]').setValue('G&M');
    await wrapper.get('[data-testid="clients-new-nit"]').setValue('901234567-1');
    await wrapper.get('[data-testid="clients-new-billing-code"]').setValue('  g&m  ');
    await wrapper.get('[data-testid="clients-new-submit"]').trigger('submit');
    await flushPromises();

    expect(mockStore.createClient).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'G&M',
        nit: '901234567-1',
        // Normalized the same way the edit modal always did.
        billing_code: 'G&M',
      }),
    );
  });

  it('creates a client from the name alone', async () => {
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-new-button"]').trigger('click');
    await wrapper.get('[data-testid="clients-new-name"]').setValue('Solo Nombre');
    await wrapper.get('[data-testid="clients-new-submit"]').trigger('submit');
    await flushPromises();

    expect(mockStore.createClient).toHaveBeenCalledWith({
      name: 'Solo Nombre',
      email: '',
      phone: '',
      company: '',
      nit: '',
      billing_code: '',
    });
  });

  it('surfaces the backend billing-code error on the create modal', async () => {
    // It used to read only `message`, so an `invalid_billing_code` answer left
    // the operator with the generic fallback and no idea what was wrong.
    mockStore.createClient.mockResolvedValueOnce({
      success: false,
      errors: { error: 'invalid_billing_code', message: 'El código debe tener entre 2 y 12 caracteres.' },
    });
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-new-button"]').trigger('click');
    await wrapper.get('[data-testid="clients-new-name"]').setValue('G&M');
    await wrapper.get('[data-testid="clients-new-billing-code"]').setValue('G/M');
    await wrapper.get('[data-testid="clients-new-submit"]').trigger('submit');
    await flushPromises();

    expect(wrapper.text()).toContain('El código debe tener entre 2 y 12 caracteres.');
  });

  it('debounces search before refetching clients', async () => {
    const wrapper = mountPage();
    await flushPromises();

    await wrapper.get('[data-testid="clients-search-input"]').setValue('ana');
    expect(mockStore.fetchClients).toHaveBeenCalledTimes(1);

    jest.advanceTimersByTime(250);
    await flushPromises();

    expect(mockStore.fetchClients).toHaveBeenNthCalledWith(2, { search: 'ana', orphans: null, inactive: false, silent: false });
  });
});

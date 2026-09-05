import { createPinia, setActivePinia } from 'pinia';
import { flushPromises, mount } from '@vue/test-utils';
import ReceivablesModal from '~/components/accounting/ReceivablesModal.vue';
import { useAccountingStore } from '~/stores/accounting';
import { get_request, patch_request } from '~/stores/services/request_http';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const ROWS = [
  {
    id: 1,
    concept: 'Kore - Entrega',
    client: 10,
    client_name: 'Kore',
    project: 100,
    project_name: 'Kore v2',
    period_label: 'Septiembre 2026',
    kind: 'expected',
    ledger: 'company',
    payment_status: 'partial',
    is_receivable_candidate: true,
    collection_confidence: 'high',
    total_amount: '1000000.00',
    paid_amount: '400000.00',
    pending_amount: '600000.00',
  },
  {
    id: 2,
    concept: 'Hosting Acme',
    client: 20,
    client_name: 'Acme',
    project: null,
    project_name: null,
    period_label: 'Octubre 2026',
    kind: 'expected',
    ledger: 'company',
    payment_status: 'pending',
    is_receivable_candidate: true,
    collection_confidence: '',
    total_amount: '500000.00',
    paid_amount: '0.00',
    pending_amount: '500000.00',
  },
];

const SUMMARY = {
  high_total: '1000000.00',
  high_count: 1,
  selected_count: 2,
  selected_total: '1500000.00',
  paid_total: '400000.00',
  pending_total: '1100000.00',
  by_confidence: {
    high: {
      count: 1, total_amount: '1000000.00',
      paid_amount: '400000.00', pending_amount: '600000.00',
    },
    medium: { count: 0, total_amount: '0.00', paid_amount: '0.00', pending_amount: '0.00' },
    low: { count: 0, total_amount: '0.00', paid_amount: '0.00', pending_amount: '0.00' },
    unclassified: {
      count: 1, total_amount: '500000.00',
      paid_amount: '0.00', pending_amount: '500000.00',
    },
  },
};

function mountModal(props = {}) {
  return mount(ReceivablesModal, {
    props: { open: true, ...props },
    global: {
      plugins: [createPinia()],
      stubs: {
        NuxtLink: { template: '<a><slot /></a>' },
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ReceivablesModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
    get_request.mockResolvedValue({ data: { results: ROWS, summary: SUMMARY } });
  });

  afterEach(() => jest.restoreAllMocks());

  it('loads the global candidate universe when opened', async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(get_request).toHaveBeenCalledWith('accounting/receivables/');
    expect(wrapper.get('[data-testid="receivables-summary-tab"]').text())
      .toContain('$1.000.000 COP');
  });

  it('renders the four confidence summaries', async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.findAll('[data-testid^="receivables-group-"]')).toHaveLength(4);
  });

  it('persists candidate changes from the management tab', async () => {
    const wrapper = mountModal();
    await flushPromises();
    patch_request.mockResolvedValue({
      data: { ...ROWS[0], is_receivable_candidate: false },
    });

    await wrapper.findAll('[role="tab"]')[2].trigger('click');
    await wrapper.findAll('[role="switch"]')[0].trigger('click');
    await flushPromises();

    expect(patch_request).toHaveBeenCalledWith(
      'accounting/incomes/1/update/',
      { is_receivable_candidate: false },
    );
  });

  it('opens candidate management grouped by client', async () => {
    const wrapper = mountModal();
    await flushPromises();

    await wrapper.findAll('[role="tab"]')[2].trigger('click');

    expect(wrapper.get('[data-testid="receivables-group-client"]').attributes('aria-selected'))
      .toBe('true');
    expect(wrapper.get('[data-testid="receivable-candidate-group-10"]').text())
      .toContain('Kore');
    expect(wrapper.get('[data-testid="receivable-candidate-group-total_amount-10"]').text())
      .toContain('$1.000.000 COP');
  });

  it('switches candidate management to project groups', async () => {
    const wrapper = mountModal();
    await flushPromises();
    await wrapper.findAll('[role="tab"]')[2].trigger('click');

    await wrapper.get('[data-testid="receivables-group-project"]').trigger('click');

    expect(wrapper.get('[data-testid="receivable-candidate-group-100"]').text())
      .toContain('Kore v2');
    expect(wrapper.get('[data-testid="receivable-candidate-group-none"]').text())
      .toContain('Sin proyecto');
  });

  it('offers the existing flat candidate list as classic view', async () => {
    const wrapper = mountModal();
    await flushPromises();
    await wrapper.findAll('[role="tab"]')[2].trigger('click');

    await wrapper.get('[data-testid="receivables-view-classic"]').trigger('click');

    expect(wrapper.find('[data-testid="receivables-group-by"]').exists()).toBe(false);
    expect(wrapper.findAll('[data-testid="receivable-row"]')).toHaveLength(4);
  });

  it('restores client grouping when the modal reopens', async () => {
    const wrapper = mountModal();
    await flushPromises();
    await wrapper.findAll('[role="tab"]')[2].trigger('click');
    await wrapper.get('[data-testid="receivables-group-project"]').trigger('click');
    await wrapper.get('[data-testid="receivables-view-classic"]').trigger('click');

    await wrapper.setProps({ open: false });
    await wrapper.setProps({ open: true });
    await flushPromises();
    await wrapper.findAll('[role="tab"]')[2].trigger('click');

    expect(wrapper.get('[data-testid="receivables-view-grouped"]').attributes('aria-selected'))
      .toBe('true');
    expect(wrapper.get('[data-testid="receivables-group-client"]').attributes('aria-selected'))
      .toBe('true');
  });

  it('shows the request error state', async () => {
    get_request.mockRejectedValue(new Error('boom'));
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.text()).toContain('No se pudieron cargar los pendientes por cobrar');
  });

  // Falla si Reintentar no vuelve a cargar el modal después de un error temporal.
  it('reloads the receivables summary when retry succeeds', async () => {
    get_request.mockRejectedValueOnce(new Error('temporary outage'));
    const wrapper = mountModal();
    await flushPromises();

    const retryButton = wrapper.findAll('button')
      .find((button) => button.text() === 'Reintentar');
    await retryButton.trigger('click');
    await flushPromises();

    expect(get_request).toHaveBeenCalledTimes(2);
    expect(get_request).toHaveBeenLastCalledWith('accounting/receivables/');
    expect(wrapper.get('[data-testid="receivables-summary-tab"]').text())
      .toContain('$1.000.000 COP');
  });

  // Falla si un modal cerrado inicia una carga y deja el store en estado de espera.
  it('does not fetch while closed', async () => {
    mountModal({ open: false });
    await flushPromises();

    expect(get_request).not.toHaveBeenCalled();
    expect(useAccountingStore().receivablesLoading).toBe(false);
  });
});

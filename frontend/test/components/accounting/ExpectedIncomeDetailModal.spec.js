import { mount, flushPromises } from '@vue/test-utils';
import ExpectedIncomeDetailModal from '~/components/accounting/ExpectedIncomeDetailModal.vue';
import { get_request } from '~/stores/services/request_http';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const ROWS = [
  {
    id: 1,
    concept: 'Kore v2 (Fase 1) - Inicio 40%',
    period_label: 'Julio 2026',
    total_amount: '1000000.00',
    paid_amount: '400000.00',
    pending_amount: '600000.00',
    payment_status: 'partial',
    payment_status_label: 'Parcial',
  },
  {
    id: 2,
    concept: 'Hosting anual Acme',
    period_label: '17 Julio 2026',
    total_amount: '500000.00',
    paid_amount: '500000.00',
    pending_amount: '0.00',
    payment_status: 'paid',
    payment_status_label: 'Pagado',
  },
];

function mountModal(props = {}) {
  return mount(ExpectedIncomeDetailModal, {
    props: {
      open: true,
      period: '2026-07',
      periodLabel: 'Julio 2026',
      total: '600000.00',
      ...props,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['update:modelValue', 'close'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseButton: {
          props: ['variant', 'type'],
          emits: ['click'],
          template:
            '<button :type="type || \'button\'" @click="$emit(\'click\', $event)"><slot /></button>',
        },
      },
    },
  });
}

describe('ExpectedIncomeDetailModal', () => {
  beforeEach(() => {
    get_request.mockReset();
  });

  it('fetches the month expected company incomes when opened', async () => {
    get_request.mockResolvedValue({ data: { results: ROWS } });
    mountModal();
    await flushPromises();

    expect(get_request).toHaveBeenCalledWith(
      'accounting/incomes/?kind=expected&ledger=company&date_from=2026-07-01&date_to=2026-07-31',
    );
  });

  it('renders one row per record and the footer pending sum', async () => {
    get_request.mockResolvedValue({ data: { results: ROWS } });
    const wrapper = mountModal();
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="expected-income-row"]');
    expect(rows).toHaveLength(2);
    expect(rows[0].text()).toContain('Kore v2 (Fase 1) - Inicio 40%');
    expect(rows[0].text()).toContain('Parcial');
    expect(rows[1].text()).toContain('Pagado');
    expect(
      wrapper.find('[data-testid="expected-income-pending-sum"]').text(),
    ).toContain('600.000');
  });

  it('shows the empty state when the month has no expected incomes', async () => {
    get_request.mockResolvedValue({ data: { results: [] } });
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.text()).toContain('Sin ingresos esperados este mes');
    expect(wrapper.findAll('[data-testid="expected-income-row"]')).toHaveLength(0);
  });

  it('shows an error message when the request fails', async () => {
    get_request.mockRejectedValue(new Error('boom'));
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.text()).toContain('No se pudieron cargar los ingresos esperados');
  });

  it('does not fetch while closed', async () => {
    get_request.mockResolvedValue({ data: { results: [] } });
    mountModal({ open: false });
    await flushPromises();

    expect(get_request).not.toHaveBeenCalled();
  });
});

import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import CollectionAccountDetailModal from '~/components/accounting/CollectionAccountDetailModal.vue';
import { get_request } from '~/stores/services/request_http';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const HOSTING_ROW = {
  id: 7,
  public_number: 'PA-KORE-001',
  billing_concept: 'Servicio de hosting kore.com.co',
  total: '550002.00',
  issue_date: '2026-06-01',
  due_date: '2026-06-15',
  commercial_status: 'issued',
  commercial_status_label: 'Emitida',
  is_overdue: false,
  origin: 'hosting',
  client: 14,
  client_display_name: 'Germán Franco',
  customer_name: 'Germán Franco',
  project_name: 'Kore',
  income_record_id: null,
};

const INCOME_ROW = {
  ...HOSTING_ROW,
  id: 9,
  origin: 'income',
  income_record_id: 42,
  public_number: 'PA-MIMITTOS-001',
  // What the document actually printed, before the identity rule existed.
  customer_name: 'MIMITTOS',
  client_display_name: 'Daniel Felipe Corredor Castiblanco',
  project_name: 'MIMITTOS',
};

const DOCUMENT = {
  id: 9,
  items: [
    {
      id: 1,
      description: 'Hosting trimestral',
      period_start: '2026-08-01',
      period_end: '2026-10-31',
      line_total: '233280.00',
    },
  ],
};

const INCOME_DETAIL = {
  income: {
    id: 42,
    concept: 'Hosting: Trimestral',
    period_label: 'Agosto 2026',
    total_amount: '233280.00',
    paid_amount: '100000.00',
    pending_amount: '133280.00',
    payment_status: 'partial',
    payment_status_label: 'Parcial',
    gustavo_amount: '116640.00',
    carlos_amount: '116640.00',
    company_amount: '0.00',
  },
  liquid: [
    {
      id: 51,
      concept: 'Abono 1',
      total_amount: '88000.00',
      period_date: '2026-08-05',
    },
  ],
  expenses: [
    {
      id: 61,
      concept: 'Comisión pasarela',
      total_amount: '12000.00',
      period_date: '2026-08-06',
      deduction_type_label: 'Comisión de pasarela',
    },
  ],
  collection_account: null,
};

function mountModal(record) {
  setActivePinia(createPinia());
  return mount(CollectionAccountDetailModal, {
    props: { open: true, record },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['close'],
          template: '<div><slot /></div>',
        },
        BaseButton: {
          props: ['variant'],
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
        BaseSegmented: {
          props: ['modelValue', 'options'],
          emits: ['update:modelValue'],
          template: `<div><button
            v-for="o in options" :key="o.value"
            :data-testid="'seg-' + o.value"
            @click="$emit('update:modelValue', o.value)">{{ o.label }}</button></div>`,
        },
        IncomePaymentStateCell: {
          props: ['row'],
          template: '<span data-testid="payment-state">{{ row.payment_status_label }}</span>',
        },
      },
    },
  });
}

function mockRequests() {
  get_request.mockImplementation((url) => {
    if (url.includes('/detail/')) return Promise.resolve({ data: INCOME_DETAIL });
    return Promise.resolve({ data: DOCUMENT });
  });
}

beforeEach(() => {
  jest.clearAllMocks();
  mockRequests();
});

describe('CollectionAccountDetailModal', () => {
  it('shows the client and the project as two separate facts', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    expect(wrapper.get('[data-testid="collection-detail-client"]').text())
      .toBe('Daniel Felipe Corredor Castiblanco');
    expect(wrapper.get('[data-testid="collection-detail-project"]').text())
      .toBe('MIMITTOS');
  });

  it('warns when the emitted document names someone other than the client', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    const warning = wrapper.get('[data-testid="collection-detail-name-mismatch"]');
    expect(warning.text()).toContain('MIMITTOS');
    expect(warning.text()).toContain('Daniel Felipe Corredor Castiblanco');
  });

  it('stays quiet when the printed name already matches the client', async () => {
    const wrapper = mountModal(HOSTING_ROW);
    await flushPromises();

    expect(wrapper.find('[data-testid="collection-detail-name-mismatch"]').exists())
      .toBe(false);
  });

  it('calls an empty project a diagnostic case rather than missing data', async () => {
    const wrapper = mountModal({ ...INCOME_ROW, project_name: '' });
    await flushPromises();

    expect(wrapper.get('[data-testid="collection-detail-project"]').text())
      .toContain('diagnóstico');
  });

  it('lists the settlement history: liquid children and linked deductions', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="collection-detail-settlement-row"]');
    expect(rows).toHaveLength(2);
    expect(rows[0].text()).toContain('Abono 1');
    expect(rows[1].text()).toContain('Comisión de pasarela');
  });

  it('shows the partner split that the incomes table no longer carries', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    const income = wrapper.get('[data-testid="collection-detail-income"]').text();
    expect(income).toContain('Gustavo');
    expect(income).toContain('Carlos');
  });

  it('explains a hosting cuenta having no income instead of showing nothing', async () => {
    const wrapper = mountModal(HOSTING_ROW);
    await flushPromises();

    expect(wrapper.get('[data-testid="collection-detail-no-income"]').text())
      .toContain('hosting');
    expect(wrapper.find('[data-testid="collection-detail-income"]').exists())
      .toBe(false);
  });

  it('offers going to the income as the secondary exit, not the default', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    await wrapper.get('[data-testid="collection-detail-go-to-income"]').trigger('click');

    expect(wrapper.emitted('go-to-income')[0]).toEqual([42]);
  });

  it('embeds the document inline so previewing never downloads it', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    await wrapper.get('[data-testid="seg-document"]').trigger('click');

    const embed = wrapper.get('[data-testid="collection-detail-pdf"]');
    expect(embed.attributes('src'))
      .toBe('/api/accounting/collection-accounts/9/pdf/?inline=1');
  });

  it('does not fetch the document until the Documento tab is opened', async () => {
    const wrapper = mountModal(INCOME_ROW);
    await flushPromises();

    // The PDF is an <embed src>, so nothing requests it while on Resumen.
    expect(wrapper.find('[data-testid="collection-detail-pdf"]').exists()).toBe(false);
  });
});

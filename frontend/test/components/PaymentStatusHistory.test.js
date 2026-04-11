import { mount } from '@vue/test-utils';
import PaymentStatusHistory from '../../components/platform/PaymentStatusHistory.vue';

const baseHistory = [
  {
    id: 1,
    from_status: 'pending',
    to_status: 'paid',
    created_at: '2024-03-01T10:00:00Z',
    source: 'api',
  },
  {
    id: 2,
    from_status: 'paid',
    to_status: 'failed',
    created_at: '2024-03-02T12:00:00Z',
    source: null,
  },
];

function mountPaymentStatusHistory(props = {}) {
  return mount(PaymentStatusHistory, {
    props: {
      payment: { history: baseHistory },
      ...props,
    },
  });
}

describe('PaymentStatusHistory', () => {
  it('renders nothing when history is empty', () => {
    const wrapper = mount(PaymentStatusHistory, {
      props: { payment: { history: [] } },
    });

    expect(wrapper.find('ul').exists()).toBe(false);
  });

  it('renders history list items', () => {
    const wrapper = mountPaymentStatusHistory();

    expect(wrapper.findAll('li').length).toBe(2);
  });

  it('shows status transition labels', () => {
    const wrapper = mountPaymentStatusHistory();

    expect(wrapper.text()).toContain('Pendiente');
    expect(wrapper.text()).toContain('Pagado');
  });

  it('shows source label when source is present', () => {
    const wrapper = mountPaymentStatusHistory();

    expect(wrapper.text()).toContain('Pago con tarjeta (API)');
  });

  it('shows custom title prop', () => {
    const wrapper = mountPaymentStatusHistory({
      payment: { history: baseHistory },
      title: 'Registro de cambios',
    });

    expect(wrapper.text()).toContain('Registro de cambios');
  });
});

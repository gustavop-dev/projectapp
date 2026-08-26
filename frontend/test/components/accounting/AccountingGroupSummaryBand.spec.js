import { mount } from '@vue/test-utils';

import AccountingGroupSummaryBand from '~/components/accounting/AccountingGroupSummaryBand.vue';

describe('AccountingGroupSummaryBand', () => {
  it('renders each metric as a labelled value', () => {
    const wrapper = mount(AccountingGroupSummaryBand, {
      props: {
        metrics: [
          { key: 'pending', label: 'Por cobrar', value: '$500 COP', testId: 'pending' },
          { key: 'paid', label: 'Recaudado', value: '$300 COP', testId: 'paid' },
        ],
      },
      slots: { default: '<span>Acme SAS</span>' },
    });

    expect(wrapper.text()).toContain('Acme SAS');
    expect(wrapper.get('[data-testid="pending"]').text()).toBe('$500 COP');
    expect(wrapper.get('[data-testid="paid"]').text()).toBe('$300 COP');
  });

  it('renders the five collection-account status counters', () => {
    const wrapper = mount(AccountingGroupSummaryBand, {
      props: {
        statuses: [
          { key: 'draft', label: 'Borradores', value: 1 },
          { key: 'issued', label: 'Emitidas', value: 2 },
          { key: 'overdue', label: 'Vencidas', value: 1 },
          { key: 'paid', label: 'Pagadas', value: 3 },
          { key: 'cancelled', label: 'Anuladas', value: 4 },
        ],
      },
    });

    expect(wrapper.findAll('dl > div').map((item) => item.text())).toEqual([
      'Borradores1', 'Emitidas2', 'Vencidas1', 'Pagadas3', 'Anuladas4',
    ]);
  });
});

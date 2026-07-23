import { mount } from '@vue/test-utils'

import AccountingMonthlyTable from '../../components/accounting/AccountingMonthlyTable.vue'

const ROWS = [
  { period: '2026-01', label: 'Enero', expected: 1000000, liquid: 800000, expenses: 300000, utility: 500000 },
  { period: '2026-02', label: 'Febrero', expected: '500000', liquid: '200000', expenses: '400000', utility: '-200000' },
]

describe('AccountingMonthlyTable', () => {
  it('shows the empty state without a totals row', () => {
    const wrapper = mount(AccountingMonthlyTable, { props: { monthly: [] } })
    expect(wrapper.text()).toContain('Sin registros.')
    expect(wrapper.find('tfoot').exists()).toBe(false)
  })

  it('renders one row per month with formatted money', () => {
    const wrapper = mount(AccountingMonthlyTable, { props: { monthly: ROWS } })
    const enero = wrapper.get('[data-testid="accounting-monthly-row-2026-01"]')
    expect(enero.text()).toContain('Enero')
    expect(enero.text()).toContain('$1.000.000')
    expect(enero.text()).toContain('$800.000')
  })

  it('sums the totals row across numeric strings and numbers', () => {
    const wrapper = mount(AccountingMonthlyTable, { props: { monthly: ROWS } })
    const totals = wrapper.get('tfoot').text()
    expect(totals).toContain('Total')
    expect(totals).toContain('$1.500.000')
    expect(totals).toContain('$300.000')
  })

  it('paints negative utility with the danger class', () => {
    const wrapper = mount(AccountingMonthlyTable, { props: { monthly: ROWS } })
    const febrero = wrapper.get('[data-testid="accounting-monthly-row-2026-02"]')
    expect(febrero.find('.text-danger-strong').text()).toContain('$-200.000')
  })

  it('treats non-numeric values as zero in the totals', () => {
    const wrapper = mount(AccountingMonthlyTable, {
      props: {
        monthly: [
          { period: '2026-03', label: 'Marzo', expected: 'n/a', liquid: 100, expenses: null, utility: 100 },
        ],
      },
    })
    const totals = wrapper.get('tfoot').text()
    expect(totals).toContain('$0')
    expect(totals).toContain('$100')
  })
})

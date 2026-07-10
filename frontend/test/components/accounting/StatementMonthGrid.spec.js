/**
 * Tests for the statements 12-month grid.
 */
import { mount } from '@vue/test-utils'
import StatementMonthGrid from '../../../components/accounting/StatementMonthGrid.vue'

function month(period, label, statements = []) {
  return { period, label, statements, has_processed: false, has_draft: false }
}

const MONTHS = [
  month('2026-01', 'Enero 2026'),
  month('2026-02', 'Febrero 2026', [
    { id: 7, card_name: 'Visa Bancolombia', status: 'processed', status_label: 'Procesado' },
    { id: 8, card_name: 'Mastercard', status: 'draft', status_label: 'Borrador' },
  ]),
]

describe('StatementMonthGrid', () => {
  it('renders one card per month with pending badge when empty', () => {
    const wrapper = mount(StatementMonthGrid, {
      props: { months: MONTHS },
    })
    const january = wrapper.find('[data-testid="statement-month-2026-01"]')
    expect(january.text()).toContain('Pendiente')
    expect(january.text()).toContain('Sin extracto procesado.')
  })

  it('shows one chip per statement with its status label', () => {
    const wrapper = mount(StatementMonthGrid, {
      props: { months: MONTHS },
    })
    const february = wrapper.find('[data-testid="statement-month-2026-02"]')
    expect(february.text()).toContain('Visa Bancolombia')
    expect(february.text()).toContain('Procesado')
    expect(february.text()).toContain('Borrador')
    expect(february.text()).not.toContain('Pendiente')
  })

  it('emits select with the statement id on chip click', async () => {
    const wrapper = mount(StatementMonthGrid, {
      props: { months: MONTHS },
    })
    await wrapper.find('[data-testid="statement-chip-7"]').trigger('click')
    expect(wrapper.emitted('select')).toEqual([[7]])
  })

  it('highlights the selected statement chip', () => {
    const wrapper = mount(StatementMonthGrid, {
      props: { months: MONTHS, selectedId: 7 },
    })
    expect(
      wrapper.find('[data-testid="statement-chip-7"]').classes(),
    ).toContain('border-primary')
  })
})

import { mount } from '@vue/test-utils'

import BaseResponsiveTable from '~/components/base/BaseResponsiveTable.vue'
import { formatMoney } from '~/utils/formatMoney'

const rows = [{
  id: 1,
  name: 'Proyecto Aurora',
  owner: 'María Gómez',
  amount: 1250000,
  internal: 'No mostrar',
  status: 'Activo',
}]

const columns = [
  {
    key: 'name',
    label: 'Proyecto',
    size: 'name',
    responsive: { primary: true, compact: 'keep', portrait: 'keep', landscape: 'keep' },
  },
  {
    key: 'owner',
    label: 'Responsable',
    responsive: { compact: 'group', portrait: 'keep', landscape: 'keep' },
  },
  {
    key: 'amount',
    label: 'Valor',
    format: 'money',
    responsive: { compact: 'group', portrait: 'group', landscape: 'keep' },
  },
  {
    key: 'internal',
    label: 'Interno',
    responsive: { compact: 'hide', portrait: 'hide', landscape: 'hide' },
  },
  {
    key: 'status',
    label: 'Estado',
    responsive: { compact: 'keep', portrait: 'keep', landscape: 'keep' },
  },
]

function mountTable(props = {}) {
  return mount(BaseResponsiveTable, {
    props: { columns, rows, showActions: false, ...props },
  })
}

describe('BaseResponsiveTable', () => {
  it('keeps, groups and hides compact columns from each explicit policy', () => {
    const wrapper = mountTable()
    const headers = wrapper.findAll('th')

    expect(headers[0].classes()).toContain('table-cell')
    expect(headers[1].classes()).toContain('hidden')
    expect(headers[3].classes()).toContain('hidden')

    const compact = wrapper.get('[data-testid="responsive-group-compact"]')
    expect(compact.text()).toContain('Responsable')
    expect(compact.text()).toContain('María Gómez')
    expect(compact.text()).toContain(formatMoney(1250000, 'COP'))
    expect(compact.text()).not.toContain('Interno')
  })

  it('promotes declared columns independently at portrait and landscape widths', () => {
    const wrapper = mountTable()
    const headers = wrapper.findAll('th')

    expect(headers[1].classes()).toContain('panel-portrait:table-cell')
    expect(headers[2].classes()).toContain('panel-portrait:hidden')
    expect(headers[2].classes()).toContain('panel-landscape:table-cell')
    expect(headers[3].classes()).toContain('panel-landscape:hidden')
    expect(headers[3].classes()).toContain('panel-desktop:table-cell')
  })

  it('uses the primary column as the predictable home for grouped details', () => {
    const wrapper = mountTable()
    const row = wrapper.get('[data-testid="accounting-row-1"]')

    expect(row.findAll('[data-testid="responsive-group-compact"]')).toHaveLength(1)
    expect(row.findAll('[data-testid="responsive-group-portrait"]')).toHaveLength(1)
    expect(row.findAll('[data-testid="responsive-group-landscape"]')).toHaveLength(0)
  })

  it('removes the scroll floor below landscape only after a policy is declared', () => {
    const priority = mountTable().get('table')
    const legacy = mountTable({
      columns: [{ key: 'name', label: 'Proyecto' }],
    }).get('table')

    expect(priority.classes()).toContain('base-responsive-table--priority')
    expect(priority.element.style.getPropertyValue('--table-min-width')).toMatch(/rem$/)
    expect(priority.element.style.minWidth).toBe('')
    expect(legacy.classes()).not.toContain('base-responsive-table--priority')
    expect(legacy.element.style.minWidth).toMatch(/rem$/)
  })

  it('warns when a mixed declaration would make an automatic choice', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {})

    mountTable({
      columns: [columns[0], { key: 'owner', label: 'Responsable' }],
    })

    expect(warn).toHaveBeenCalledWith(expect.stringContaining('Missing: owner'))
    warn.mockRestore()
  })

  it('uses a consumer test id prefix', () => {
    const wrapper = mountTable({ testIdPrefix: 'diagnostic' })

    expect(wrapper.find('[data-testid="diagnostic-row-1"]').exists()).toBe(true)
  })

  it('omits legacy actions for custom action menus', () => {
    const wrapper = mountTable({ showActions: true, showDefaultActions: false })

    expect(wrapper.find('[aria-label="Editar"]').exists()).toBe(false)
    expect(wrapper.find('[aria-label="Eliminar"]').exists()).toBe(false)
  })

  it('uses the selected background and consumer row classes together', () => {
    const wrapper = mountTable({
      selectable: true,
      selected: [1],
      rowClass: () => 'opacity-60',
    })
    const row = wrapper.get('[data-testid="accounting-row-1"]')

    expect(row.classes()).toContain('bg-primary-soft')
    expect(row.classes()).toContain('opacity-60')
  })

  it('emits row gestures only when interactive rows are enabled', async () => {
    const wrapper = mountTable({ interactiveRows: true })
    const row = wrapper.get('[data-testid="accounting-row-1"]')

    await row.trigger('click')
    await row.trigger('auxclick', { button: 1 })

    expect(wrapper.emitted('row-click')?.[0]?.[0]).toEqual(rows[0])
    expect(wrapper.emitted('row-auxclick')?.[0]?.[0]).toEqual(rows[0])
  })

  it('uses a business label for selectable rows when declared', () => {
    const wrapper = mountTable({
      selectable: true,
      selectionLabel: (row) => `Seleccionar ${row.name}`,
    })

    expect(wrapper.get('[data-testid="accounting-select-1"]').attributes('aria-label'))
      .toBe('Seleccionar Proyecto Aurora')
  })
})

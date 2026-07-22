import { mount } from '@vue/test-utils'

import ViewMapLegend from '../../components/views/ViewMapLegend.vue'
import {
  viewTypeOptions,
  viewAudienceOptions,
} from '../../constants/viewMapFilterOptions'

describe('ViewMapLegend', () => {
  it('renders the collapsible legend summary', () => {
    const wrapper = mount(ViewMapLegend)
    expect(wrapper.find('summary').text()).toContain('Leyenda de colores')
  })

  it('renders one badge per view-type option', () => {
    const wrapper = mount(ViewMapLegend)
    const labels = viewTypeOptions.map((option) => option.label)
    const text = wrapper.text()
    expect(labels.every((label) => text.includes(label))).toBe(true)
  })

  it('renders one badge per audience option', () => {
    const wrapper = mount(ViewMapLegend)
    const total = viewTypeOptions.length + viewAudienceOptions.length
    expect(wrapper.findAll('span.inline-flex, [class*="badge"], details .flex-wrap > *').length)
      .toBeGreaterThanOrEqual(total)
  })
})

import { mount } from '@vue/test-utils'
import BaseIndicatorCard from '~/components/base/BaseIndicatorCard.vue'

const BaseActionIconStub = {
  template: '<span aria-hidden="true" />',
}

const BaseTooltipStub = {
  props: {
    floating: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    return { tooltipId: 'indicator-tooltip' }
  },
  template: `
    <div>
      <slot name="trigger" :tooltip-id="tooltipId" />
      <slot />
    </div>
  `,
}

function mountCard(props = {}, slots = {}) {
  return mount(BaseIndicatorCard, {
    props: { label: 'Total líquido', value: '$1.500.000 COP', ...props },
    slots,
    global: {
      stubs: {
        BaseActionIcon: BaseActionIconStub,
        BaseTooltip: BaseTooltipStub,
      },
    },
  })
}

describe('BaseIndicatorCard', () => {
  it('renders the indicator label and its exact value', () => {
    // Falla si la tarjeta deja de mostrar la pregunta o el resultado del indicador.
    const wrapper = mountCard()

    expect(wrapper.get('[data-testid="indicator-label"]').text()).toBe('Total líquido')
    expect(wrapper.get('[data-testid="accounting-stat-value"]').text()).toBe('$1.500.000 COP')
  })

  it('renders the supplied support copy in the reserved support row', () => {
    // Falla si una línea de apoyo deja de llegar a la fila reservada.
    const wrapper = mountCard({ support: '75% recibido' })

    expect(wrapper.get('[data-testid="indicator-support"]').text()).toBe('75% recibido')
    expect(wrapper.get('[data-testid="indicator-support"]').attributes('aria-hidden'))
      .toBeUndefined()
  })

  it('keeps an empty, hidden support row when no support copy exists', () => {
    // Falla si las tarjetas sin apoyo pierden la fila que mantiene la altura pareja.
    const wrapper = mountCard()
    const support = wrapper.get('[data-testid="indicator-support"]')

    expect(support.element.textContent).toBe('\u00a0')
    expect(support.attributes('aria-hidden')).toBe('true')
  })

  it('removes the empty support row from the compact horizontal layout', () => {
    // Falla si la variante corta vuelve a reservar altura para contenido inexistente.
    const wrapper = mountCard({ layout: 'compact-horizontal' })

    expect(wrapper.get('article').attributes('data-layout')).toBe('compact-horizontal')
    expect(wrapper.get('article').classes()).toContain('h-20')
    expect(wrapper.find('[data-testid="indicator-support"]').exists()).toBe(false)
  })

  it('keeps compact help outside the filtering button', async () => {
    // Falla si la ayuda vuelve a superponerse o queda anidada dentro de la acción principal.
    const wrapper = mountCard(
      {
        layout: 'compact-horizontal',
        action: 'filter',
        actionLabel: 'Filtrar por estado activo',
        helpLabel: 'Ayuda sobre Activo',
        helpTestId: 'compact-state-help',
      },
      { help: '<p>El proyecto está operando.</p>' },
    )
    const action = wrapper.get('[aria-label="Filtrar por estado activo"]')
    const help = wrapper.get('[data-testid="compact-state-help"]')

    expect(wrapper.findComponent(BaseTooltipStub).props('floating')).toBe(false)
    expect(action.element.contains(help.element)).toBe(false)

    await help.trigger('click')

    expect(wrapper.emitted('activate')).toBeUndefined()
  })

  it('exposes an accessible action and emits activate when it is selected', async () => {
    // Falla si una tarjeta filtrable deja de ser accionable o de avisar al listado.
    const wrapper = mountCard({ action: 'filter', actionLabel: 'Filtrar ingresos líquidos' })
    const action = wrapper.get('[aria-label="Filtrar ingresos líquidos"]')

    expect(action.element.tagName).toBe('BUTTON')
    expect(action.attributes('type')).toBe('button')

    await action.trigger('click')

    expect(wrapper.emitted('activate')).toEqual([[]])
  })

  it('keeps help independently selectable without activating the card', async () => {
    // Falla si la ayuda queda fusionada con la acción principal y cambia el listado al consultarla.
    const wrapper = mountCard(
      {
        action: 'list',
        actionLabel: 'Ver detalle',
        helpLabel: 'Ayuda sobre el indicador',
        helpTestId: 'indicator-custom-help',
      },
      { help: '<p>Explicación concreta</p>' },
    )
    const help = wrapper.get('[data-testid="indicator-custom-help"]')

    expect(wrapper.findComponent(BaseTooltipStub).props('floating')).toBe(true)
    expect(help.attributes('aria-label')).toBe('Ayuda sobre el indicador')
    expect(wrapper.get('[data-testid="indicator-custom-help-content"]').text())
      .toBe('Explicación concreta')

    await help.trigger('click')

    expect(wrapper.emitted('activate')).toBeUndefined()
  })
})

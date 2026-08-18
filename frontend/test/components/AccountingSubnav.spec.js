import { mount } from '@vue/test-utils'

import AccountingSubnav from '../../components/accounting/AccountingSubnav.vue'

global.useLocalePath = jest.fn(() => (path) => path)

// El desplegable de móvil navega con el router en vez de con un <a>, así que
// hace falta la misma clase de stub que ya lleva useLocalePath.
const push = jest.fn()
global.useRouter = jest.fn(() => ({ push }))

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a :href="to" v-bind="$attrs"><slot /></a>', props: ['to'] },
  },
}

beforeEach(() => {
  push.mockClear()
})

describe('AccountingSubnav', () => {
  it('renders one link per accounting section', () => {
    const wrapper = mount(AccountingSubnav, { global: GLOBAL })
    expect(wrapper.findAll('a')).toHaveLength(12)
    expect(wrapper.text()).toContain('Bolsillo')
    expect(wrapper.text()).toContain('Extractos')
  })

  it('marks the active section with aria-current', () => {
    const wrapper = mount(AccountingSubnav, {
      props: { active: 'incomes' },
      global: GLOBAL,
    })
    const active = wrapper.find('[data-testid="accounting-subnav-incomes"]')
    expect(active.attributes('aria-current')).toBe('page')
    expect(active.classes()).toContain('bg-primary')
  })

  it('leaves inactive sections without aria-current', () => {
    const wrapper = mount(AccountingSubnav, {
      props: { active: 'incomes' },
      global: GLOBAL,
    })
    const inactive = wrapper.find('[data-testid="accounting-subnav-pocket"]')
    expect(inactive.attributes('aria-current')).toBeUndefined()
    expect(inactive.classes()).toContain('bg-surface-raised')
  })

  it('points each link at its accounting route', () => {
    const wrapper = mount(AccountingSubnav, { global: GLOBAL })
    expect(
      wrapper.find('[data-testid="accounting-subnav-statements"]').attributes('href'),
    ).toBe('/panel/accounting/statements')
  })

  it('defaults the active section to the summary', () => {
    const wrapper = mount(AccountingSubnav, { global: GLOBAL })
    expect(
      wrapper.find('[data-testid="accounting-subnav-index"]').attributes('aria-current'),
    ).toBe('page')
  })

  describe('selector de móvil', () => {
    it('ofrece las mismas doce secciones y en el mismo orden que las pastillas', () => {
      const wrapper = mount(AccountingSubnav, { global: GLOBAL })

      const options = wrapper.findAll('[data-testid="accounting-subnav-select"] option')
      expect(options).toHaveLength(12)
      // Dos ordenamientos distintos obligarían a aprender dos mapas de lo mismo.
      expect(options.map((option) => option.text())).toEqual(
        wrapper.findAll('nav a').map((link) => link.text()),
      )
    })

    it('marca la sección activa como seleccionada al abrirse', () => {
      const wrapper = mount(AccountingSubnav, {
        props: { active: 'statements' },
        global: GLOBAL,
      })

      expect(
        wrapper.get('[data-testid="accounting-subnav-select"]').element.value,
      ).toBe('statements')
    })

    it('navega a la ruta de la sección elegida', async () => {
      const wrapper = mount(AccountingSubnav, {
        props: { active: 'index' },
        global: GLOBAL,
      })

      await wrapper.get('[data-testid="accounting-subnav-select"]').setValue('pocket')

      expect(push).toHaveBeenCalledWith('/panel/accounting/pocket')
    })

    it('se distingue del selector de filtros por peso visual y por nombre', () => {
      const wrapper = mount(AccountingSubnav, { global: GLOBAL })

      // Los dos selectores quedan contiguos en nueve de las doce vistas: el de
      // navegación va sólido y el de filtros neutro.
      const select = wrapper.get('[data-testid="accounting-subnav-select"]')
      expect(select.classes()).toContain('bg-primary')
      expect(select.attributes('aria-label')).toBe('Sección de contabilidad')
    })
  })
})

import { flushPromises, mount } from '@vue/test-utils'

import BaseAlert from '../../components/base/BaseAlert.vue'
import BaseBadge from '../../components/base/BaseBadge.vue'
import BaseSegmented from '../../components/base/BaseSegmented.vue'
import FinancingProgramView from '../../components/Financing/ProgramView.vue'


global.useI18n = jest.fn(() => ({
  t: (key, params = {}) => `${key}${params.count ? `:${params.count}` : ''}${params.title ? `:${params.title}` : ''}`,
}))

const program = {
  hero: {
    eyebrow: 'Financiación de largo plazo',
    title: 'Construimos hoy',
    subtitle: 'Compartimos el riesgo del producto.',
    trust_note: 'Una oportunidad se convierte en producto.',
  },
  eligibility: {
    badge: 'Aprobación previa',
    title: 'Sujeto a evaluación',
    summary: 'La propuesta define el saldo aprobado.',
  },
  options: [
    {
      id: 'five-year', name: 'Alianza a 5 años', badge: 'Recomendada',
      summary: 'Incluye continuidad y capacidad mensual.', exclusivity_years: 5,
      recommended: true, hour_package_included: true, financing_cycles: 2,
      highlights: ['Hasta dos ciclos de financiación'],
    },
    {
      id: 'three-year', name: 'Alianza a 3 años', badge: 'Alternativa',
      summary: 'Conserva financiación sin paquete.', exclusivity_years: 3,
      recommended: false, hour_package_included: false, financing_cycles: 1,
      highlights: ['Requerimientos cotizados aparte'],
    },
  ],
  conditions: [
    {
      id: 'financing', number: '01', icon: '↗', title: '12 meses',
      summary: 'Financia el saldo aprobado.', commercial_reason: 'Libera capital inicial.',
      highlights: ['Interés ordinario 0%'],
    },
    {
      id: 'exclusivity', number: '02', icon: '◇', title: 'Exclusividad',
      summary: 'Una sola casa desarrolladora.', commercial_reason: 'Protege el contexto.',
      highlights: ['Custodia segura'],
    },
    {
      id: 'calculator', number: '03', icon: '◎', title: 'Calculadora',
      summary: 'Anticipa esfuerzo.', commercial_reason: 'Hace visible el rango.',
      highlights: ['Resultado orientativo'],
    },
    {
      id: 'hour-package', number: '04', icon: '◷', title: '60 horas',
      summary: 'Capacidad mensual.', commercial_reason: 'Mantiene la evolución.',
      highlights: ['No acumula horas'],
    },
    {
      id: 'payment-discipline', number: '05', icon: '%', title: 'Pagos claros',
      summary: 'Las cuotas vencen en los primeros cinco días.', commercial_reason: 'Cubre el riesgo.',
      highlights: ['Cada mora aumenta 1% el Hosting vigente'],
    },
  ],
  calculator: {
    eyebrow: 'Transparencia',
    title: 'De una necesidad a un rango',
    summary: 'Recibe lenguaje natural.',
    input: { title: 'Qué se ingresa', items: ['Descripción del cambio'] },
    output: { title: 'Qué se obtiene', items: ['Esfuerzo, tiempo y precio'] },
    disclaimer: 'La cotización formal prevalece.',
  },
  package: {
    name: 'Paquete Pro', hours: 60, included_label: 'Incluido',
    title: 'Capacidad mensual', summary: 'Para requerimientos acotados.',
    renewal_label: 'Se renueva cada mes', rollover_label: 'No acumula horas',
    availability_label: 'Desde producción',
  },
  legal_terms: [
    {
      id: 'approval', title: 'Saldo aprobado', summary: 'Requiere evaluación.',
      items: ['Sólo cubre fases aprobadas.'],
    },
  ],
  cta: {
    eyebrow: 'Conversemos', title: 'Solicita una evaluación',
    body: 'Cuéntanos sobre el producto.', button: 'Hablar por WhatsApp',
    whatsapp_url: 'https://wa.me/573238122373?text=financing',
  },
  disclaimer: 'Información comercial de referencia.',
}

function mountProgram(props = {}) {
  return mount(FinancingProgramView, {
    props: {
      program,
      downloadUrl: '/api/financing/public/pdf/?lang=es',
      language: 'es',
      ...props,
    },
    global: {
      components: { BaseAlert, BaseBadge, BaseSegmented },
      stubs: {
        NuxtLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

describe('FinancingProgramView', () => {
  beforeEach(() => {
    window.localStorage.clear()
    global.fetch = jest.fn()
    URL.createObjectURL = jest.fn(() => 'blob:financing')
    URL.revokeObjectURL = jest.fn()
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    })
    Object.defineProperty(navigator, 'share', {
      configurable: true,
      value: undefined,
    })
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders both partnership options', () => {
    const wrapper = mountProgram()

    expect(wrapper.get('[data-testid="financing-option-five-year"]').text()).toContain('Alianza a 5 años')
    expect(wrapper.get('[data-testid="financing-option-three-year"]').text()).toContain('Alianza a 3 años')
  })

  it('renders the calculator input and output', () => {
    const wrapper = mountProgram()

    const calculator = wrapper.get('[data-testid="financing-calculator-input-output"]')
    expect(calculator.text()).toContain('Descripción del cambio')
    expect(calculator.text()).toContain('Esfuerzo, tiempo y precio')
  })

  it('renders the late-payment Hosting consequence', () => {
    const wrapper = mountProgram()

    expect(wrapper.get('[data-testid="financing-condition-payment-discipline"]').text())
      .toContain('Cada mora aumenta 1% el Hosting vigente')
  })

  it('renders the second-cycle benefit in the recommended option', () => {
    const wrapper = mountProgram()

    expect(wrapper.get('[data-testid="financing-option-five-year"]').text())
      .toContain('Hasta dos ciclos de financiación')
  })

  it('reveals an agreement rule from its accordion', async () => {
    const wrapper = mountProgram()
    const trigger = wrapper.get('[data-testid="financing-term-trigger-approval"]')

    await trigger.trigger('click')

    expect(trigger.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('[data-testid="financing-term-approval"]').text()).toContain('Sólo cubre fases aprobadas.')
  })

  it('emits the requested language', async () => {
    const wrapper = mountProgram()

    await wrapper.get('[data-testid="financing-language-en"]').trigger('click')

    expect(wrapper.emitted('change-language')).toEqual([['en']])
  })

  it('shows a visible error when the PDF request fails', async () => {
    global.fetch.mockRejectedValue(new Error('offline'))
    const wrapper = mountProgram()

    await wrapper.get('[data-testid="financing-download-pdf"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('financing.pdfError')
  })

  it('copies the current URL when native sharing is unavailable', async () => {
    window.history.replaceState({}, '', '/es-co/financing')
    const wrapper = mountProgram()

    await wrapper.get('[data-testid="financing-share"]').trigger('click')
    await flushPromises()

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('http://localhost/es-co/financing')
  })

  it('shows a visible error when clipboard sharing fails', async () => {
    navigator.clipboard.writeText.mockRejectedValue(new Error('blocked'))
    const wrapper = mountProgram()

    await wrapper.get('[data-testid="financing-share"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('financing.shareFailed')
  })
})

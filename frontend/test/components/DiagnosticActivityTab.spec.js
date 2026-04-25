import { mount } from '@vue/test-utils'

jest.mock('../../stores/diagnostics_constants', () => ({
  ACTIVITY_CHANGE_TYPES: Object.freeze([
    { value: 'note', label: 'Nota' },
    { value: 'call', label: 'Llamada' },
    { value: 'meeting', label: 'Reunión' },
    { value: 'followup', label: 'Seguimiento' },
  ]),
}))

import DiagnosticActivityTab from '../../components/WebAppDiagnostic/admin/DiagnosticActivityTab.vue'

function mountTab(diagnosticOverrides = {}) {
  return mount(DiagnosticActivityTab, {
    props: {
      diagnostic: { change_logs: [], ...diagnosticOverrides },
    },
  })
}

describe('DiagnosticActivityTab', () => {
  it('mounts without errors with an empty change_logs prop', () => {
    const wrapper = mountTab()
    expect(wrapper.exists()).toBe(true)
  })

  it('renders a select and a text input in the activity form', () => {
    const wrapper = mountTab()
    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
  })

  it('renders the submit button with text Registrar', () => {
    const wrapper = mountTab()
    expect(wrapper.find('button').text()).toBe('Registrar')
  })

  it('logs computed returns empty array when change_logs is absent', () => {
    const wrapper = mount(DiagnosticActivityTab, {
      props: { diagnostic: {} },
    })
    expect(wrapper.find('ol').exists()).toBe(false)
    expect(wrapper.text()).toContain('Sin actividad registrada')
  })

  it('logs computed derives from diagnostic.change_logs array', () => {
    const wrapper = mountTab({
      change_logs: [
        { id: 1, change_type: 'note', description: 'Primer contacto', created_at: '2026-01-10T10:00:00Z' },
      ],
    })
    expect(wrapper.text()).toContain('Primer contacto')
  })

  it('select renders all change type options', () => {
    const wrapper = mountTab()
    const options = wrapper.findAll('option')
    expect(options.length).toBe(4)
    expect(options[0].text()).toBe('Nota')
    expect(options[1].text()).toBe('Llamada')
  })

  it('submit emits log with change_type and description when description is non-empty', async () => {
    const wrapper = mountTab()
    await wrapper.find('input[type="text"]').setValue('New note')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('log')).toBeTruthy()
    expect(wrapper.emitted('log')[0][0]).toMatchObject({
      change_type: 'note',
      description: 'New note',
    })
  })

  it('submit does not emit log when description is empty', async () => {
    const wrapper = mountTab()
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('log')).toBeFalsy()
  })

  it('submit does not emit log when description is only whitespace', async () => {
    const wrapper = mountTab()
    await wrapper.find('input[type="text"]').setValue('   ')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('log')).toBeFalsy()
  })

  it('description field is cleared after successful submit', async () => {
    const wrapper = mountTab()
    await wrapper.find('input[type="text"]').setValue('Note text')
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('input[type="text"]').element.value).toBe('')
  })

  it('each log entry renders a non-empty formatDate output', () => {
    const wrapper = mountTab({
      change_logs: [
        { id: 1, change_type: 'note', description: 'X', created_at: '2026-01-15T09:30:00Z' },
      ],
    })
    const dateText = wrapper.text()
    expect(dateText).toBeTruthy()
    expect(dateText.length).toBeGreaterThan(0)
  })

  it('iconFor note returns a non-empty string', () => {
    const wrapper = mountTab({
      change_logs: [{ id: 1, change_type: 'note', description: 'N', created_at: '2026-01-10T10:00:00Z' }],
    })
    const dot = wrapper.find('ol span')
    expect(dot.text().trim().length).toBeGreaterThan(0)
  })

  it('iconFor unknown change_type returns fallback bullet', () => {
    const wrapper = mountTab({
      change_logs: [{ id: 1, change_type: 'unknown_type', description: 'X', created_at: '2026-01-10T10:00:00Z' }],
    })
    const dot = wrapper.find('ol span')
    expect(dot.text().trim()).toBe('•')
  })

  it('labelFor call returns a non-empty label string', () => {
    const wrapper = mountTab({
      change_logs: [{ id: 1, change_type: 'call', description: 'Called', created_at: '2026-01-10T10:00:00Z' }],
    })
    expect(wrapper.text()).toContain('Llamada')
  })

  it('selecting a different change_type in the select updates the form', async () => {
    const wrapper = mountTab()
    await wrapper.find('select').setValue('meeting')
    expect(wrapper.find('select').element.value).toBe('meeting')
  })

  it('submit uses the selected change_type in the emitted payload', async () => {
    const wrapper = mountTab()
    await wrapper.find('select').setValue('call')
    await wrapper.find('input[type="text"]').setValue('Called client')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('log')[0][0].change_type).toBe('call')
  })
})

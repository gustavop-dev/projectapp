import { mount } from '@vue/test-utils'

import DiagnosticPromptPanel from '../../components/WebAppDiagnostic/admin/DiagnosticPromptPanel.vue'
import {
  useDiagnosticCommercialPrompt,
  useDiagnosticTechnicalPrompt,
} from '../../composables/useDiagnosticPrompt'

jest.mock('../../composables/useDiagnosticPrompt', () => {
  const makeState = (label) => ({ label, loadSaved: jest.fn() })
  const commercial = makeState('commercial')
  const technical = makeState('technical')
  return {
    useDiagnosticCommercialPrompt: jest.fn(() => commercial),
    useDiagnosticTechnicalPrompt: jest.fn(() => technical),
  }
})

const GLOBAL = {
  stubs: {
    PromptSubTabsPanel: {
      template: '<div><slot name="commercial" /><slot name="technical" /></div>',
    },
    PromptEditor: {
      props: ['state', 'downloadFilename'],
      template: '<div class="prompt-editor-stub" :data-label="state.label" :data-filename="downloadFilename" />',
    },
  },
}

describe('DiagnosticPromptPanel', () => {
  it('renders both prompt editors with their download filenames', () => {
    const wrapper = mount(DiagnosticPromptPanel, { global: GLOBAL })
    const editors = wrapper.findAll('.prompt-editor-stub')
    expect(editors).toHaveLength(2)
    expect(editors[0].attributes('data-filename')).toBe('prompt-diagnostic-commercial.md')
    expect(editors[1].attributes('data-filename')).toBe('prompt-diagnostic-technical.md')
  })

  it('binds each editor to its own prompt state', () => {
    const wrapper = mount(DiagnosticPromptPanel, { global: GLOBAL })
    const labels = wrapper.findAll('.prompt-editor-stub').map((e) => e.attributes('data-label'))
    expect(labels).toEqual(['commercial', 'technical'])
  })

  it('loads the saved prompts on mount', () => {
    mount(DiagnosticPromptPanel, { global: GLOBAL })
    expect(useDiagnosticCommercialPrompt().loadSaved).toHaveBeenCalled()
    expect(useDiagnosticTechnicalPrompt().loadSaved).toHaveBeenCalled()
  })
})

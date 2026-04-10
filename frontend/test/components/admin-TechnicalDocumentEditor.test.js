import { mount } from '@vue/test-utils';

jest.mock('../../utils/technicalModuleStub', () => ({
  createGenericTechnicalEpicStub: jest.fn((id, label) => ({
    epicKey: `E-${id}`,
    title: label,
    description: '',
    linked_module_ids: [id],
    requirements: [],
  })),
}));

import TechnicalDocumentEditor from '../../components/BusinessProposal/admin/TechnicalDocumentEditor.vue';

const baseSection = {
  id: 1,
  title: 'Technical Spec',
  is_wide_panel: false,
  content_json: {
    purpose: 'Sistema de gestión de propuestas',
    stack: [{ layer: 'Frontend', technology: 'Vue 3', rationale: 'Reactivity' }],
    epics: [],
  },
};

function mountTechnicalDocumentEditor(props = {}) {
  return mount(TechnicalDocumentEditor, {
    props: {
      section: baseSection,
      moduleLinkOptions: [],
      ...props,
    },
  });
}

describe('TechnicalDocumentEditor', () => {
  it('renders the editor wrapper', () => {
    const wrapper = mountTechnicalDocumentEditor();

    expect(wrapper.find('[data-testid="technical-document-editor"]').exists()).toBe(true);
  });

  it('renders the purpose textarea with prefilled value', () => {
    const wrapper = mountTechnicalDocumentEditor();

    const textarea = wrapper.find('textarea');
    expect(textarea.exists()).toBe(true);
    expect(textarea.element.value).toBe('Sistema de gestión de propuestas');
  });

  it('renders section headings for key sections', () => {
    const wrapper = mountTechnicalDocumentEditor();

    expect(wrapper.text()).toContain('Propósito');
    expect(wrapper.text()).toContain('Stack tecnológico');
  });

  it('shows module stub selector when moduleLinkOptions are provided', () => {
    const wrapper = mountTechnicalDocumentEditor({
      moduleLinkOptions: [{ id: 'mod-1', label: 'E-commerce' }],
    });

    expect(wrapper.text()).toContain('Plantilla genérica por módulo opcional');
  });

  it('does not show stub selector when moduleLinkOptions is empty', () => {
    const wrapper = mountTechnicalDocumentEditor({ moduleLinkOptions: [] });

    expect(wrapper.text()).not.toContain('Plantilla genérica por módulo opcional');
  });
});

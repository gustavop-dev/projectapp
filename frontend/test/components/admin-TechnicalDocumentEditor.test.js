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

    expect(wrapper.text()).toContain('Plantilla genérica por módulo comercial');
  });

  it('does not show stub selector when moduleLinkOptions is empty', () => {
    const wrapper = mountTechnicalDocumentEditor({ moduleLinkOptions: [] });

    expect(wrapper.text()).not.toContain('Plantilla genérica por módulo comercial');
  });

  it('emits canonical linked_module_ids when the source content uses legacy ids', async () => {
    const wrapper = mountTechnicalDocumentEditor({
      section: {
        ...baseSection,
        content_json: {
          ...baseSection.content_json,
          epics: [
            {
              epicKey: 'legacy-epic',
              title: 'Legacy Epic',
              linked_module_ids: ['views'],
              requirements: [
                { title: 'Legacy Req', linked_module_ids: ['pwa_module'] },
              ],
            },
          ],
        },
      },
      moduleLinkOptions: [
        { id: 'group-views', label: 'Vistas', aliases: ['group-views', 'views'] },
        { id: 'module-pwa_module', label: 'PWA', aliases: ['module-pwa_module', 'pwa_module'] },
      ],
    });

    const saveButton = wrapper.findAll('button').find((button) =>
      button.text().includes('Guardar detalle técnico'),
    );
    expect(saveButton).toBeTruthy();
    await saveButton.trigger('click');

    const emitted = wrapper.emitted('save');
    expect(emitted).toHaveLength(1);
    const payload = emitted[0][0].payload.content_json;
    expect(payload.epics[0].linked_module_ids).toEqual(['group-views']);
    expect(payload.epics[0].requirements[0].linked_module_ids).toEqual(['module-pwa_module']);
  });
});

// ── Dynamic row additions ────────────────────────────────────────────────────

describe('TechnicalDocumentEditor dynamic rows', () => {
  // ── Stack rows ──────────────────────────────────────────────────────────

  it('adds a stack row when the + Fila button is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor();

    const filaBtn = wrapper.findAll('button').find(b => b.text() === '+ Fila');
    await filaBtn.trigger('click');

    // 1 pre-existing row + 1 new empty row
    expect(wrapper.vm.doc.stack).toHaveLength(2);
    expect(wrapper.vm.doc.stack[1]).toEqual({ layer: '', technology: '', rationale: '' });
  });

  it('removes a stack row when its delete button is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor();

    const deleteBtn = wrapper.findAll('button').find(b => b.text() === '✕');
    await deleteBtn.trigger('click');

    expect(wrapper.vm.doc.stack).toHaveLength(0);
  });

  // ── Epics ───────────────────────────────────────────────────────────────

  it('adds a new epic when the + Módulo button is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor();

    const addEpicBtn = wrapper.findAll('button').find(b => b.text() === '+ Módulo');
    await addEpicBtn.trigger('click');

    expect(wrapper.vm.doc.epics).toHaveLength(1);
  });

  it('removes an epic when the Eliminar módulo button is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor({
      section: {
        ...baseSection,
        content_json: {
          ...baseSection.content_json,
          epics: [{ epicKey: 'mod-a', title: 'Module A', description: '', linked_module_ids: [], requirements: [] }],
        },
      },
    });

    const deleteBtn = wrapper.findAll('button').find(b => b.text() === 'Eliminar módulo');
    await deleteBtn.trigger('click');

    expect(wrapper.vm.doc.epics).toHaveLength(0);
  });

  // ── Requirements ────────────────────────────────────────────────────────

  it('adds a requirement to an epic when + Requerimiento is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor({
      section: {
        ...baseSection,
        content_json: {
          ...baseSection.content_json,
          epics: [{ epicKey: 'mod-a', title: 'Module A', description: '', linked_module_ids: [], requirements: [] }],
        },
      },
    });

    const reqBtn = wrapper.findAll('button').find(b => b.text() === '+ Requerimiento');
    await reqBtn.trigger('click');

    expect(wrapper.vm.doc.epics[0].requirements).toHaveLength(1);
  });

  it('removes a requirement from an epic when Quitar requerimiento is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor({
      section: {
        ...baseSection,
        content_json: {
          ...baseSection.content_json,
          epics: [
            {
              epicKey: 'mod-a',
              title: 'Module A',
              description: '',
              linked_module_ids: [],
              requirements: [
                { flowKey: 'req-1', title: 'Login', description: '', configuration: '', usageFlow: '', priority: 'high', linked_module_ids: [] },
              ],
            },
          ],
        },
      },
    });

    const quitarBtn = wrapper.findAll('button').find(b => b.text() === 'Quitar requerimiento');
    await quitarBtn.trigger('click');

    expect(wrapper.vm.doc.epics[0].requirements).toHaveLength(0);
  });

  // ── Save and validation ─────────────────────────────────────────────────

  it('emits save with serialized content_json when the save button is clicked', async () => {
    const wrapper = mountTechnicalDocumentEditor();

    const saveBtn = wrapper.findAll('button').find(b => b.text().includes('Guardar detalle técnico'));
    await saveBtn.trigger('click');

    const emitted = wrapper.emitted('save');
    expect(emitted).toHaveLength(1);
    expect(emitted[0][0]).toMatchObject({ sectionId: baseSection.id });
    expect(emitted[0][0].payload.content_json).toBeDefined();
  });

  it('shows a validation error when two epics share the same epicKey', async () => {
    const wrapper = mountTechnicalDocumentEditor({
      section: {
        ...baseSection,
        content_json: {
          ...baseSection.content_json,
          epics: [
            { epicKey: 'dup-key', title: 'First', description: '', linked_module_ids: [], requirements: [] },
            { epicKey: 'dup-key', title: 'Second', description: '', linked_module_ids: [], requirements: [] },
          ],
        },
      },
    });

    const saveBtn = wrapper.findAll('button').find(b => b.text().includes('Guardar detalle técnico'));
    await saveBtn.trigger('click');

    expect(wrapper.text()).toContain('epicKey duplicado');
  });
});

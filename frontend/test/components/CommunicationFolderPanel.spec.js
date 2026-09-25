const mockStore = {
  fetchFolders: jest.fn(),
  saveFolder: jest.fn(),
  deleteFolder: jest.fn(),
};
const mockNotify = { success: jest.fn() };

jest.mock('~/stores/communications', () => ({
  useCommunicationsStore: () => mockStore,
}));
jest.mock('~/composables/usePanelNotify', () => ({
  usePanelNotify: () => mockNotify,
}));

import { flushPromises, mount } from '@vue/test-utils';
import CommunicationFolderPanel from '~/components/communications/CommunicationFolderPanel.vue';

global.useI18n = () => ({
  t: (key, values = {}) => ({
    'communicationFiling.folders': 'Carpetas',
    'communicationFiling.all': 'Todos',
    'communicationFiling.unfiled': 'Sin carpeta',
    'communicationFiling.create': 'Nueva carpeta',
    'communicationFiling.edit': 'Editar carpeta',
    'communicationFiling.name': 'Nombre',
    'communicationFiling.parent': 'Carpeta superior',
    'communicationFiling.root': 'Raíz',
    'communicationFiling.save': 'Guardar',
    'communicationFiling.cancel': 'Cancelar',
    'communicationFiling.delete': 'Eliminar carpeta',
    'communicationFiling.chooseContext': 'Selecciona un cliente o proyecto para organizar sus carpetas.',
    'communicationFiling.empty': 'Todavía no hay carpetas.',
    'communicationFiling.folderSaved': 'Carpeta guardada',
    'communicationFiling.expand': `Expandir ${values.name}`,
    'communicationFiling.collapse': `Plegar ${values.name}`,
  }[key] || key),
});

const BaseButtonStub = {
  emits: ['click'],
  template: '<button v-bind="$attrs" @click="$emit(\'click\', $event)"><slot /></button>',
};
const BaseActionButtonStub = {
  props: ['label'],
  emits: ['click'],
  template: '<button v-bind="$attrs" :aria-label="label" @click="$emit(\'click\', $event)">{{ label }}</button>',
};
const BaseModalStub = {
  props: ['modelValue'],
  template: '<div v-if="modelValue" role="dialog"><slot /></div>',
};
const BaseInputStub = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<input v-bind="$attrs" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)">',
};
const BaseSelectStub = {
  props: ['modelValue', 'options'],
  emits: ['update:modelValue'],
  template: '<select v-bind="$attrs" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option></select>',
};

const folders = () => [
  { id: 1, name: 'Clientes', parent: null, client: 7, project: 3 },
  { id: 2, name: 'Seguimiento', parent: 1, client: 7, project: 3 },
  { id: 3, name: 'Legal', parent: null, client: 7, project: 3 },
];

function mountPanel(props = {}) {
  return mount(CommunicationFolderPanel, {
    props: { clientId: 7, projectId: 3, ...props },
    global: {
      stubs: {
        BaseActionButton: BaseActionButtonStub,
        BaseActionIcon: true,
        BaseAlert: { template: '<p role="alert"><slot /></p>' },
        BaseButton: BaseButtonStub,
        BaseFormField: { template: '<label><slot /></label>' },
        BaseInput: BaseInputStub,
        BaseModal: BaseModalStub,
        BaseModalActions: { template: '<div><slot /></div>' },
        BaseSelect: BaseSelectStub,
      },
    },
  });
}

describe('CommunicationFolderPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStore.fetchFolders.mockResolvedValue({ success: true, data: folders() });
    mockStore.saveFolder.mockResolvedValue({ success: true, data: folders()[0] });
  });

  it('does not offer folder creation without a client context', async () => {
    const wrapper = mountPanel({ clientId: null, projectId: null });
    await flushPromises();

    expect(wrapper.text()).toContain('Selecciona un cliente o proyecto para organizar sus carpetas.');
    expect(wrapper.findAll('[aria-label="Nueva carpeta"]')).toHaveLength(0);
    expect(mockStore.fetchFolders).not.toHaveBeenCalled();
  });

  // Falla si navegar un proyecto deja fuera las carpetas del cliente o muestra otro proyecto.
  it('keeps client folders and the selected project folders in the tree', async () => {
    mockStore.fetchFolders.mockResolvedValue({
      success: true,
      data: [
        { id: 11, name: 'Cliente', parent: null, client: 7, project: null },
        { id: 12, name: 'Proyecto 19', parent: null, client: 7, project: 19 },
        { id: 13, name: 'Proyecto 20', parent: null, client: 7, project: 20 },
      ],
    });
    const wrapper = mountPanel({ projectId: 19 });
    await flushPromises();

    expect(mockStore.fetchFolders).toHaveBeenCalledWith({ client: 7 });
    expect(wrapper.get('[data-testid="communication-folder-11"]').text()).toBe('Cliente');
    expect(wrapper.get('[data-testid="communication-folder-12"]').text()).toBe('Proyecto 19');
    expect(wrapper.findAll('[data-testid="communication-folder-13"]')).toHaveLength(0);
  });

  // Falla si crear desde una carpeta deja de usarla como superior y pierde el contexto.
  it('creates a child folder using the selected folder as parent', async () => {
    const wrapper = mountPanel({ selected: '2' });
    await flushPromises();

    await wrapper.get('[aria-label="Nueva carpeta"]').trigger('click');
    await wrapper.get('[data-testid="communication-folder-name"]').setValue('Respuestas');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mockStore.saveFolder).toHaveBeenCalledWith(null, {
      name: 'Respuestas', parent: 2, client: 7, project: 3,
    });
  });

  // Falla si una subcarpeta de cliente hereda por error el proyecto que se está viendo.
  it('keeps a client folder child outside the current project scope', async () => {
    mockStore.fetchFolders.mockResolvedValue({
      success: true,
      data: [{ id: 11, name: 'Cliente', parent: null, client: 7, project: null }],
    });
    const wrapper = mountPanel({ projectId: 19, selected: '11' });
    await flushPromises();

    await wrapper.get('[aria-label="Nueva carpeta"]').trigger('click');
    await wrapper.get('[data-testid="communication-folder-name"]').setValue('Seguimiento del cliente');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mockStore.saveFolder).toHaveBeenCalledWith(null, {
      name: 'Seguimiento del cliente', parent: 11, client: 7, project: null,
    });
  });

  // Falla si el selector vuelve a permitir que una carpeta sea hija de sí misma o de un descendiente.
  it('excludes the edited folder and its descendant from parent choices', async () => {
    const wrapper = mountPanel();
    await flushPromises();

    await wrapper.get('[aria-label="Editar carpeta: Clientes"]').trigger('click');
    const options = wrapper.get('[data-testid="communication-folder-parent"]').findAll('option');

    expect(options.map((option) => option.element.value)).toEqual(['', '3']);
    expect(options.map((option) => option.text())).toEqual(['Raíz', 'Legal']);
  });

  // Falla si una respuesta rechazada se oculta y el operador no puede corregir la carpeta.
  it('keeps the folder form open with the save error', async () => {
    mockStore.saveFolder.mockResolvedValue({ success: false, message: 'No puedes mover una carpeta dentro de sí misma.' });
    const wrapper = mountPanel();
    await flushPromises();

    await wrapper.get('[aria-label="Nueva carpeta"]').trigger('click');
    await wrapper.get('[data-testid="communication-folder-name"]').setValue('Respuestas');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.get('[role="dialog"]').text()).toContain('No puedes mover una carpeta dentro de sí misma.');
    expect(wrapper.get('[data-testid="communication-folder-name"]').element.value).toBe('Respuestas');
  });
});

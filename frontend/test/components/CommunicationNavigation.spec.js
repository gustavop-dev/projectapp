import { mount } from '@vue/test-utils';
import CommunicationNavigation from '../../components/communications/CommunicationNavigation.vue';

const BaseInputStub = {
  props: ['modelValue', 'placeholder', 'size'],
  emits: ['update:modelValue'],
  template: '<input :value="modelValue" :placeholder="placeholder" />',
};

function mountNavigation(props = {}) {
  return mount(CommunicationNavigation, {
    props: {
      mode: 'project',
      selection: 'all',
      facets: {
        navigation_total: 0,
        without_project_count: 0,
        projects: [
          {
            id: 9,
            name: 'Kore',
            count: 0,
            catalog_bucket: 'active',
            unavailable: false,
          },
          {
            id: 13,
            name: 'Candle',
            count: 0,
            catalog_bucket: 'archived',
            unavailable: false,
          },
        ],
        clients: [],
      },
      ...props,
    },
    global: {
      stubs: {
        BaseInput: BaseInputStub,
        EntityNavigationModeSwitch: {
          template: '<div data-testid="mode-switch" />',
        },
      },
    },
  });
}

describe('CommunicationNavigation', () => {
  it('renders an active project with zero threads', () => {
    const wrapper = mountNavigation();

    // Falla si el catálogo excluye proyectos sólo porque aún no tienen hilos.
    expect(wrapper.get('[data-testid="communications-navigation-project-9"]').text())
      .toBe('Kore0');
  });

  it('renders archived projects inside their group', () => {
    const wrapper = mountNavigation();

    // Falla si los proyectos archivados desaparecen del catálogo en vez de agruparse.
    const archived = wrapper.get('[data-testid="communications-navigation-archived-group"]');
    expect(archived.text()).toBe('Proyectos archivados1Candle0');
  });

  it('emits the selected project identifier', async () => {
    const wrapper = mountNavigation();

    // Falla si seleccionar un proyecto deja el filtro de comunicaciones sin actualizar.
    await wrapper.get('[data-testid="communications-navigation-project-9"]').trigger('click');
    expect(wrapper.emitted('select')).toEqual([[9]]);
  });
});

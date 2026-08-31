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

  it('swaps active for inactive projects when the lifecycle toggle is on', async () => {
    const wrapper = mountNavigation();

    // Apagado: solo los activos, sin grupo de archivados.
    expect(wrapper.find('[data-testid="communications-navigation-archived-group"]').exists())
      .toBe(false);
    expect(wrapper.find('[data-testid="communications-navigation-project-9"]').exists())
      .toBe(true);

    await wrapper.get('[data-testid="communications-inactive-projects-toggle"]').trigger('click');
    expect(wrapper.emitted('toggle-inactive-projects')).toEqual([[true]]);
    await wrapper.setProps({ showInactiveProjects: true });

    // Encendido: el interruptor es EXCLUYENTE, igual que en el gestor documental.
    const archived = wrapper.get('[data-testid="communications-navigation-archived-group"]');
    expect(archived.text()).toBe('Proyectos archivados1Candle0');
    expect(wrapper.find('[data-testid="communications-navigation-project-9"]').exists())
      .toBe(false);
  });

  it('groups inactive clients under their own heading', async () => {
    const wrapper = mountNavigation({
      mode: 'client',
      facets: {
        navigation_total: 0,
        without_project_count: 0,
        projects: [],
        clients: [
          { id: 4, name: 'Activa', count: 1, catalog_bucket: 'active', unavailable: false },
          { id: 5, name: 'Histórica', count: 0, catalog_bucket: 'archived', unavailable: false },
        ],
      },
    });

    // En modo cliente no hay interruptor de ciclo de vida: el grupo se ve siempre,
    // que es exactamente lo que hace el gestor documental.
    expect(wrapper.find('[data-testid="communications-inactive-projects-control"]').exists())
      .toBe(false);
    expect(wrapper.get('[data-testid="communications-navigation-archived-group"]').text())
      .toContain('Clientes inactivos');
  });

  it('offers both sections open, with an accessible collapse trigger each', () => {
    const wrapper = mountNavigation();
    const entities = wrapper.get('[data-testid="communications-entities-section-toggle"]');
    const own = wrapper.get('[data-testid="communications-own-section-toggle"]');

    expect(entities.attributes('aria-expanded')).toBe('true');
    expect(own.attributes('aria-expanded')).toBe('true');
    expect(wrapper.find(`#${entities.attributes('aria-controls')}`).exists()).toBe(true);
    expect(wrapper.find(`#${own.attributes('aria-controls')}`).exists()).toBe(true);
    expect(entities.text()).toContain('Proyectos');
  });

  it('collapses the entity catalog without losing it from the DOM', async () => {
    const wrapper = mountNavigation();
    const entities = wrapper.get('[data-testid="communications-entities-section-toggle"]');

    await entities.trigger('click');

    expect(entities.attributes('aria-expanded')).toBe('false');
    const body = wrapper.get(`#${entities.attributes('aria-controls')}`);
    expect(body.attributes('aria-hidden')).toBe('true');

    // El estado es de modulo: dejarlo plegado se filtraria al resto del archivo.
    await entities.trigger('click');
    expect(entities.attributes('aria-expanded')).toBe('true');
  });

  it('lists loose threads under their own section', () => {
    const wrapper = mountNavigation({
      facets: {
        navigation_total: 3,
        without_project_count: 2,
        projects: [],
        clients: [],
      },
    });

    const own = wrapper.get('[data-testid="communications-own-section"]');
    expect(own.text()).toContain('Comunicaciones propias');
    expect(wrapper.get('[data-testid="communications-own-section-count"]').text()).toBe('2');
    expect(wrapper.get('[data-testid="communications-navigation-without-project"]').text())
      .toContain('Sin proyecto');
  });

  it('flips the archived scope from its own switch', async () => {
    const wrapper = mountNavigation();

    await wrapper.get('[data-testid="communications-archived-entry"]').trigger('click');

    expect(wrapper.emitted('toggle-archived')).toEqual([[true]]);
  });

  it('emits the selected project identifier', async () => {
    const wrapper = mountNavigation();

    // Falla si seleccionar un proyecto deja el filtro de comunicaciones sin actualizar.
    await wrapper.get('[data-testid="communications-navigation-project-9"]').trigger('click');
    expect(wrapper.emitted('select')).toEqual([[9]]);
  });
});

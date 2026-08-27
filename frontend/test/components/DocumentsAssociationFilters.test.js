/**
 * Tests for DocumentsAssociationFilters — los dos ejes de asociación del
 * listado (cliente/proyecto) con sus chips «sin asociar» excluyentes.
 */
import { mount } from '@vue/test-utils';
import DocumentsAssociationFilters from '../../components/panel/documents/DocumentsAssociationFilters.vue';

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'initialLabel', 'showLinkedHint', 'placeholder', 'testId'],
  emits: ['update:modelValue', 'select', 'create-new'],
  template: '<input :data-testid="testId" />',
};

const ProjectSelectStub = {
  name: 'ProjectSelect',
  props: ['modelValue', 'clientProfileId', 'allowNoClient', 'allowCreate', 'showHint', 'testid'],
  emits: ['update:modelValue', 'select'],
  template: '<input :data-testid="testid" />',
};

function mountFilters(props = {}) {
  return mount(DocumentsAssociationFilters, {
    props,
    global: {
      stubs: {
        ClientAutocomplete: ClientAutocompleteStub,
        ProjectSelect: ProjectSelectStub,
      },
    },
  });
}

describe('DocumentsAssociationFilters', () => {
  it('commits a picked client and drops it on clear', async () => {
    const wrapper = mountFilters();
    const autocomplete = wrapper.findComponent({ name: 'ClientAutocomplete' });

    autocomplete.vm.$emit('select', { id: 5, name: 'Ana Pérez' });
    expect(wrapper.emitted('update:client').at(-1)).toEqual([5]);

    autocomplete.vm.$emit('select', null);
    expect(wrapper.emitted('update:client').at(-1)).toEqual([null]);
  });

  it('the sin-cliente chip toggles the none sentinel', async () => {
    const wrapper = mountFilters();

    await wrapper.find('[data-testid="documents-filter-client-none"]').trigger('click');
    expect(wrapper.emitted('update:client').at(-1)).toEqual(['none']);

    await wrapper.setProps({ client: 'none' });
    await wrapper.find('[data-testid="documents-filter-client-none"]').trigger('click');
    expect(wrapper.emitted('update:client').at(-1)).toEqual([null]);
  });

  it('forwards the project selection and its none chip', async () => {
    const wrapper = mountFilters();

    wrapper.findComponent({ name: 'ProjectSelect' }).vm.$emit('update:modelValue', 11);
    expect(wrapper.emitted('update:project').at(-1)).toEqual([11]);

    await wrapper.find('[data-testid="documents-filter-project-none"]').trigger('click');
    expect(wrapper.emitted('update:project').at(-1)).toEqual(['none']);
  });

  it('scopes the project picker to the numeric client only', async () => {
    const wrapper = mountFilters({ client: 8 });
    expect(wrapper.findComponent({ name: 'ProjectSelect' }).props('clientProfileId')).toBe(8);

    await wrapper.setProps({ client: 'none' });
    expect(wrapper.findComponent({ name: 'ProjectSelect' }).props('clientProfileId')).toBeNull();
  });

  it('renders project help once below its complete group', () => {
    const wrapper = mountFilters();

    expect(wrapper.get('[data-testid="documents-filter-project-help"]').text())
      .toBe('Opcional. Filtra por un proyecto o elige «Sin proyecto».');
    expect(wrapper.findComponent({ name: 'ProjectSelect' }).props('showHint')).toBe(false);
  });

  it.each([
    ['documents-filter-client-none'],
    ['documents-filter-project-none'],
  ])('renders %s as an atomic button', (testId) => {
    // Fails if either unassociated action lets its short interface label wrap.
    const wrapper = mountFilters();

    expect(wrapper.get(`[data-testid="${testId}"]`).classes())
      .toContain('whitespace-nowrap');
  });
});

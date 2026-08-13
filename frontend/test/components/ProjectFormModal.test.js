/**
 * ProjectFormModal: the module's create/edit form.
 *
 * Covers the PA-38 minimum (name + client gate the submit), the client
 * immutability on edit (the payload must not carry client_profile_id), the
 * non-blocking duplicate warning, and the orphans-panel seed that leaves
 * only the name to type.
 */
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ProjectFormModal from '../../components/panel/projects/ProjectFormModal.vue';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'initialLabel', 'testId'],
  emits: ['update:modelValue', 'select', 'create-new'],
  template: '<div data-testid="client-autocomplete-stub" />',
};

const CLIENT = { id: 7, name: 'Deivis Ríos', company: 'Vástago', email: 'deivis@example.com' };

const RECORD = {
  id: 3,
  name: 'Vástago',
  description: 'App de gestión',
  status: 'paused',
  status_label: 'Pausado',
  client: { profile_id: 7, name: 'Deivis Ríos', company: 'Vástago' },
};

function mountModal(props = {}) {
  setActivePinia(createPinia());
  return mount(ProjectFormModal, {
    props: { open: true, saving: false, ...props },
    global: {
      plugins: [createPinia()],
      stubs: {
        ClientAutocomplete: ClientAutocompleteStub,
        ClientFormFields: true,
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['close'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseFormField: {
          props: ['label', 'hint', 'required'],
          template: '<div><label v-if="label">{{ label }}</label><slot /></div>',
        },
        BaseInput: {
          props: ['modelValue', 'type', 'placeholder'],
          emits: ['update:modelValue'],
          template:
            '<input :type="type || \'text\'" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseTextarea: {
          props: ['modelValue', 'rows'],
          emits: ['update:modelValue'],
          template:
            '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseSelect: {
          props: ['modelValue', 'options'],
          emits: ['update:modelValue'],
          template: '<select :value="modelValue" />',
        },
        BaseButton: {
          props: ['variant', 'size', 'disabled', 'type'],
          template:
            '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
}

describe('ProjectFormModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('gates the submit on the PA-38 minimum: name AND client', async () => {
    const wrapper = mountModal();
    await flushPromises();

    const submit = () => wrapper.find('[data-testid="project-form-submit"]');
    expect(submit().attributes('disabled')).toBeDefined();

    await wrapper.find('[data-testid="project-form-name"]').setValue('Kore');
    expect(submit().attributes('disabled')).toBeDefined();

    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('select', CLIENT);
    await flushPromises();
    expect(submit().attributes('disabled')).toBeUndefined();

    await wrapper.find('form').trigger('submit');
    const payload = wrapper.emitted('submit')[0][0];
    expect(payload).toEqual({
      name: 'Kore',
      client_profile_id: 7,
      description: '',
      status: 'active',
    });
  });

  it('editing hydrates the form and never sends the client', async () => {
    const wrapper = mountModal({ record: RECORD });
    await flushPromises();

    expect(wrapper.find('[data-testid="project-form-name"]').element.value).toBe('Vástago');
    expect(wrapper.find('[data-testid="project-form-client-readonly"]').text())
      .toContain('Deivis Ríos');
    expect(wrapper.findComponent(ClientAutocompleteStub).exists()).toBe(false);

    await wrapper.find('[data-testid="project-form-name"]').setValue('Vástago App');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload).toEqual({
      name: 'Vástago App',
      description: 'App de gestión',
      status: 'paused',
    });
    expect(payload).not.toHaveProperty('client_profile_id');
  });

  it('warns about a same-name project for the same client without blocking', async () => {
    const wrapper = mountModal({
      existingProjects: [
        { id: 9, name: 'Vástago', client: { profile_id: 7 } },
      ],
    });
    await flushPromises();

    await wrapper.find('[data-testid="project-form-name"]').setValue('vastago');
    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('select', CLIENT);
    await flushPromises();

    expect(wrapper.find('[data-testid="project-form-duplicate-warning"]').exists()).toBe(true);
    expect(
      wrapper.find('[data-testid="project-form-submit"]').attributes('disabled'),
    ).toBeUndefined();
  });

  it('stays silent when the same name belongs to another client', async () => {
    const wrapper = mountModal({
      existingProjects: [
        { id: 9, name: 'Vástago', client: { profile_id: 99 } },
      ],
    });
    await flushPromises();

    await wrapper.find('[data-testid="project-form-name"]').setValue('Vástago');
    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('select', CLIENT);
    await flushPromises();

    expect(wrapper.find('[data-testid="project-form-duplicate-warning"]').exists()).toBe(false);
  });

  it('a seeded client leaves only the name to type', async () => {
    const wrapper = mountModal({
      seedClient: { id: 7, name: 'Deivis Ríos' },
    });
    await flushPromises();

    await wrapper.find('[data-testid="project-form-name"]').setValue('Vástago');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.client_profile_id).toBe(7);
    expect(payload.name).toBe('Vástago');
  });
});

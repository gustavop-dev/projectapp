/**
 * ProjectFormModal: the module's create/edit form.
 *
 * Covers the PA-38 minimum (name + client validate on submit), the client
 * immutability on edit (the payload must not carry client_profile_id), the
 * non-blocking duplicate warning, and the orphans-panel seed that leaves
 * only the name to type.
 */
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ProjectFormModal from '../../components/panel/projects/ProjectFormModal.vue';
import { get_request } from '../../stores/services/request_http';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: {
    modelValue: { type: Number, default: null },
    initialLabel: { type: String, default: '' },
    testId: { type: String, default: '' },
    allowCreate: { type: Boolean, default: false },
    error: { type: Boolean, default: false },
    errorDescribedBy: { type: String, default: '' },
  },
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
  current_state: {
    id: 12,
    name: 'Pausado',
    system_key: 'paused',
    operational_effect: 'paused',
  },
  document_manager_enabled: false,
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
          props: ['label', 'hint', 'required', 'error'],
          template: `
            <div>
              <label v-if="label">{{ label }}<span v-if="required">*</span></label>
              <slot :invalid="Boolean(error)" :error-id="error ? 'field-error' : undefined" />
              <p v-if="error" role="alert">{{ error }}</p>
              <p v-else-if="hint">{{ hint }}</p>
            </div>
          `,
        },
        BaseFormRow: { template: '<div><slot /></div>' },
        BaseModalActions: { template: '<div data-testid="base-modal-actions"><slot /></div>' },
        BaseInput: {
          props: ['modelValue', 'type', 'placeholder', 'error'],
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
          template: `
            <select :value="modelValue">
              <option v-for="option in options" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          `,
        },
        BaseToggle: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: `
            <button
              type="button"
              :aria-pressed="String(modelValue)"
              @click="$emit('update:modelValue', !modelValue)"
            >Alternar</button>
          `,
        },
        BaseButton: {
          props: ['variant', 'size', 'disabled', 'type'],
          // `emits` declared so the parent's @click doesn't ALSO fall through
          // as a native listener (it would double-fire every handler).
          emits: ['click'],
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
    get_request.mockImplementation((url) => Promise.resolve({
      data: url.startsWith('project-states/')
        ? [{
          id: 10,
          name: 'En desarrollo',
          system_key: 'development',
          operational_effect: 'development',
          is_active: true,
          merged_into: null,
          group: 4,
        }]
        : [{ id: 4, name: 'Ciclo del proyecto', selection_mode: 'exclusive' }],
    }));
  });

  it('places validation beside each missing required field after submit', async () => {
    const wrapper = mountModal();
    await flushPromises();

    const submit = () => wrapper.find('[data-testid="project-form-submit"]');
    expect(submit().attributes('disabled')).toBeUndefined();

    await wrapper.find('form').trigger('submit');

    expect(wrapper.findAll('[role="alert"]').map((alert) => alert.text())).toEqual([
      'Escribe el nombre del proyecto.',
      'Elige o crea un cliente.',
    ]);
    expect(wrapper.emitted('submit')).toBeUndefined();

    await wrapper.find('[data-testid="project-form-name"]').setValue('Kore');
    expect(wrapper.text()).not.toContain('Escribe el nombre del proyecto.');

    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('select', CLIENT);
    await flushPromises();
    expect(wrapper.text()).not.toContain('Elige o crea un cliente.');

    await wrapper.find('form').trigger('submit');
    const payload = wrapper.emitted('submit')[0][0];
    expect(payload).toEqual({
      name: 'Kore',
      client_profile_id: 7,
      description: '',
      document_manager_enabled: true,
      state_id: 10,
    });
  });

  it('renders En desarrollo as the initial state selection', async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.get('[data-testid="project-form-status"]').element.value).toBe('10');
  });

  it('omits the redundant default-state help', async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.get('[data-testid="project-form-status"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain('Si no eliges un estado');
    expect(wrapper.text()).not.toContain('(opcional)');
  });

  it('exposes inline client creation from the selector', async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.findComponent(ClientAutocompleteStub).props('allowCreate')).toBe(true);
  });

  it('editing hydrates the form and never sends the client', async () => {
    const wrapper = mountModal({ record: RECORD });
    await flushPromises();

    expect(wrapper.find('[data-testid="project-form-name"]').element.value).toBe('Vástago');
    expect(wrapper.find('[data-testid="project-form-client-readonly"]').text())
      .toContain('Deivis Ríos');
    expect(wrapper.findComponent(ClientAutocompleteStub).exists()).toBe(false);
    expect(wrapper.get('[data-testid="project-form-document-manager"]')
      .attributes('aria-pressed')).toBe('false');

    await wrapper.find('[data-testid="project-form-name"]').setValue('Vástago App');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload).toEqual({
      name: 'Vástago App',
      description: 'App de gestión',
      document_manager_enabled: false,
    });
    expect(payload).not.toHaveProperty('client_profile_id');
  });

  it('lets an operator enable a historical project without changing its content', async () => {
    const wrapper = mountModal({ record: RECORD });
    await flushPromises();

    await wrapper.get('[data-testid="project-form-document-manager"]').trigger('click');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')[0][0].document_manager_enabled).toBe(true);
    expect(wrapper.text()).toContain('nunca elimina carpetas ni archivos');
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

  it('the edit form offers the guided change-client entry, the create form does not', async () => {
    const editing = mountModal({ record: RECORD });
    await flushPromises();

    await editing
      .find('[data-testid="project-form-change-client"]')
      .trigger('click');

    // The field itself stays immutable: the button only asks the page to
    // open the guided cascade.
    expect(editing.emitted('change-client')).toHaveLength(1);
    expect(editing.emitted('submit')).toBeUndefined();

    const creating = mountModal();
    await flushPromises();
    expect(
      creating.find('[data-testid="project-form-change-client"]').exists(),
    ).toBe(false);
  });
});

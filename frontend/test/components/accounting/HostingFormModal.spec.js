import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import HostingFormModal from '../../../components/accounting/HostingFormModal.vue';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request, create_request } = require('../../../stores/services/request_http');

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'initialLabel', 'testId'],
  emits: ['update:modelValue', 'select', 'create-new'],
  template: '<div data-testid="client-autocomplete-stub" />',
};

const CLIENT = {
  id: 5,
  name: 'Daniel Felipe Corredor',
  company: 'MIMITTOS',
  email: 'arq.daniel@example.com',
  nit: '901234567',
  cedula: '',
  is_email_placeholder: false,
};

const LEGACY_RECORD = {
  id: 1,
  client: null,
  client_display_name: '',
  client_name: 'Jimmy & Daniel - Mimittos',
  client_email: '',
  client_contact_name: '',
  client_identification: '',
  domain_url: 'https://mimittos.com/',
  monthly_value: '19440.00',
  payment_modality: 'quarterly',
  benefit: '',
  valid_from: '2026-02-01',
  valid_to: '2026-11-01',
  payment_per_cycle: '58320.00',
  is_active: true,
  notes: '',
};

function mountModal(props = {}) {
  setActivePinia(createPinia());
  return mount(HostingFormModal, {
    props: { open: true, saving: false, ...props },
    global: {
      plugins: [createPinia()],
      stubs: {
        ClientAutocomplete: ClientAutocompleteStub,
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
        BaseCurrencyInput: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<input type="text" inputmode="numeric" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
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
        BaseToggle: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input type="checkbox" :checked="modelValue" />',
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

describe('HostingFormModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    get_request.mockResolvedValue({ data: [CLIENT] });
  });

  it('sends the client alongside the billing snapshot', async () => {
    const wrapper = mountModal();
    await flushPromises();

    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('select', CLIENT);
    await flushPromises();
    await wrapper.find('[data-testid="hosting-form-monthly"]').setValue('19440');

    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.client).toBe(5);
    // The snapshot is seeded from the profile so the cuenta de cobro prints
    // something even if the operator types nothing else.
    expect(payload.client_name).toBe('MIMITTOS');
    expect(payload.client_email).toBe('arq.daniel@example.com');
    expect(payload.client_identification).toBe('901234567');
  });

  it('never overwrites what the operator already typed', async () => {
    const wrapper = mountModal();
    await flushPromises();

    await wrapper.find('[data-testid="hosting-form-client-name"]').setValue('Facturar a Otro');
    await wrapper.find('[data-testid="hosting-form-client-email"]').setValue('pagos@otro.co');
    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('select', CLIENT);
    await flushPromises();

    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.client_name).toBe('Facturar a Otro');
    expect(payload.client_email).toBe('pagos@otro.co');
  });

  it('suggests the matching client when editing a legacy record', async () => {
    const wrapper = mountModal({ record: { ...LEGACY_RECORD } });
    await flushPromises();

    const suggestion = wrapper.find('[data-testid="hosting-form-client-suggestion"]');
    expect(suggestion.text()).toContain('MIMITTOS');
    expect(get_request).toHaveBeenCalledWith(
      expect.stringContaining('client-profiles/search/'),
      expect.anything(),
    );

    await wrapper.find('[data-testid="hosting-form-accept-suggestion"]').trigger('click');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')[0][0].client).toBe(5);
  });

  it('flags a legacy record as pending instead of blocking it', async () => {
    const wrapper = mountModal({ record: { ...LEGACY_RECORD } });
    await flushPromises();

    expect(wrapper.find('[data-testid="hosting-form-client-pending"]').exists()).toBe(true);

    // Saving without a client still works: completing it is a separate step.
    await wrapper.find('form').trigger('submit');
    expect(wrapper.emitted('submit')[0][0].client).toBeNull();
  });

  it('offers no suggestion when nothing resembles a registered client', async () => {
    get_request.mockResolvedValue({ data: [] });
    const wrapper = mountModal({
      record: { ...LEGACY_RECORD, client_name: 'Katerin Ruiz - Senses Candles' },
    });
    await flushPromises();

    expect(wrapper.find('[data-testid="hosting-form-client-suggestion"]').exists()).toBe(false);
  });

  it('creates a client inline and links it', async () => {
    const wrapper = mountModal();
    await flushPromises();

    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('create-new', 'Senses Candles');
    await flushPromises();
    expect(
      wrapper.find('[data-testid="hosting-form-inline-client-name"]').element.value,
    ).toBe('Senses Candles');

    create_request.mockResolvedValueOnce({
      data: { ...CLIENT, id: 12, name: 'Senses Candles', company: '' },
    });
    await wrapper.find('[data-testid="hosting-form-inline-client-save"]').trigger('click');
    await flushPromises();

    expect(create_request).toHaveBeenCalledWith(
      'proposals/client-profiles/create/',
      expect.objectContaining({ name: 'Senses Candles' }),
    );
    expect(wrapper.find('[data-testid="hosting-form-inline-client"]').exists()).toBe(false);

    await wrapper.find('[data-testid="hosting-form-monthly"]').setValue('38333');
    await wrapper.find('form').trigger('submit');
    expect(wrapper.emitted('submit')[0][0].client).toBe(12);
  });
});

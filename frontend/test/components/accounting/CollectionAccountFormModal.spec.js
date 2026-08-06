import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import CollectionAccountFormModal from '../../../components/accounting/CollectionAccountFormModal.vue';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

jest.mock('@vueuse/core', () => ({
  useDebounceFn: (fn) => fn,
  onClickOutside: jest.fn(),
}));

const { get_request, create_request } = require('../../../stores/services/request_http');

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'testId'],
  emits: ['update:modelValue', 'select', 'create-new'],
  template: '<div data-testid="client-autocomplete-stub" />',
};

const IncomeFormModalStub = {
  name: 'IncomeFormModal',
  props: ['open', 'record', 'saving'],
  emits: ['close', 'submit'],
  template: '<div v-if="open" data-testid="income-form-stub" />',
};

const clientFixture = {
  id: 5,
  name: 'Ana Pérez',
  company: 'Acme Soluciones',
  email: 'ana@acme.co',
  nit: '901234567',
  cedula: '',
  is_email_placeholder: false,
};

const incomeFixture = {
  id: 8,
  client: null,
  client_name: null,
  concept: 'Desarrollo módulo de reportes',
  kind: 'expected',
  kind_label: 'Esperado',
  total_amount: '1490000.00',
  pending_amount: '1490000.00',
  has_collection_account: false,
  collection_account_number: null,
};

const linkedIncomeFixture = {
  ...incomeFixture,
  id: 9,
  concept: 'Hosting Kore renovación',
  has_collection_account: true,
  collection_account_number: 'PA-KORE-001',
};

function mockRequests() {
  get_request.mockImplementation((url) => {
    if (url.includes('client-profiles/5/')) {
      return Promise.resolve({ data: clientFixture });
    }
    if (url.includes('next-number')) {
      return Promise.resolve({
        data: {
          suggested_number: 'PA-ACME-003',
          billing_code: 'ACME',
          issuer_city: 'Bogotá',
        },
      });
    }
    return Promise.resolve({
      data: { results: [incomeFixture, linkedIncomeFixture] },
    });
  });
  create_request.mockImplementation((url) => {
    if (url.includes('preview')) {
      return Promise.resolve({
        data: {
          subject: 'Cuenta de cobro PA-ACME-003 — ProjectApp',
          html_body: '<p>Valor a pagar</p>',
          public_number: 'PA-ACME-003',
          total: '1490000.00',
          due_date: '2026-08-13',
          customer_email: 'ana@acme.co',
          pdf_base64: 'JVBERi0=',
        },
      });
    }
    return Promise.resolve({
      data: {
        document: { id: 33, public_number: 'PA-ACME-003' },
        email_sent: true,
      },
    });
  });
}

function mountModal(props = {}) {
  return mount(CollectionAccountFormModal, {
    props: { open: true, ...props },
    global: {
      plugins: [createPinia()],
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['close'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseFormField: {
          props: ['label', 'hint', 'error', 'required', 'for', 'size'],
          template: '<div><label v-if="label">{{ label }}</label><slot /></div>',
        },
        BaseInput: {
          props: ['modelValue', 'type', 'size', 'error', 'placeholder', 'disabled', 'min', 'max', 'maxlength'],
          emits: ['update:modelValue'],
          template:
            '<input :type="type || \'text\'" :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseCurrencyInput: {
          props: ['modelValue', 'decimals', 'size', 'error', 'placeholder', 'disabled', 'suggestion'],
          emits: ['update:modelValue'],
          template:
            '<input type="text" inputmode="numeric" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value === \'\' ? null : Number($event.target.value))" />',
        },
        BaseTextarea: {
          props: ['modelValue', 'rows'],
          emits: ['update:modelValue'],
          template:
            '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseSegmented: {
          props: ['modelValue', 'options', 'fullWidth'],
          emits: ['update:modelValue'],
          template:
            '<div><button v-for="o in options" :key="o.value" type="button" @click="$emit(\'update:modelValue\', o.value)">{{ o.label }}</button></div>',
        },
        BaseButton: {
          props: ['variant', 'size', 'disabled', 'type', 'iconOnly'],
          template:
            '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
        ClientAutocomplete: ClientAutocompleteStub,
        IncomeFormModal: IncomeFormModalStub,
      },
    },
  });
}

async function selectClient(wrapper, client = clientFixture) {
  const autocomplete = wrapper.findComponent(ClientAutocompleteStub);
  autocomplete.vm.$emit('update:modelValue', client.id);
  autocomplete.vm.$emit('select', client);
  await flushPromises();
}

describe('CollectionAccountFormModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
    mockRequests();
    global.URL.createObjectURL = jest.fn(() => 'blob:preview-pdf');
    global.URL.revokeObjectURL = jest.fn();
  });

  it('prefills concept and amount from the income prop and locks the selector', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();

    expect(wrapper.find('[data-testid="collection-form-income-locked"]').text())
      .toContain('Desarrollo módulo de reportes');
    expect(wrapper.find('[data-testid="collection-form-income"]').exists()).toBe(false);
    expect(
      wrapper.find('[data-testid="collection-form-concept"]').element.value,
    ).toBe('Desarrollo módulo de reportes');
    expect(
      Number(wrapper.find('[data-testid="collection-form-amount"]').element.value),
    ).toBe(1490000);
  });

  it('lists incomes and blocks the ones that already have a cuenta', async () => {
    const wrapper = mountModal();
    await flushPromises();

    await wrapper.find('[data-testid="collection-form-income"]').trigger('focus');
    await flushPromises();

    const blocked = wrapper.find('[data-testid="collection-form-income-option-9"]');
    expect(blocked.text()).toContain('Ya tiene cuenta de cobro (PA-KORE-001)');

    await blocked.trigger('mousedown');
    expect(wrapper.find('[data-testid="collection-form-concept"]').element.value).toBe('');

    await wrapper.find('[data-testid="collection-form-income-option-8"]').trigger('mousedown');
    expect(wrapper.find('[data-testid="collection-form-concept"]').element.value)
      .toBe('Desarrollo módulo de reportes');
  });

  it('selecting a client prefills the snapshot and the suggested consecutivo', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();

    await selectClient(wrapper);

    expect(get_request).toHaveBeenCalledWith(
      'accounting/collection-accounts/next-number/?client_profile_id=5',
    );
    expect(
      wrapper.find('[data-testid="collection-form-number"]').element.value,
    ).toBe('PA-ACME-003');
    expect(
      wrapper.find('[data-testid="collection-form-customer-name"]').element.value,
    ).toBe('Acme Soluciones');
    expect(
      wrapper.find('[data-testid="collection-form-customer-email"]').element.value,
    ).toBe('ana@acme.co');
    expect(
      wrapper.find('[data-testid="collection-form-customer-identification"]').element.value,
    ).toBe('901234567');
  });

  it('omits the consecutivo from the payload while it matches the suggestion', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();
    await selectClient(wrapper);

    await wrapper.find('[data-testid="collection-form-preview"]').trigger('submit');
    await flushPromises();

    const [url, payload] = create_request.mock.calls.at(-1);
    expect(url).toBe('accounting/collection-accounts/preview/');
    expect(payload.public_number).toBeUndefined();
    expect(payload.client_profile_id).toBe(5);
    expect(payload.income_record_id).toBe(8);
    expect(payload.items[0].unit_price).toBe('1490000');
  });

  it('sends an edited consecutivo in the payload', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();
    await selectClient(wrapper);

    const numberInput = wrapper.find('[data-testid="collection-form-number"]');
    await numberInput.setValue('PA-ACME-044');
    await numberInput.trigger('input');

    await wrapper.find('[data-testid="collection-form-preview"]').trigger('submit');
    await flushPromises();

    const payload = create_request.mock.calls.at(-1)[1];
    expect(payload.public_number).toBe('PA-ACME-044');
  });

  it('shows the preview and confirm sends the same payload and emits created', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();
    await selectClient(wrapper);

    await wrapper.find('[data-testid="collection-form-preview"]').trigger('submit');
    await flushPromises();

    expect(wrapper.find('[data-testid="collection-preview-subject"]').text())
      .toContain('PA-ACME-003');
    const previewPayload = create_request.mock.calls.at(-1)[1];

    await wrapper.find('[data-testid="collection-form-confirm"]').trigger('click');
    await flushPromises();

    const [confirmUrl, confirmPayload] = create_request.mock.calls.at(-1);
    expect(confirmUrl).toBe('accounting/collection-accounts/create/');
    expect(confirmPayload).toEqual(previewPayload);
    expect(wrapper.emitted('created')).toBeTruthy();
  });

  it('stays on the form when the preview request fails', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();
    await selectClient(wrapper);

    create_request.mockImplementation((url) => {
      if (url.includes('preview')) {
        return Promise.reject({ response: { status: 500, data: {} } });
      }
      return Promise.resolve({
        data: { document: { id: 33, public_number: 'PA-ACME-003' }, email_sent: true },
      });
    });

    await wrapper.find('[data-testid="collection-form-preview"]').trigger('submit');
    await flushPromises();

    // Falls if goPreview() ever moves `step.value = 'preview'` before the
    // `!result.success` guard: the operator would see a stale/partial
    // preview instead of staying on the form with the error notification.
    expect(wrapper.find('[data-testid="collection-preview-subject"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="collection-form-concept"]').exists()).toBe(true);
  });

  it('volver a editar returns to the form keeping its state', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();
    await selectClient(wrapper);

    await wrapper.find('[data-testid="collection-form-preview"]').trigger('submit');
    await flushPromises();
    await wrapper.find('[data-testid="collection-form-back"]').trigger('click');

    expect(
      wrapper.find('[data-testid="collection-form-concept"]').element.value,
    ).toBe('Desarrollo módulo de reportes');
    expect(
      wrapper.find('[data-testid="collection-form-number"]').element.value,
    ).toBe('PA-ACME-003');
  });

  it('preloads and locks the client when the income already carries one', async () => {
    const wrapper = mountModal({
      income: { ...incomeFixture, client: 5, client_name: 'Acme Soluciones' },
    });
    await flushPromises();

    // No second ask: the picker is replaced by a locked display...
    expect(wrapper.find('[data-testid="collection-form-client-locked"]').text())
      .toContain('Acme Soluciones');
    expect(wrapper.findComponent(ClientAutocompleteStub).exists()).toBe(false);
    // ...and the snapshot + suggested consecutivo arrived on their own.
    expect(get_request).toHaveBeenCalledWith('proposals/client-profiles/5/');
    expect(
      wrapper.find('[data-testid="collection-form-customer-email"]').element.value,
    ).toBe('ana@acme.co');
    expect(
      wrapper.find('[data-testid="collection-form-number"]').element.value,
    ).toBe('PA-ACME-003');

    await wrapper.find('[data-testid="collection-form-preview"]').trigger('submit');
    await flushPromises();

    expect(create_request.mock.calls.at(-1)[1].client_profile_id).toBe(5);
  });

  it('create-new client opens the inline form and links the created profile', async () => {
    const wrapper = mountModal({ income: incomeFixture });
    await flushPromises();

    wrapper.findComponent(ClientAutocompleteStub).vm.$emit('create-new', 'Nuevo SAS');
    await flushPromises();

    const inline = wrapper.find('[data-testid="collection-form-inline-client"]');
    expect(inline.exists()).toBe(true);
    expect(
      wrapper.find('[data-testid="collection-form-inline-client-name"]').element.value,
    ).toBe('Nuevo SAS');

    create_request.mockResolvedValueOnce({
      data: { ...clientFixture, id: 12, name: 'Nuevo SAS', company: '' },
    });
    await wrapper.find('[data-testid="collection-form-inline-client-save"]').trigger('click');
    await flushPromises();

    expect(create_request).toHaveBeenCalledWith(
      'proposals/client-profiles/create/',
      expect.objectContaining({ name: 'Nuevo SAS' }),
    );
    expect(wrapper.find('[data-testid="collection-form-inline-client"]').exists()).toBe(false);
    expect(
      wrapper.find('[data-testid="collection-form-number"]').element.value,
    ).toBe('PA-ACME-003');
  });
});

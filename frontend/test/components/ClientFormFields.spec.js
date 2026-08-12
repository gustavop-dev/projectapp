import { mount } from '@vue/test-utils';

import ClientFormFields from '~/components/clients/ClientFormFields.vue';
import { emptyClientForm } from '~/utils/billingCode';

function mountFields(overrides = {}) {
  return mount(ClientFormFields, {
    props: {
      modelValue: { ...emptyClientForm(), ...overrides },
      testidPrefix: 'clients-new',
    },
  });
}

const FIELDS = ['name', 'email', 'phone', 'company', 'nit', 'billing-code'];

describe('ClientFormFields', () => {
  it('renders the same six fields every client surface shares', () => {
    const wrapper = mountFields();

    FIELDS.forEach((field) => {
      expect(wrapper.find(`[data-testid="clients-new-${field}"]`).exists()).toBe(true);
    });
  });

  it('keeps the fields in one fixed order so the modals stay recognizable', () => {
    const wrapper = mountFields();

    const rendered = wrapper
      .findAll('[data-testid^="clients-new-"]')
      .map((input) => input.attributes('data-testid'));

    expect(rendered).toEqual(FIELDS.map((field) => `clients-new-${field}`));
  });

  it('requires only the name and marks the rest optional', () => {
    const wrapper = mountFields();

    expect(
      wrapper.find('[data-testid="clients-new-name"]').attributes('required'),
    ).toBeDefined();
    FIELDS.slice(1).forEach((field) => {
      expect(
        wrapper.find(`[data-testid="clients-new-${field}"]`).attributes('required'),
      ).toBeUndefined();
    });

    const text = wrapper.text();
    ['Email', 'Teléfono', 'Empresa', 'NIT', 'Código de facturación'].forEach((label) => {
      expect(text).toContain(`${label} (opcional)`);
    });
  });

  it('emits the whole form back when a field changes', async () => {
    const wrapper = mountFields();

    await wrapper.find('[data-testid="clients-new-billing-code"]').setValue('G&M');

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual({
      ...emptyClientForm(),
      billing_code: 'G&M',
    });
  });

  it('caps the billing code at the length the column allows', () => {
    const wrapper = mountFields();

    expect(
      wrapper.find('[data-testid="clients-new-billing-code"]').attributes('maxlength'),
    ).toBe('12');
  });

  it('drives each testid from the prefix so surfaces keep distinct hooks', () => {
    const wrapper = mount(ClientFormFields, {
      props: {
        modelValue: emptyClientForm(),
        testidPrefix: 'collection-form-inline-client',
      },
    });

    expect(
      wrapper.find('[data-testid="collection-form-inline-client-nit"]').exists(),
    ).toBe(true);
    expect(wrapper.find('[data-testid="clients-new-nit"]').exists()).toBe(false);
  });
});

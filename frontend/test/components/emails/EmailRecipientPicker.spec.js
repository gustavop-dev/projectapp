import { flushPromises, mount } from '@vue/test-utils';
import EmailRecipientPicker from '../../../components/emails/EmailRecipientPicker.vue';


const mockSearchClients = jest.fn();

jest.mock('@vueuse/core', () => ({
  useDebounceFn: (callback) => callback,
}));

jest.mock('../../../stores/proposal_clients', () => ({
  useProposalClientsStore: () => ({ searchClients: mockSearchClients }),
}));

const BaseFormFieldStub = {
  props: ['label', 'error'],
  template: '<div><label>{{ label }}</label><slot /><p v-if="error" role="alert">{{ error }}</p></div>',
};

const BaseFloatingListboxStub = {
  props: ['open'],
  template: '<div v-if="open"><slot /></div>',
};

function mountPicker(props = {}) {
  return mount(EmailRecipientPicker, {
    props: {
      modelValue: [],
      label: 'Para',
      totalCount: 0,
      testId: 'recipient-picker',
      ...props,
    },
    global: {
      stubs: {
        BaseFormField: BaseFormFieldStub,
        BaseFloatingListbox: BaseFloatingListboxStub,
        BaseButton: {
          props: ['disabled', 'type'],
          template: '<button :type="type" :disabled="disabled"><slot /></button>',
        },
        BaseActionIcon: true,
      },
    },
  });
}

describe('EmailRecipientPicker', () => {
  beforeEach(() => {
    mockSearchClients.mockReset().mockResolvedValue({ success: true, data: [] });
  });

  it('adds a normalized manual address', async () => {
    const wrapper = mountPicker();

    await wrapper.get('input').setValue('Persona@Example.com');
    await wrapper.get('input').trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual([
      { email: 'persona@example.com', name: '', clientId: null },
    ]);
  });

  it('adds pasted addresses as one update', async () => {
    const wrapper = mountPicker();

    await wrapper.get('input').trigger('paste', {
      clipboardData: {
        getData: () => 'uno@example.com; dos@example.com',
      },
    });

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual([
      { email: 'uno@example.com', name: '', clientId: null },
      { email: 'dos@example.com', name: '', clientId: null },
    ]);
  });

  it('rejects an address used by the other header', async () => {
    const wrapper = mountPicker({ excludedEmails: ['repetido@example.com'] });

    await wrapper.get('input').setValue('repetido@example.com');
    await wrapper.get('input').trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    expect(wrapper.get('[role="alert"]').text()).toContain('otro campo');
  });

  it('enforces the combined recipient limit', async () => {
    const wrapper = mountPicker({ totalCount: 10 });

    await wrapper.get('input').setValue('extra@example.com');
    await wrapper.get('input').trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    expect(wrapper.get('[role="alert"]').text()).toContain('máximo 10');
  });

  it('adds a registered client result', async () => {
    mockSearchClients.mockResolvedValue({
      success: true,
      data: [{
        id: 27,
        name: 'Ana Cliente',
        email: 'ana@example.com',
        company: 'Ana SAS',
        is_email_placeholder: false,
      }],
    });
    const wrapper = mountPicker();

    await wrapper.get('input').setValue('Ana');
    await flushPromises();
    await wrapper.get('[data-testid="recipient-picker-client-27"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual([
      { email: 'ana@example.com', name: 'Ana Cliente', clientId: 27 },
    ]);
  });
});

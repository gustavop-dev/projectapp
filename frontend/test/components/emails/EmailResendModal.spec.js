import { flushPromises, mount } from '@vue/test-utils';
import EmailResendModal from '../../../components/emails/EmailResendModal.vue';

const mockStore = {
  isResending: false,
  resendEmail: jest.fn(),
};

jest.mock('../../../stores/emails', () => ({
  useEmailStore: () => mockStore,
}));

const entry = {
  id: 9,
  recipient: 'original@example.com',
  subject: 'Propuesta exacta',
  attachments: [{ id: 4, filename: 'propuesta.pdf' }],
};

function mountModal(props = {}) {
  return mount(EmailResendModal, {
    props: { open: true, entry, ...props },
    global: {
      stubs: {
        BaseModal: { template: '<div><slot /></div>' },
        BaseInput: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)">',
        },
        BaseButton: {
          template: '<button><slot /></button>',
        },
        BaseAlert: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('EmailResendModal', () => {
  beforeEach(() => {
    mockStore.isResending = false;
    mockStore.resendEmail.mockReset().mockResolvedValue({
      success: true,
      data: { email_log_id: 22 },
    });
  });

  it('shows the locked subject and retained attachment', () => {
    const wrapper = mountModal();

    expect(wrapper.text()).toContain('Propuesta exacta');
    expect(wrapper.text()).toContain('propuesta.pdf');
    expect(wrapper.text()).toContain('Sólo puedes cambiar el destinatario');
  });

  it('submits the edited recipient without editable message fields', async () => {
    const wrapper = mountModal();
    await wrapper.get('input').setValue('nuevo@example.com');

    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mockStore.resendEmail).toHaveBeenCalledWith(9, 'nuevo@example.com');
    expect(wrapper.emitted('resent')[0]).toEqual([{ email_log_id: 22 }]);
  });

  it('keeps the modal open with a server failure message', async () => {
    mockStore.resendEmail.mockResolvedValue({
      success: false,
      message: 'SMTP no disponible.',
    });
    const wrapper = mountModal();

    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.text()).toContain('SMTP no disponible.');
    expect(wrapper.emitted('resent')).toBeUndefined();
  });
});

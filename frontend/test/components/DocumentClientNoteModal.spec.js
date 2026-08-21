import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

import DocumentClientNoteModal from '../../components/panel/documents/DocumentClientNoteModal.vue';
import BaseButton from '../../components/base/BaseButton.vue';
import BaseInput from '../../components/base/BaseInput.vue';
import BaseModal from '../../components/base/BaseModal.vue';
import BaseTextarea from '../../components/base/BaseTextarea.vue';

const mockNotifyError = jest.fn();

jest.mock('../../composables/usePanelNotify', () => ({
  usePanelNotify: () => ({ error: mockNotifyError }),
}));

function mountModal(props = {}) {
  return mount(DocumentClientNoteModal, {
    props: { modelValue: true, ...props },
    global: {
      components: { BaseButton, BaseInput, BaseModal, BaseTextarea },
      stubs: {
        Teleport: true,
        Transition: false,
        NuxtLink: { template: '<a><slot /></a>' },
      },
    },
  });
}

const subjectField = (wrapper) => wrapper.find('[data-testid="client-note-subject"]');
const emailField = (wrapper) => wrapper.find('[data-testid="client-note-email"]');
const whatsappField = (wrapper) => wrapper.find('[data-testid="client-note-whatsapp"]');

describe('DocumentClientNoteModal', () => {
  beforeEach(() => {
    mockNotifyError.mockReset();
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    });
  });

  it('opens with the stored client note', () => {
    const wrapper = mountModal({
      subject: 'Entrega lista',
      emailBody: 'Hola Ana, el documento está listo.',
      whatsappMessage: 'Hola Ana, revisa tu correo.',
    });

    expect(subjectField(wrapper).element.value).toBe('Entrega lista');
    expect(emailField(wrapper).element.value).toBe('Hola Ana, el documento está listo.');
    expect(whatsappField(wrapper).element.value).toBe('Hola Ana, revisa tu correo.');
  });

  it('applies a trimmed client note', async () => {
    const wrapper = mountModal();
    await subjectField(wrapper).setValue('  Informe listo  ');
    await emailField(wrapper).setValue('  Correo completo  ');
    await whatsappField(wrapper).setValue('  WhatsApp breve  ');

    await wrapper.find('[data-testid="document-client-note-modal"]').trigger('submit');

    expect(wrapper.emitted('apply')[0]).toEqual([{
      subject: 'Informe listo',
      emailBody: 'Correo completo',
      whatsappMessage: 'WhatsApp breve',
    }]);
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]);
  });

  it('closes without applying draft changes', async () => {
    const wrapper = mountModal({ subject: 'Original' });
    await subjectField(wrapper).setValue('Borrador');

    await wrapper.find('[data-testid="client-note-cancel"]').trigger('click');

    expect(wrapper.emitted('apply')).toBeFalsy();
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]);
  });

  it('copies the email body', async () => {
    const wrapper = mountModal({ emailBody: 'Correo para copiar' });

    await wrapper.find('[data-testid="client-note-copy-email"]').trigger('click');
    await nextTick();

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Correo para copiar');
    expect(wrapper.find('[data-testid="client-note-copy-email"]').text()).toBe('Copiado');
  });

  it('renders stored content as read only', () => {
    const wrapper = mountModal({ readonly: true, subject: 'Asunto guardado' });

    expect(subjectField(wrapper).element.disabled).toBe(true);
    expect(emailField(wrapper).element.disabled).toBe(true);
    expect(whatsappField(wrapper).element.disabled).toBe(true);
    expect(wrapper.find('[data-testid="client-note-apply"]').exists()).toBe(false);
  });
});

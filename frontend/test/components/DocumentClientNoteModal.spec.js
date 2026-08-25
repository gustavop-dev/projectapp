import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

import DocumentClientNoteModal from '../../components/panel/documents/DocumentClientNoteModal.vue';
import BaseActionIcon from '../../components/base/BaseActionIcon.vue';
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
const customTitleField = (wrapper, index = 0) => wrapper.find(`[data-testid="client-note-custom-title-${index}"]`);
const customContentField = (wrapper, index = 0) => wrapper.find(`[data-testid="client-note-custom-content-${index}"]`);

describe('DocumentClientNoteModal', () => {
  beforeEach(() => {
    mockNotifyError.mockReset();
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    });
  });

  it('opens with the stored notes', () => {
    const wrapper = mountModal({
      subject: 'Entrega lista',
      emailBody: 'Hola Ana, el documento está listo.',
      whatsappMessage: 'Hola Ana, revisa tu correo.',
      customNotes: [{ title: 'Seguimiento', content: 'Llamar el viernes.' }],
    });

    expect(subjectField(wrapper).element.value).toBe('Entrega lista');
    expect(emailField(wrapper).element.value).toBe('Hola Ana, el documento está listo.');
    expect(whatsappField(wrapper).element.value).toBe('Hola Ana, revisa tu correo.');
    expect(customTitleField(wrapper).element.value).toBe('Seguimiento');
    expect(customContentField(wrapper).element.value).toBe('Llamar el viernes.');
  });

  it('applies a trimmed client note', async () => {
    const wrapper = mountModal();
    await subjectField(wrapper).setValue('  Informe listo  ');
    await emailField(wrapper).setValue('  Correo completo  ');
    await whatsappField(wrapper).setValue('  WhatsApp breve  ');
    await wrapper.find('[data-testid="client-note-add-custom"]').trigger('click');
    await customTitleField(wrapper).setValue('  Próximo paso  ');
    await customContentField(wrapper).setValue('  Confirmar la fecha.  ');

    await wrapper.find('[data-testid="document-client-note-modal"]').trigger('submit');

    expect(wrapper.emitted('apply')[0]).toEqual([{
      subject: 'Informe listo',
      emailBody: 'Correo completo',
      whatsappMessage: 'WhatsApp breve',
      customNotes: [{ title: 'Próximo paso', content: 'Confirmar la fecha.' }],
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
    expect(wrapper.get('[role="status"]').text()).toBe('Copiado: correo');
    expect(wrapper.find('[data-testid="client-note-copy-email"]').attributes('aria-label'))
      .toBe('Copiado: correo');
  });

  it('renders client messages as read only', () => {
    const wrapper = mountModal({
      readonly: true,
      subject: 'Asunto guardado',
    });

    expect(subjectField(wrapper).element.disabled).toBe(true);
    expect(emailField(wrapper).element.disabled).toBe(true);
    expect(whatsappField(wrapper).element.disabled).toBe(true);
    expect(wrapper.find('[data-testid="client-note-apply"]').exists()).toBe(false);
  });

  it('renders custom notes as read only', () => {
    const wrapper = mountModal({
      readonly: true,
      customNotes: [{ title: 'Seguimiento', content: 'Llamar el viernes.' }],
    });

    expect(customTitleField(wrapper).element.disabled).toBe(true);
    expect(customContentField(wrapper).element.disabled).toBe(true);
    expect(wrapper.find('[data-testid="client-note-add-custom"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="client-note-custom-delete-0"]').exists()).toBe(false);
  });

  it('requires complete custom notes before applying', async () => {
    const wrapper = mountModal();
    await wrapper.find('[data-testid="client-note-add-custom"]').trigger('click');

    await wrapper.find('[data-testid="document-client-note-modal"]').trigger('submit');

    expect(wrapper.emitted('apply')).toBeFalsy();
    expect(wrapper.find('[data-testid="client-note-custom-title-error-0"]').text())
      .toBe('El título es obligatorio.');
    expect(wrapper.find('[data-testid="client-note-custom-content-error-0"]').text())
      .toBe('El contenido es obligatorio.');
  });

  it('marks the custom note delete action with the shared trash icon', () => {
    const wrapper = mountModal({
      customNotes: [{ title: 'Temporal', content: 'No conservar.' }],
    });

    const remove = wrapper.find('[data-testid="client-note-custom-delete-0"]');
    expect(remove.findComponent(BaseActionIcon).props('action')).toBe('delete');
    expect(remove.text()).toBe('');
  });

  it('deletes a custom note from the draft', async () => {
    const wrapper = mountModal({
      customNotes: [{ title: 'Temporal', content: 'No conservar.' }],
    });

    await wrapper.find('[data-testid="client-note-custom-delete-0"]').trigger('click');
    await wrapper.find('[data-testid="document-client-note-modal"]').trigger('submit');

    expect(wrapper.emitted('apply')[0][0].customNotes).toEqual([]);
  });

  it('copies a custom note content', async () => {
    const wrapper = mountModal({
      customNotes: [{ title: 'Seguimiento', content: 'Llamar el viernes.' }],
    });

    await wrapper.find('[data-testid="client-note-custom-copy-content-0"]').trigger('click');
    await nextTick();

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Llamar el viernes.');
    expect(wrapper.get('[role="status"]').text()).toBe('Copiado: contenido de la nota 1');
  });

  it('copies a custom note title', async () => {
    const wrapper = mountModal({
      customNotes: [{ title: 'Seguimiento', content: 'Llamar el viernes.' }],
    });
    const copyButton = wrapper.find('[data-testid="client-note-custom-copy-title-0"]');
    expect(copyButton.findComponent(BaseActionIcon).props('action')).toBe('copy');

    await copyButton.trigger('click');
    await nextTick();

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Seguimiento');
    expect(wrapper.get('[role="status"]').text()).toBe('Copiado: título de la nota 1');
    expect(copyButton.attributes('aria-label')).toBe('Copiado: título de la nota 1');
  });
});

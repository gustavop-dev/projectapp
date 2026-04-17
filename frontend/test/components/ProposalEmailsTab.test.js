import { mount } from '@vue/test-utils';
import ProposalEmailsTab from '../../components/BusinessProposal/admin/ProposalEmailsTab.vue';
import { usePanelToast } from '../../composables/usePanelToast';

const { toastMsg, clearToast } = usePanelToast();

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const proposalStore = {
  sendComposedEmail: jest.fn(),
  fetchEmailHistory: jest.fn(),
  fetchEmailDefaults: jest.fn(),
};

global.useProposalStore = jest.fn(() => proposalStore);

const baseProposal = {
  id: 42,
  client_name: 'Carlos',
  client_email: 'carlos@example.com',
};

function buildHistoryEntry(overrides = {}) {
  return {
    id: 1,
    subject: 'Seguimiento',
    recipient: 'carlos@example.com',
    status: 'sent',
    sent_at: '2026-04-10T10:00:00Z',
    metadata: {
      greeting: 'Hola Carlos',
      sections: ['Primer bloque'],
      footer: 'Footer',
      attachment_names: ['brief.pdf'],
    },
    ...overrides,
  };
}

function mountTab(props = {}) {
  return mount(ProposalEmailsTab, {
    props: {
      proposal: baseProposal,
      ...props,
    },
  });
}

describe('ProposalEmailsTab', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    proposalStore.sendComposedEmail.mockReset();
    proposalStore.fetchEmailHistory.mockReset();
    proposalStore.fetchEmailDefaults.mockReset();
    proposalStore.fetchEmailDefaults.mockResolvedValue({
      success: true,
      data: {
        greeting: 'Hola Carlos',
        footer: 'Quedamos atentos.',
      },
    });
    proposalStore.fetchEmailHistory.mockResolvedValue({
      success: true,
      data: {
        results: [],
        page: 1,
        has_next: false,
      },
    });
    proposalStore.sendComposedEmail.mockResolvedValue({ success: true });
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    clearToast();
  });

  it('loads defaults and history on mount with the proposal-email base path', async () => {
    mountTab();
    await flushPromises();

    expect(proposalStore.fetchEmailDefaults).toHaveBeenCalledWith(42, 'proposal-email');
    expect(proposalStore.fetchEmailHistory).toHaveBeenCalledWith(42, 1, 'proposal-email');
  });

  it('falls back to empty recipient and generic greeting when the proposal has no client data', async () => {
    proposalStore.fetchEmailDefaults.mockResolvedValueOnce({ success: true, data: {} });
    const wrapper = mountTab({
      proposal: {
        id: 42,
        client_name: '',
        client_email: '',
      },
    });
    await flushPromises();

    const inputs = wrapper.findAll('input');
    expect(inputs[0].element.value).toBe('');
    expect(inputs[2].element.value).toBe('Hola');
    expect(wrapper.findAll('button').find((button) => button.text().includes('Enviar correo')).attributes('disabled')).toBeDefined();
  });

  it('renders the empty history state when there are no entries', async () => {
    const wrapper = mountTab();
    await flushPromises();

    expect(wrapper.text()).toContain('No se han enviado correos desde esta propuesta.');
  });

  it('switches to branded mode and reloads defaults and history', async () => {
    const wrapper = mountTab();
    await flushPromises();

    await wrapper.findAll('button').find((button) => button.text().includes('General')).trigger('click');
    await flushPromises();

    expect(proposalStore.fetchEmailDefaults).toHaveBeenLastCalledWith(42, 'branded-email');
    expect(proposalStore.fetchEmailHistory).toHaveBeenLastCalledWith(42, 1, 'branded-email');
  });

  it('disables the send button until recipient, subject, and one section have content', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const sendButton = wrapper.findAll('button').find((button) => button.text().includes('Enviar correo'));
    expect(sendButton.attributes('disabled')).toBeDefined();

    const inputs = wrapper.findAll('input');
    await inputs[1].setValue('Asunto');
    await wrapper.find('textarea').setValue('Contenido');

    expect(sendButton.attributes('disabled')).toBeUndefined();
  });

  it('adds and removes composer sections from the UI', async () => {
    const wrapper = mountTab();
    await flushPromises();

    await wrapper.findAll('button').find((button) => button.text().includes('Agregar sección')).trigger('click');
    expect(wrapper.text()).toContain('Sección 2');

    await wrapper.findAll('button').find((button) => button.html().includes('M19 7l-.867')).trigger('click');
    expect(wrapper.text()).not.toContain('Sección 2');
  });

  it('shows a validation error for files with disallowed extensions', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const fileInput = wrapper.find('input[type="file"]');
    const file = new File(['bad'], 'malware.exe', { type: 'application/octet-stream' });
    Object.defineProperty(fileInput.element, 'files', {
      configurable: true,
      value: [file],
    });

    await fileInput.trigger('change');

    expect(wrapper.text()).toContain('malware.exe: tipo no permitido');
  });

  it('ignores file change events with no selected files', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const fileInput = wrapper.find('input[type="file"]');
    Object.defineProperty(fileInput.element, 'files', {
      configurable: true,
      value: [],
    });

    await fileInput.trigger('change');

    expect(wrapper.text()).not.toContain('tipo no permitido');
  });

  it('shows a validation error for oversized files', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const fileInput = wrapper.find('input[type="file"]');
    const file = new File(['x'.repeat(10)], 'large.pdf', { type: 'application/pdf' });
    Object.defineProperty(file, 'size', {
      configurable: true,
      value: 16 * 1024 * 1024,
    });
    Object.defineProperty(fileInput.element, 'files', {
      configurable: true,
      value: [file],
    });

    await fileInput.trigger('change');

    expect(wrapper.text()).toContain('large.pdf: excede 15 MB');
  });

  it('adds valid attachments and allows removing them', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const fileInput = wrapper.find('input[type="file"]');
    const file = new File(['pdf'], 'brief.pdf', { type: 'application/pdf' });
    Object.defineProperty(fileInput.element, 'files', {
      configurable: true,
      value: [file],
    });

    await fileInput.trigger('change');
    expect(wrapper.text()).toContain('brief.pdf');

    await wrapper.findAll('button').find((button) => button.html().includes('M6 18L18 6')).trigger('click');
    expect(wrapper.text()).not.toContain('brief.pdf');
  });

  it('sends a composed email and resets the form after a successful response', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const inputs = wrapper.findAll('input');
    await inputs[1].setValue('Seguimiento de propuesta');
    await wrapper.find('textarea').setValue('Primer bloque');

    await wrapper.findAll('button').find((button) => button.text().includes('Enviar correo')).trigger('click');
    await flushPromises();

    const [, formData, basePath] = proposalStore.sendComposedEmail.mock.calls[0];
    expect(basePath).toBe('proposal-email');
    expect(formData.get('recipient_email')).toBe('carlos@example.com');
    expect(formData.get('subject')).toBe('Seguimiento de propuesta');
    expect(formData.get('greeting')).toBe('Hola Carlos');
    expect(formData.get('sections')).toBe(JSON.stringify(['Primer bloque']));
    expect(toastMsg.value).toEqual({ type: 'success', text: 'Correo enviado correctamente.' });

    jest.advanceTimersByTime(5000);
    expect(toastMsg.value).toBeNull();
  });

  it('appends attachments to the form data when sending', async () => {
    const wrapper = mountTab();
    await flushPromises();

    const fileInput = wrapper.find('input[type="file"]');
    const file = new File(['pdf'], 'brief.pdf', { type: 'application/pdf' });
    Object.defineProperty(fileInput.element, 'files', {
      configurable: true,
      value: [file],
    });
    await fileInput.trigger('change');

    const inputs = wrapper.findAll('input');
    await inputs[1].setValue('Seguimiento con adjunto');
    await wrapper.find('textarea').setValue('Primer bloque');
    await wrapper.findAll('button').find((button) => button.text().includes('Enviar correo')).trigger('click');
    await flushPromises();

    const [, formData] = proposalStore.sendComposedEmail.mock.calls[0];
    expect(formData.getAll('attachments')).toHaveLength(1);
    expect(formData.getAll('attachments')[0].name).toBe('brief.pdf');
  });

  it('shows a fallback error when the send request fails', async () => {
    proposalStore.sendComposedEmail.mockResolvedValueOnce({ success: false });
    const wrapper = mountTab();
    await flushPromises();

    const inputs = wrapper.findAll('input');
    await inputs[1].setValue('Seguimiento de propuesta');
    await wrapper.find('textarea').setValue('Primer bloque');

    await wrapper.findAll('button').find((button) => button.text().includes('Enviar correo')).trigger('click');
    await flushPromises();

    expect(toastMsg.value).toEqual({ type: 'error', text: 'Error al enviar el correo. Intenta de nuevo.' });
  });

  it('renders history entries and toggles the expanded detail view', async () => {
    proposalStore.fetchEmailHistory.mockResolvedValueOnce({
      success: true,
      data: {
        results: [buildHistoryEntry()],
        page: 1,
        has_next: false,
      },
    });

    const wrapper = mountTab();
    await flushPromises();

    expect(wrapper.text()).toContain('Seguimiento');
    await wrapper.findAll('button').find((button) => button.text().includes('carlos@example.com')).trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('Primer bloque');
    expect(wrapper.text()).toContain('brief.pdf');
  });

  it('collapses an expanded history entry on the second toggle', async () => {
    proposalStore.fetchEmailHistory.mockResolvedValueOnce({
      success: true,
      data: {
        results: [buildHistoryEntry()],
        page: 1,
        has_next: false,
      },
    });

    const wrapper = mountTab();
    await flushPromises();

    const historyButton = wrapper.findAll('button').find((button) => button.text().includes('carlos@example.com'));
    await historyButton.trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('Primer bloque');

    await historyButton.trigger('click');
    await flushPromises();
    expect(wrapper.text()).not.toContain('Primer bloque');
  });

  it('renders unknown history status values and blank dates without formatting them', async () => {
    proposalStore.fetchEmailHistory.mockResolvedValueOnce({
      success: true,
      data: {
        results: [
          buildHistoryEntry({
            id: 2,
            status: 'queued',
            sent_at: null,
          }),
        ],
        page: 1,
        has_next: false,
      },
    });

    const wrapper = mountTab();
    await flushPromises();

    expect(wrapper.text()).toContain('queued');
    expect(wrapper.text()).toContain('carlos@example.com');
  });

  it('loads the next history page when the load more button is clicked', async () => {
    proposalStore.fetchEmailHistory
      .mockResolvedValueOnce({
        success: true,
        data: {
          results: [buildHistoryEntry({ id: 1, subject: 'Primero' })],
          page: 1,
          has_next: true,
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          results: [buildHistoryEntry({ id: 2, subject: 'Segundo' })],
          page: 2,
          has_next: false,
        },
      });

    const wrapper = mountTab();
    await flushPromises();
    await wrapper.findAll('button').find((button) => button.text().includes('Cargar más')).trigger('click');
    await flushPromises();

    expect(proposalStore.fetchEmailHistory).toHaveBeenLastCalledWith(42, 2, 'proposal-email');
    expect(wrapper.text()).toContain('Segundo');
  });
});

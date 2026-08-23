const mockEmailStore = {
  copyRecipients: [],
  copyFamilies: [
    { value: 'proposals', label: 'Propuestas' },
    { value: 'collections', label: 'Cuentas de cobro' },
  ],
  isLoadingCopyRecipients: false,
  isSavingCopyRecipient: false,
  fetchCopyRecipients: jest.fn(),
  createCopyRecipient: jest.fn(),
  updateCopyRecipient: jest.fn(),
  deleteCopyRecipient: jest.fn(),
};

const mockNotify = { success: jest.fn(), error: jest.fn() };

jest.mock('../../../stores/emails', () => ({
  useEmailStore: () => mockEmailStore,
}));

jest.mock('../../../composables/usePanelNotify', () => ({
  usePanelNotify: () => mockNotify,
}));

import { flushPromises, mount } from '@vue/test-utils';
import ClientEmailCopySettings from '../../../components/emails/ClientEmailCopySettings.vue';
import BaseButton from '../../../components/base/BaseButton.vue';
import BaseFormField from '../../../components/base/BaseFormField.vue';
import BaseInput from '../../../components/base/BaseInput.vue';

function mountSettings() {
  return mount(ClientEmailCopySettings, {
    global: { components: { BaseButton, BaseFormField, BaseInput } },
  });
}

describe('ClientEmailCopySettings', () => {
  beforeEach(() => {
    mockEmailStore.copyRecipients = [{
      id: 8,
      email: 'audit@example.com',
      is_active: true,
      families: ['proposals'],
    }];
    mockEmailStore.fetchCopyRecipients.mockReset()
      .mockResolvedValue({ success: true });
    mockEmailStore.createCopyRecipient.mockReset()
      .mockResolvedValue({ success: true });
    mockEmailStore.updateCopyRecipient.mockReset()
      .mockResolvedValue({ success: true });
    mockEmailStore.deleteCopyRecipient.mockReset()
      .mockResolvedValue({ success: true });
    mockNotify.success.mockReset();
    mockNotify.error.mockReset();
  });

  it('shows the configured BCC recipient and volume warning', async () => {
    const wrapper = mountSettings();
    await flushPromises();

    expect(mockEmailStore.fetchCopyRecipients).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('audit@example.com');
    expect(wrapper.text()).toContain('volumen SMTP');
    expect(wrapper.text()).toContain('BCC');
  });

  it('creates a recipient with every selected family', async () => {
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.get('[data-testid="client-copy-email"]')
      .setValue('new@example.com');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mockEmailStore.createCopyRecipient).toHaveBeenCalledWith({
      email: 'new@example.com',
      is_active: true,
      families: ['proposals', 'collections'],
    });
  });

  it('persists a changed family selection', async () => {
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.get('[data-testid="client-copy-8-collections"]')
      .setValue(true);
    await wrapper.get('[data-testid="client-copy-save-8"]').trigger('click');
    await flushPromises();

    expect(mockEmailStore.updateCopyRecipient).toHaveBeenCalledWith(8, {
      families: ['proposals', 'collections'],
    });
  });

  it('reports backend validation details on create', async () => {
    mockEmailStore.createCopyRecipient.mockResolvedValue({
      success: false,
      error: { email: ['Ese correo ya está en la lista.'] },
    });
    const wrapper = mountSettings();
    await flushPromises();

    await wrapper.get('[data-testid="client-copy-email"]')
      .setValue('audit@example.com');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mockNotify.error).toHaveBeenCalledWith({
      title: 'No se pudo agregar',
      detail: 'Ese correo ya está en la lista.',
    });
  });
});

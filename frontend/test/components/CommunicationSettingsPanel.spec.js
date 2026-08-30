const preferences = () => ({
  navigation_mode: 'project',
  thread_order: 'recent',
  page_size: 20,
  default_channel: 'whatsapp',
  show_manual_help: true,
  navigation_width: 288,
});

const mockStore = {
  preferences: preferences(),
  preferenceError: null,
  isPreferenceSaving: false,
  updatePreferences: jest.fn(),
  resetPreferences: jest.fn(),
};
const mockNotify = { success: jest.fn() };

jest.mock('../../stores/communications', () => ({
  useCommunicationsStore: () => mockStore,
}));
jest.mock('../../composables/usePanelNotify', () => ({
  usePanelNotify: () => mockNotify,
}));
jest.mock('../../composables/useUnsavedGuard', () => ({
  useUnsavedGuard: () => ({
    confirmState: { open: false },
    handleConfirmed: jest.fn(),
    handleSecondaryAction: jest.fn(),
    handleCancelled: jest.fn(),
  }),
}));

import { flushPromises, mount } from '@vue/test-utils';
import CommunicationSettingsPanel from '../../components/communications/CommunicationSettingsPanel.vue';
import BaseAlert from '../../components/base/BaseAlert.vue';
import BaseFormField from '../../components/base/BaseFormField.vue';
import BaseSegmented from '../../components/base/BaseSegmented.vue';
import BaseToggle from '../../components/base/BaseToggle.vue';

const ViewSettingsPanelStub = {
  emits: ['reset'],
  template: `
    <div data-testid="view-settings-panel">
      <button data-testid="view-settings-reset" @click="$emit('reset')">Restablecer pestañas</button>
    </div>
  `,
};

const ConfirmModalStub = {
  props: ['modelValue', 'title', 'confirmText'],
  emits: ['update:modelValue', 'confirm'],
  template: `
    <div v-if="modelValue" role="dialog">
      <span>{{ title }}</span>
      <button
        data-testid="confirm-modal-confirm"
        @click="$emit('confirm'); $emit('update:modelValue', false)"
      >{{ confirmText }}</button>
    </div>
  `,
};

function mountPanel() {
  return mount(CommunicationSettingsPanel, {
    global: {
      components: {
        BaseAlert,
        BaseFormField,
        BaseSegmented,
        BaseToggle,
      },
      stubs: {
        ConfirmModal: ConfirmModalStub,
        NuxtLink: { template: '<a><slot /></a>' },
        ViewSettingsPanel: ViewSettingsPanelStub,
      },
    },
  });
}

describe('CommunicationSettingsPanel', () => {
  beforeEach(() => {
    mockStore.preferences = preferences();
    mockStore.preferenceError = null;
    mockStore.isPreferenceSaving = false;
    mockStore.updatePreferences.mockReset().mockImplementation(async (payload) => ({
      success: true,
      data: { ...preferences(), ...payload },
    }));
    mockStore.resetPreferences.mockReset().mockResolvedValue({
      success: true,
      data: preferences(),
    });
    mockNotify.success.mockReset();
  });

  it('shows every safe preference group', () => {
    const wrapper = mountPanel();

    expect(wrapper.text()).toContain('Organización del listado');
    expect(wrapper.text()).toContain('Registro de mensajes');
    expect(wrapper.get('[data-testid="view-settings-panel"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain('Automatizaciones');
  });

  it('saves only a changed channel', async () => {
    const wrapper = mountPanel();
    const channel = wrapper.get('[data-testid="communication-settings-default-channel"]');
    await channel.findAll('[role="tab"]')[1].trigger('click');

    await wrapper.get('[data-testid="communication-settings-save"]').trigger('click');
    await flushPromises();

    expect(mockStore.updatePreferences).toHaveBeenCalledWith({ default_channel: 'email' });
    expect(mockNotify.success).toHaveBeenCalledWith({ title: 'Configuraciones guardadas' });
  });

  it('keeps a failed edit available for retry', async () => {
    mockStore.updatePreferences.mockResolvedValue({ success: false });
    const wrapper = mountPanel();
    const channel = wrapper.get('[data-testid="communication-settings-default-channel"]');
    await channel.findAll('[role="tab"]')[1].trigger('click');

    await wrapper.get('[data-testid="communication-settings-save"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="communication-settings-unsaved"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="communication-settings-save"]').attributes('disabled'))
      .toBeUndefined();
  });

  it('asks before closing a dirty panel', async () => {
    const wrapper = mountPanel();
    const channel = wrapper.get('[data-testid="communication-settings-default-channel"]');
    await channel.findAll('[role="tab"]')[1].trigger('click');

    await wrapper.get('[data-testid="communication-settings-back"]').trigger('click');

    expect(wrapper.get('[role="dialog"]').text()).toContain('Descartar cambios');
    expect(wrapper.emitted('close')).toBeUndefined();
  });

  it('restores preference defaults after confirmation', async () => {
    const wrapper = mountPanel();
    await wrapper.get('[data-testid="communication-settings-reset"]').trigger('click');

    await wrapper.get('[data-testid="confirm-modal-confirm"]').trigger('click');
    await flushPromises();

    expect(mockStore.resetPreferences).toHaveBeenCalledTimes(1);
    expect(mockNotify.success).toHaveBeenCalledWith({ title: 'Preferencias restablecidas' });
  });
});

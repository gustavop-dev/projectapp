import { mount } from '@vue/test-utils';

import RecurringActionsModal from '~/components/accounting/RecurringActionsModal.vue';

const RECORD = {
  id: 42,
  name: 'Figma equipo',
  price: '270000.00',
  currency: 'COP',
  frequency_label: 'Trimestral',
  is_active: true,
  is_archived: false,
  reminders_effectively_muted: false,
};

function mountModal(record = RECORD) {
  return mount(RecurringActionsModal, {
    props: { open: true, record },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'kind', 'size'],
          emits: ['close'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseButton: {
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
        BaseActionIcon: true,
      },
    },
  });
}

function actionIds(wrapper) {
  return wrapper.findAll('[data-testid^="recurring-action-"]')
    .map((node) => node.attributes('data-testid'))
    .map((id) => id.replace(`recurring-action-`, '').replace(`-${RECORD.id}`, ''));
}

describe('RecurringActionsModal', () => {
  it('offers the current lifecycle menu for an active payment', () => {
    const wrapper = mountModal();

    expect(actionIds(wrapper)).toEqual([
      'edit', 'duplicate', 'deactivate', 'mute', 'archive',
    ]);
  });

  it('offers activation for an inactive payment', () => {
    const wrapper = mountModal({ ...RECORD, is_active: false });

    expect(actionIds(wrapper)).toContain('activate');
    expect(actionIds(wrapper)).not.toContain('deactivate');
  });

  it('offers reminder reactivation for a muted payment', () => {
    const wrapper = mountModal({ ...RECORD, reminders_effectively_muted: true });

    expect(actionIds(wrapper)).toContain('unmute');
    expect(actionIds(wrapper)).not.toContain('mute');
  });

  it('limits archived payments to safe archive operations', () => {
    const wrapper = mountModal({
      ...RECORD,
      is_active: false,
      is_archived: true,
    });

    expect(actionIds(wrapper)).toEqual(['edit', 'duplicate', 'restore', 'delete']);
  });

  it('routes the chosen action to the page', async () => {
    const wrapper = mountModal();

    await wrapper.get('[data-testid="recurring-action-duplicate-42"]').trigger('click');

    expect(wrapper.emitted('duplicate')[0]).toEqual([RECORD]);
    expect(wrapper.emitted('close')).toHaveLength(1);
  });
});

import { mount } from '@vue/test-utils';

import RecurringRowActionsButton from '~/components/accounting/RecurringRowActionsButton.vue';

const BaseActionButtonStub = {
  props: ['label', 'statusLabel', 'disabled', 'loading'],
  emits: ['click'],
  template: `
    <button
      :aria-label="statusLabel || label"
      :disabled="disabled"
      @click="$emit('click', $event)"
    />
  `,
};

function mountButton(props = {}) {
  return mount(RecurringRowActionsButton, {
    props: { row: { id: 42, name: 'Figma equipo' }, ...props },
    global: { stubs: { BaseActionButton: BaseActionButtonStub } },
  });
}

describe('RecurringRowActionsButton', () => {
  it('opens the menu for its own payment', async () => {
    const wrapper = mountButton();

    await wrapper.get('[data-testid="recurring-actions-42"]').trigger('click');

    expect(wrapper.emitted('open')[0]).toEqual([{ id: 42, name: 'Figma equipo' }]);
  });

  it('names the payment while idle', () => {
    const button = mountButton().get('[data-testid="recurring-actions-42"]');

    expect(button.attributes('aria-label')).toBe('Acciones de Figma equipo');
    expect(button.attributes('disabled')).toBeUndefined();
  });

  it('blocks a second action while preparing a duplicate', async () => {
    const wrapper = mountButton({ busy: true });
    const button = wrapper.get('[data-testid="recurring-actions-42"]');

    expect(button.attributes('aria-label')).toBe('Preparando duplicado');
    expect(button.attributes('disabled')).toBeDefined();
    await button.trigger('click');
    expect(wrapper.emitted('open')).toBeUndefined();
  });
});

/**
 * Tests for IncomeRowActionsButton: the kebab both income tables render.
 * The behaviour worth pinning is the busy state — duplicating fetches its
 * prefill before anything can open, and this button is the only thing on
 * screen that says so once the action menu has closed.
 */
import { mount } from '@vue/test-utils';
import IncomeRowActionsButton from '../../../components/accounting/IncomeRowActionsButton.vue';

const BaseButtonStub = {
  props: ['variant', 'size', 'iconOnly', 'disabled', 'loading', 'type'],
  emits: ['click'],
  template:
    '<button :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
};

function mountButton(props = {}) {
  return mount(IncomeRowActionsButton, {
    props: { row: { id: 42 }, ...props },
    global: { stubs: { BaseButton: BaseButtonStub } },
  });
}

describe('IncomeRowActionsButton', () => {
  it('opens the menu for its own row', async () => {
    const wrapper = mountButton();

    await wrapper.get('[data-testid="income-actions-42"]').trigger('click');

    expect(wrapper.emitted('open')[0]).toEqual([{ id: 42 }]);
  });

  it('announces itself as the actions button while idle', () => {
    const wrapper = mountButton();
    const button = wrapper.get('[data-testid="income-actions-42"]');

    expect(button.attributes('aria-label')).toBe('Acciones de ingreso 42');
    expect(button.attributes('disabled')).toBeUndefined();
  });

  it('says it is preparing the duplicate and refuses a second click while busy', async () => {
    const wrapper = mountButton({ busy: true });
    const button = wrapper.get('[data-testid="income-actions-42"]');

    expect(button.attributes('aria-label')).toBe('Preparando duplicado');
    expect(button.attributes('disabled')).toBeDefined();

    await button.trigger('click');

    expect(wrapper.emitted('open')).toBeUndefined();
  });
});

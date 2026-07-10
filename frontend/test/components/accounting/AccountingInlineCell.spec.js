/**
 * Tests for AccountingInlineCell.
 *
 * Covers: display by default, dblclick opens the editor, Enter saves the
 * changed value, unchanged blur emits nothing, Esc cancels, money type
 * emits numbers.
 */
import { mount } from '@vue/test-utils';
import AccountingInlineCell from '../../../components/accounting/AccountingInlineCell.vue';

function mountCell(props = {}) {
  return mount(AccountingInlineCell, {
    props: { value: 'Acme', ...props },
  });
}

async function openEditor(wrapper) {
  await wrapper.find('[data-testid="inline-cell-display"]').trigger('dblclick');
  return wrapper.find('input');
}

describe('AccountingInlineCell', () => {
  it('renders the value (or slot) as plain display', () => {
    const wrapper = mountCell();

    expect(wrapper.find('[data-testid="inline-cell-display"]').text()).toBe('Acme');
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('opens an input on double click', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    expect(input.exists()).toBe(true);
    expect(input.element.value).toBe('Acme');
  });

  it('emits save with the trimmed value on Enter', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    await input.setValue('  Acme Corp  ');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([['Acme Corp']]);
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('emits nothing when the value did not change on blur', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    await input.trigger('blur');

    expect(wrapper.emitted('save')).toBeUndefined();
  });

  it('cancels on Esc without saving', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    await input.setValue('Otro');
    await input.trigger('keydown.esc');

    expect(wrapper.emitted('save')).toBeUndefined();
    expect(wrapper.find('[data-testid="inline-cell-display"]').exists()).toBe(true);
  });

  it('money type edits through the currency input and emits a number', async () => {
    const wrapper = mountCell({ type: 'money', value: '91667.00' });
    const input = await openEditor(wrapper);

    expect(input.element.value).toBe('91.667');

    await input.setValue('120000');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[120000]]);
  });

  it('money type does not emit when the amount is unchanged', async () => {
    const wrapper = mountCell({ type: 'money', value: '91667.00' });
    const input = await openEditor(wrapper);

    await input.trigger('blur');

    expect(wrapper.emitted('save')).toBeUndefined();
  });
});

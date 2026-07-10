/**
 * Tests for AccountingStatusSelect.
 *
 * Covers: rendered state, boolean emit on change, snap-back (select keeps
 * reflecting the prop), no emit when re-selecting the same state, spinner
 * while updating.
 */
import { mount } from '@vue/test-utils';
import AccountingStatusSelect from '../../../components/accounting/AccountingStatusSelect.vue';

function mountSelect(props = {}) {
  return mount(AccountingStatusSelect, {
    props: { value: true, ...props },
  });
}

describe('AccountingStatusSelect', () => {
  it('reflects the current boolean state', () => {
    const active = mountSelect({ value: true });
    const inactive = mountSelect({ value: false });

    expect(active.find('select').element.value).toBe('true');
    expect(inactive.find('select').element.value).toBe('false');
  });

  it('emits the chosen boolean and snaps the select back', async () => {
    const wrapper = mountSelect({ value: true });
    const select = wrapper.find('select');

    await select.setValue('false');

    expect(wrapper.emitted('change')).toEqual([[false]]);
    // Snap-back: the select reflects state, not intent.
    expect(select.element.value).toBe('true');
  });

  it('does not emit when re-selecting the current state', async () => {
    const wrapper = mountSelect({ value: true });

    await wrapper.find('select').setValue('true');

    expect(wrapper.emitted('change')).toBeUndefined();
  });

  it('disables the select and shows the spinner while updating', () => {
    const wrapper = mountSelect({ updating: true });

    expect(wrapper.find('select').attributes('disabled')).toBeDefined();
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true);
  });
});

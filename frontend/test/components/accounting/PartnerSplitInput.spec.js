import { mount } from '@vue/test-utils';
import PartnerSplitInput from '~/components/accounting/PartnerSplitInput.vue';

function mountInput(props = {}) {
  return mount(PartnerSplitInput, {
    props: { total: '', gustavoAmount: '', carlosAmount: '', ...props },
  });
}

const totalInput = (wrapper) => wrapper.find('[data-testid="partner-split-total"]');
const gustavoInput = (wrapper) => wrapper.find('[data-testid="partner-split-gustavo"]');
const carlosInput = (wrapper) => wrapper.find('[data-testid="partner-split-carlos"]');
const autoToggle = (wrapper) => wrapper.find('[data-testid="partner-split-auto"]');

describe('PartnerSplitInput', () => {
  it('auto mode splits an even total 50/50', async () => {
    const wrapper = mountInput();

    await totalInput(wrapper).setValue('1000');

    expect(wrapper.emitted('update:total')[0]).toEqual(['1000']);
    expect(wrapper.emitted('update:gustavoAmount')[0]).toEqual([500]);
    expect(wrapper.emitted('update:carlosAmount')[0]).toEqual([500]);
  });

  it('auto mode splits an odd total so partner amounts sum exactly', async () => {
    const wrapper = mountInput();

    await totalInput(wrapper).setValue('101');

    expect(wrapper.emitted('update:gustavoAmount')[0]).toEqual([50]);
    expect(wrapper.emitted('update:carlosAmount')[0]).toEqual([51]);
  });

  it('disables partner inputs while auto mode is on', () => {
    const wrapper = mountInput({ total: 100 });

    expect(gustavoInput(wrapper).attributes('disabled')).toBeDefined();
    expect(carlosInput(wrapper).attributes('disabled')).toBeDefined();
  });

  it('manual mode enables partner inputs and emits raw partner edits', async () => {
    const wrapper = mountInput({ total: 100, gustavoAmount: 50, carlosAmount: 50 });

    await autoToggle(wrapper).trigger('click');

    expect(gustavoInput(wrapper).attributes('disabled')).toBeUndefined();

    await gustavoInput(wrapper).setValue('70');

    expect(wrapper.emitted('update:gustavoAmount')).toBeTruthy();
    expect(wrapper.emitted('update:gustavoAmount').at(-1)).toEqual(['70']);
    // Editing one partner never auto-adjusts the other.
    expect(wrapper.emitted('update:carlosAmount')).toBeFalsy();
  });

  it('shows a warning in manual mode when partner sum exceeds the total', async () => {
    const wrapper = mountInput({ total: 100, gustavoAmount: 80, carlosAmount: 40 });

    // Auto ON: warning hidden even if the sum exceeds the total.
    expect(wrapper.find('[data-testid="partner-split-warning"]').exists()).toBe(false);

    await autoToggle(wrapper).trigger('click');

    expect(wrapper.find('[data-testid="partner-split-warning"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('La suma de socios supera el total');
  });

  it('re-enabling auto recomputes the split from the total', async () => {
    const wrapper = mountInput({ total: 101, gustavoAmount: 80, carlosAmount: 40 });

    await autoToggle(wrapper).trigger('click'); // off
    await autoToggle(wrapper).trigger('click'); // back on

    expect(wrapper.emitted('update:gustavoAmount').at(-1)).toEqual([50]);
    expect(wrapper.emitted('update:carlosAmount').at(-1)).toEqual([51]);
  });

  it('shows the ProjectApp pocket remainder when total exceeds the partner sum', () => {
    const wrapper = mountInput({ total: 1000, gustavoAmount: 300, carlosAmount: 300 });

    const remainder = wrapper.find('[data-testid="partner-split-remainder"]');
    expect(remainder.exists()).toBe(true);
    expect(remainder.text()).toContain('Bolsillo ProjectApp:');
  });

  it('hides the remainder line when nothing is left over', () => {
    const wrapper = mountInput({ total: 1000, gustavoAmount: 500, carlosAmount: 500 });

    expect(wrapper.find('[data-testid="partner-split-remainder"]').exists()).toBe(false);
  });
});

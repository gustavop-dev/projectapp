import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import ProposalFilterRangeDropdown from '../../components/proposals/ProposalFilterRangeDropdown.vue';

let outsideHandler = null;

jest.mock('@vueuse/core', () => ({
  onClickOutside: jest.fn((_, handler) => {
    outsideHandler = handler;
  }),
}));

function mountDropdown(props = {}) {
  outsideHandler = null;
  return mount(ProposalFilterRangeDropdown, {
    props: {
      label: 'Inversión',
      type: 'number',
      minValue: null,
      maxValue: null,
      ...props,
    },
  });
}

describe('ProposalFilterRangeDropdown', () => {
  it('opens the range panel when the trigger is clicked', async () => {
    const wrapper = mountDropdown();

    await wrapper.get('button').trigger('click');

    expect(wrapper.findAll('input')).toHaveLength(2);
    expect(wrapper.text()).toContain('Inversión');
  });

  it('renders the icon and active badge when any range value is set', () => {
    const wrapper = mountDropdown({
      icon: '💰',
      minValue: 100,
    });

    expect(wrapper.text()).toContain('💰');
    expect(wrapper.text()).toContain('✓');
  });

  it('emits parsed numeric min and max values', async () => {
    const wrapper = mountDropdown();

    await wrapper.get('button').trigger('click');
    const inputs = wrapper.findAll('input');
    await inputs[0].setValue('1500');
    await inputs[0].trigger('change');
    await inputs[1].setValue('3200');
    await inputs[1].trigger('change');

    expect(wrapper.emitted('update:minValue')).toContainEqual([1500]);
    expect(wrapper.emitted('update:maxValue')).toContainEqual([3200]);
  });

  it('emits raw date strings for date inputs', async () => {
    const wrapper = mountDropdown({
      label: 'Creación',
      type: 'date',
      unit: '/ 10',
    });

    await wrapper.get('button').trigger('click');
    const inputs = wrapper.findAll('input');
    await inputs[0].setValue('2026-04-01');
    await inputs[0].trigger('change');
    await inputs[1].setValue('2026-04-30');
    await inputs[1].trigger('change');

    expect(wrapper.emitted('update:minValue')).toContainEqual(['2026-04-01']);
    expect(wrapper.emitted('update:maxValue')).toContainEqual(['2026-04-30']);
    expect(wrapper.text()).toContain('(/ 10)');
  });

  it('emits null when an input is cleared', async () => {
    const wrapper = mountDropdown({ minValue: 10, maxValue: 20 });

    await wrapper.get('button').trigger('click');
    const inputs = wrapper.findAll('input');
    await inputs[0].setValue('');
    await inputs[0].trigger('change');
    await inputs[1].setValue('');
    await inputs[1].trigger('change');

    expect(wrapper.emitted('update:minValue')).toContainEqual([null]);
    expect(wrapper.emitted('update:maxValue')).toContainEqual([null]);
  });

  it('clears both values from the footer action', async () => {
    const wrapper = mountDropdown({ minValue: 100, maxValue: 200 });

    await wrapper.get('button').trigger('click');
    await wrapper.findAll('button')[1].trigger('click');

    expect(wrapper.emitted('update:minValue')).toEqual([[null]]);
    expect(wrapper.emitted('update:maxValue')).toEqual([[null]]);
  });

  it('closes the range panel when the click-outside handler runs', async () => {
    const wrapper = mountDropdown();

    await wrapper.get('button').trigger('click');
    expect(wrapper.findAll('input')).toHaveLength(2);

    outsideHandler();
    await nextTick();

    expect(wrapper.findAll('input')).toHaveLength(0);
  });
});

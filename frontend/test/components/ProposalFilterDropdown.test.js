import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import ProposalFilterDropdown from '../../components/proposals/ProposalFilterDropdown.vue';

let outsideHandler = null;

jest.mock('@vueuse/core', () => ({
  onClickOutside: jest.fn((_, handler) => {
    outsideHandler = handler;
  }),
}));

const options = [
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviada' },
];

function mountDropdown(props = {}) {
  outsideHandler = null;
  return mount(ProposalFilterDropdown, {
    props: {
      label: 'Estado',
      options,
      modelValue: [],
      ...props,
    },
  });
}

describe('ProposalFilterDropdown', () => {
  it('opens the option list when the trigger is clicked', async () => {
    const wrapper = mountDropdown();

    await wrapper.get('button').trigger('click');

    expect(wrapper.text()).toContain('Borrador');
    expect(wrapper.text()).toContain('Enviada');
  });

  it('renders the icon and active count badge when values are selected', () => {
    const wrapper = mountDropdown({
      icon: '📌',
      modelValue: ['draft', 'sent'],
    });

    expect(wrapper.text()).toContain('📌');
    expect(wrapper.text()).toContain('2');
  });

  it('emits the selected value when an unchecked option is toggled', async () => {
    const wrapper = mountDropdown({ modelValue: ['draft'] });

    await wrapper.get('button').trigger('click');
    await wrapper.findAll('input[type="checkbox"]')[1].setValue(true);

    expect(wrapper.emitted('update:modelValue')).toEqual([[['draft', 'sent']]]);
  });

  it('emits the filtered value list when a checked option is toggled off', async () => {
    const wrapper = mountDropdown({ modelValue: ['draft'] });

    await wrapper.get('button').trigger('click');
    await wrapper.find('input[type="checkbox"]').setValue(false);

    expect(wrapper.emitted('update:modelValue')).toEqual([[[]]]);
  });

  it('clears all selected values from the footer action', async () => {
    const wrapper = mountDropdown({ modelValue: ['draft'] });

    await wrapper.get('button').trigger('click');
    await wrapper.findAll('button')[1].trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[[]]]);
  });

  it('closes the option list when the click-outside handler runs', async () => {
    const wrapper = mountDropdown();

    await wrapper.get('button').trigger('click');
    expect(wrapper.text()).toContain('Borrador');

    outsideHandler();
    await nextTick();

    expect(wrapper.text()).not.toContain('Borrador');
  });
});

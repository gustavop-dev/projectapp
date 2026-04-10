import { mount } from '@vue/test-utils';
import ClientFilterPanel from '../../components/clients/ClientFilterPanel.vue';

const emptyFilters = {
  lastStatuses: [], projectTypes: [], marketTypes: [],
  totalProposalsMin: null, totalProposalsMax: null,
  acceptedMin: null, acceptedMax: null,
  lastActivityAfter: null, lastActivityBefore: null,
};

function mountPanel(props = {}) {
  return mount(ClientFilterPanel, {
    props: { modelValue: emptyFilters, isOpen: true, filterCount: 0, ...props },
    global: { stubs: { ProposalFilterDropdown: true, ProposalFilterRangeDropdown: true } },
  });
}

describe('ClientFilterPanel', () => {
  it('shows the filter panel content when isOpen is true', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.find('div').isVisible()).toBe(true);
  });

  it('hides the filter panel content when isOpen is false', () => {
    const wrapper = mountPanel({ isOpen: false });

    expect(wrapper.find('div').isVisible()).toBe(false);
  });

  it('shows "Limpiar todo" button when filterCount is greater than zero', () => {
    const wrapper = mountPanel({ filterCount: 2 });

    expect(wrapper.text()).toContain('Limpiar todo');
  });

  it('hides "Limpiar todo" button when filterCount is zero', () => {
    const wrapper = mountPanel({ filterCount: 0 });

    expect(wrapper.text()).not.toContain('Limpiar todo');
  });

  it('emits reset when the "Limpiar todo" button is clicked', async () => {
    const wrapper = mountPanel({ filterCount: 1 });

    await wrapper.find('button').trigger('click');

    expect(wrapper.emitted('reset')).toHaveLength(1);
  });

  it('shows active filter chips when filters are applied', () => {
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, lastStatuses: ['draft'] },
    });

    expect(wrapper.text()).toContain('Estado:');
  });
});

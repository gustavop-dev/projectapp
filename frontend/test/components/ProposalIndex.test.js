import { mount } from '@vue/test-utils';
import ProposalIndex from '../../components/BusinessProposal/ProposalIndex.vue';

const defaultSections = [
  { id: 'intro', title: 'Introducción' },
  { id: 'budget', title: 'Presupuesto' },
];

function mountIndex(props = {}) {
  return mount(ProposalIndex, {
    props: {
      sections: defaultSections,
      currentIndex: 0,
      visitedPanelIds: new Set(),
      viewMode: '',
      language: 'es',
      ...props,
    },
    global: { stubs: { Transition: true } },
  });
}

describe('ProposalIndex', () => {
  it('renders section titles from the sections prop', () => {
    const wrapper = mountIndex();

    expect(wrapper.text()).toContain('Introducción');
    expect(wrapper.text()).toContain('Presupuesto');
  });

  it('emits navigate with the section index when a section button is clicked', async () => {
    const wrapper = mountIndex();

    const sectionButtons = wrapper.find('[data-testid="index-panel"]').findAll('ul button');
    await sectionButtons[1].trigger('click');

    expect(wrapper.emitted('navigate')).toEqual([[1]]);
  });

  it('emits backToGateway when the back-to-gateway button is clicked', async () => {
    const wrapper = mountIndex();

    await wrapper.find('[data-testid="back-to-gateway-btn"]').trigger('click');

    expect(wrapper.emitted('backToGateway')).toHaveLength(1);
  });

  it('shows the switch-to-detailed button when viewMode is executive', () => {
    const wrapper = mountIndex({ viewMode: 'executive' });

    expect(wrapper.find('[data-testid="switch-to-detailed-btn"]').exists()).toBe(true);
  });

  it('hides the switch-to-detailed button when viewMode is not executive', () => {
    const wrapper = mountIndex({ viewMode: '' });

    expect(wrapper.find('[data-testid="switch-to-detailed-btn"]').exists()).toBe(false);
  });

  it('emits switchToDetailed when the switch-to-detailed button is clicked', async () => {
    const wrapper = mountIndex({ viewMode: 'executive' });

    await wrapper.find('[data-testid="switch-to-detailed-btn"]').trigger('click');

    expect(wrapper.emitted('switchToDetailed')).toHaveLength(1);
  });
});

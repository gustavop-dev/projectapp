import { mount } from '@vue/test-utils';
import SectionCounter from '../../components/BusinessProposal/SectionCounter.vue';

function mountCounter(props = {}) {
  return mount(SectionCounter, {
    props: { current: 1, total: 5, ...props },
  });
}

describe('SectionCounter', () => {
  it('renders the current section number', () => {
    const wrapper = mountCounter({ current: 3, total: 8 });

    expect(wrapper.get('[data-testid="section-counter"]').text()).toContain('3');
  });

  it('renders the total section count', () => {
    const wrapper = mountCounter({ current: 1, total: 8 });

    expect(wrapper.get('[data-testid="section-counter"]').text()).toContain('8');
  });
});

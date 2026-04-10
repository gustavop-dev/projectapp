import { mount } from '@vue/test-utils';
import InvestmentDetailedTeaser from '../../components/BusinessProposal/InvestmentDetailedTeaser.vue';

function mountTeaser(props = {}) {
  return mount(InvestmentDetailedTeaser, {
    props: { language: 'es', ...props },
  });
}

describe('InvestmentDetailedTeaser', () => {
  it('renders the Spanish title by default', () => {
    const wrapper = mountTeaser();

    expect(wrapper.text()).toContain('Hay más por descubrir');
  });

  it('renders the English title when language is "en"', () => {
    const wrapper = mountTeaser({ language: 'en' });

    expect(wrapper.text()).toContain("There's more to discover");
  });

  it('renders the CTA button', () => {
    const wrapper = mountTeaser();

    expect(wrapper.find('.switch-to-detailed-btn').exists()).toBe(true);
  });

  it('emits switchToDetailed when the CTA button is clicked', async () => {
    const wrapper = mountTeaser();

    await wrapper.get('.switch-to-detailed-btn').trigger('click');

    expect(wrapper.emitted('switchToDetailed')).toHaveLength(1);
  });
});

import { mount } from '@vue/test-utils';
import ProposalViewGateway from '../../components/BusinessProposal/ProposalViewGateway.vue';

function mountGateway(props = {}) {
  return mount(ProposalViewGateway, {
    props: { language: 'es', clientName: '', showTechnical: false, ...props },
  });
}

describe('ProposalViewGateway', () => {
  it('renders the Spanish heading text by default', () => {
    const wrapper = mountGateway();

    expect(wrapper.text()).toContain('¿Cómo prefieres explorar esta propuesta?');
  });

  it('emits select with "executive" when the executive card is clicked', async () => {
    const wrapper = mountGateway();

    await wrapper.findAll('.gateway-card')[0].trigger('click');

    expect(wrapper.emitted('select')).toEqual([['executive']]);
  });

  it('emits select with "detailed" when the detailed card is clicked', async () => {
    const wrapper = mountGateway();

    await wrapper.findAll('.gateway-card')[1].trigger('click');

    expect(wrapper.emitted('select')).toEqual([['detailed']]);
  });

  it('does not render the technical card when showTechnical is false', () => {
    const wrapper = mountGateway({ showTechnical: false });

    expect(wrapper.find('[data-testid="gateway-technical-card"]').exists()).toBe(false);
  });

  it('renders the technical card when showTechnical is true', () => {
    const wrapper = mountGateway({ showTechnical: true });

    expect(wrapper.find('[data-testid="gateway-technical-card"]').exists()).toBe(true);
  });

  it('emits select with "technical" when the technical card is clicked', async () => {
    const wrapper = mountGateway({ showTechnical: true });

    await wrapper.find('[data-testid="gateway-technical-card"]').trigger('click');

    expect(wrapper.emitted('select')).toEqual([['technical']]);
  });

  it('renders the English heading text when language is "en"', () => {
    const wrapper = mountGateway({ language: 'en' });

    expect(wrapper.text()).toContain('How would you like to explore this proposal?');
  });
});

import { mount } from '@vue/test-utils';
import ProposalPreview from '../../components/BusinessProposal/admin/ProposalPreview.vue';

function mountProposalPreview(props = {}) {
  return mount(ProposalPreview, {
    props: {
      uuid: 'abc-123',
      ...props,
    },
  });
}

describe('ProposalPreview', () => {
  it('renders a link element', () => {
    const wrapper = mountProposalPreview();

    expect(wrapper.find('a').exists()).toBe(true);
  });

  it('link href points to the correct proposal path', () => {
    const wrapper = mountProposalPreview({ uuid: 'xyz-789' });

    expect(wrapper.find('a').attributes('href')).toBe('/proposal/xyz-789');
  });

  it('link opens in a new tab', () => {
    const wrapper = mountProposalPreview();

    expect(wrapper.find('a').attributes('target')).toBe('_blank');
  });

  it('displays Preview text', () => {
    const wrapper = mountProposalPreview();

    expect(wrapper.text()).toContain('Preview');
  });
});

import { mount } from '@vue/test-utils';

jest.mock('../../stores/proposals', () => ({
  useProposalStore: jest.fn(() => ({
    requestMagicLink: jest.fn().mockResolvedValue({}),
  })),
}));

import ProposalExpired from '../../components/BusinessProposal/ProposalExpired.vue';

const proposal = {
  client_name: 'John Doe',
  title: 'Web Project Proposal',
  seller_name: 'Jane Smith',
  expired_at: '2024-01-15T10:00:00Z',
  whatsapp_url: 'https://wa.me/123456789',
};

function mountProposalExpired(props = {}) {
  return mount(ProposalExpired, {
    props: { proposal, ...props },
  });
}

describe('ProposalExpired', () => {
  it('renders the section element', () => {
    const wrapper = mountProposalExpired();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the expired heading text', () => {
    const wrapper = mountProposalExpired();

    expect(wrapper.text()).toContain('ha expirado');
  });

  it('renders the client name in the heading', () => {
    const wrapper = mountProposalExpired();

    expect(wrapper.text()).toContain('John Doe');
  });

  it('renders the magic link email form', () => {
    const wrapper = mountProposalExpired();

    expect(wrapper.find('form').exists()).toBe(true);
    expect(wrapper.find('input[type="email"]').exists()).toBe(true);
  });

  it('renders the submit button for magic link', () => {
    const wrapper = mountProposalExpired();

    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('renders whatsapp link when whatsapp_url is provided', () => {
    const wrapper = mountProposalExpired();

    const link = wrapper.findAll('a').find(a => a.attributes('href') === 'https://wa.me/123456789');
    expect(link).toBeTruthy();
  });
});

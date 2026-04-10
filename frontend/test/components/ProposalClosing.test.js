import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useExpirationTimer', () => ({
  useExpirationTimer: jest.fn(() => ({
    daysRemaining: require('vue').ref(30),
  })),
}));

jest.mock('canvas-confetti', () => jest.fn());

global.useProposalStore = jest.fn(() => ({
  respondToProposal: jest.fn().mockResolvedValue({ success: true }),
  commentOnProposal: jest.fn().mockResolvedValue({ success: true }),
  scheduleFollowup: jest.fn().mockResolvedValue({ success: true }),
}));

import ProposalClosing from '../../components/BusinessProposal/ProposalClosing.vue';

const sentProposal = {
  uuid: 'test-uuid-123',
  status: 'sent',
  title: 'Test Proposal',
  total_investment: 1490000,
  currency: 'COP',
};

function mountProposalClosing(props = {}) {
  return mount(ProposalClosing, {
    props: { proposal: sentProposal, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: true,
      },
    },
  });
}

describe('ProposalClosing', () => {
  it('renders the section element', () => {
    const wrapper = mountProposalClosing();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the accept button when proposal status is sent', () => {
    const wrapper = mountProposalClosing();

    const acceptBtn = wrapper.findAll('button').find(b => b.text().includes('Acepto'));
    expect(acceptBtn).toBeTruthy();
  });

  it('renders the validity notice when validityMessage is provided', () => {
    const wrapper = mountProposalClosing({ validityMessage: 'Esta propuesta es válida por 30 días.' });

    expect(wrapper.text()).toContain('Esta propuesta es válida por 30 días.');
  });

  it('renders the thank you message when provided', () => {
    const wrapper = mountProposalClosing({ thankYouMessage: '¡Gracias por revisar nuestra propuesta!' });

    expect(wrapper.text()).toContain('¡Gracias por revisar nuestra propuesta!');
  });

  it('does not render accept button when proposal status is accepted', () => {
    const wrapper = mountProposalClosing({
      proposal: { ...sentProposal, status: 'accepted' },
    });

    const acceptBtn = wrapper.findAll('button').find(b => b.text().includes('Acepto la propuesta'));
    expect(acceptBtn).toBeFalsy();
  });
});

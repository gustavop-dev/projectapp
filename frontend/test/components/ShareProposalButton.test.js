import { mount } from '@vue/test-utils';

global.useProposalStore = jest.fn(() => ({
  trackProposalEvent: jest.fn(),
}));

Object.assign(navigator, {
  clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
  share: undefined,
});

import ShareProposalButton from '../../components/BusinessProposal/ShareProposalButton.vue';

function mountShareProposalButton(props = {}) {
  return mount(ShareProposalButton, {
    props: { proposalUuid: 'test-uuid-123', ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ShareProposalButton', () => {
  it('renders the floating share button', () => {
    const wrapper = mountShareProposalButton();

    expect(wrapper.find('[data-testid="share-proposal-btn"]').exists()).toBe(true);
  });

  it('shows the Spanish share title by default', () => {
    const wrapper = mountShareProposalButton();

    expect(wrapper.find('[data-testid="share-proposal-btn"]').attributes('title')).toBe('Compartir propuesta');
  });

  it('shows the English share title when language is en', () => {
    const wrapper = mountShareProposalButton({ language: 'en' });

    expect(wrapper.find('[data-testid="share-proposal-btn"]').attributes('title')).toBe('Share proposal');
  });

  it('opens the share modal when share button is clicked', async () => {
    const wrapper = mountShareProposalButton();

    await wrapper.find('[data-testid="share-proposal-btn"]').trigger('click');

    expect(wrapper.find('.share-modal-card').exists()).toBe(true);
  });

  it('shows the copy link button inside the modal', async () => {
    const wrapper = mountShareProposalButton();

    await wrapper.find('[data-testid="share-proposal-btn"]').trigger('click');

    expect(wrapper.text()).toContain('Copiar enlace');
  });
});

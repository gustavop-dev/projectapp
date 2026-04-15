import { mount } from '@vue/test-utils';

import ProposalActionsModal from '../../components/BusinessProposal/admin/ProposalActionsModal.vue';

function mountModal(proposal = {}, extra = {}) {
  return mount(ProposalActionsModal, {
    props: {
      visible: true,
      proposal: { status: 'draft', available_transitions: [], uuid: 'p-1', ...proposal },
      ...extra,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ProposalActionsModal', () => {
  it('does not render when visible is false', () => {
    const wrapper = mountModal({}, { visible: false });
    expect(wrapper.find('[data-testid="proposal-action-preview"]').exists()).toBe(false);
  });

  it('shows "send" action for draft with client_email', () => {
    const wrapper = mountModal({ status: 'draft', client_email: 'a@b.com' });
    expect(wrapper.find('[data-testid="proposal-action-send"]').exists()).toBe(true);
  });

  it('hides "send" action for draft without client_email', () => {
    const wrapper = mountModal({ status: 'draft', client_email: '' });
    expect(wrapper.find('[data-testid="proposal-action-send"]').exists()).toBe(false);
  });

  it('shows "resend" and "negotiate" for sent with transitions', () => {
    const wrapper = mountModal({
      status: 'sent',
      client_email: 'a@b.com',
      available_transitions: ['negotiating', 'rejected'],
    });
    expect(wrapper.find('[data-testid="proposal-action-resend"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="proposal-action-negotiate"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="proposal-action-reject"]').exists()).toBe(true);
  });

  it('renders preview as an anchor to the public URL', () => {
    const wrapper = mountModal({ uuid: 'abc-123' });
    const preview = wrapper.find('[data-testid="proposal-action-preview"]');
    expect(preview.exists()).toBe(true);
    expect(preview.element.tagName).toBe('A');
    expect(preview.attributes('href')).toBe('/proposal/abc-123?preview=1');
  });

  it('marks the suggested action with a "Sugerido" badge', () => {
    const wrapper = mountModal({ status: 'draft', client_email: 'a@b.com' });
    const sendItem = wrapper.find('[data-testid="proposal-action-send"]');
    expect(sendItem.text()).toContain('Sugerido');
  });

  it('emits the action key and close when an action is clicked', async () => {
    const wrapper = mountModal({ status: 'draft', client_email: 'a@b.com' });
    await wrapper.find('[data-testid="proposal-action-send"]').trigger('click');
    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits close when backdrop is clicked', async () => {
    const wrapper = mountModal();
    await wrapper.find('.fixed.inset-0.z-\\[9999\\] > div.absolute').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('includes launch action for accepted and re-label when already launched', () => {
    const wrapper = mountModal({
      status: 'accepted',
      available_transitions: ['finished'],
      platform_onboarding_completed_at: '2026-01-01T00:00:00Z',
    });
    const launch = wrapper.find('[data-testid="proposal-action-launch"]');
    expect(launch.exists()).toBe(true);
    expect(launch.text()).toContain('Re-lanzar a Plataforma');
    expect(wrapper.find('[data-testid="proposal-action-finish"]').exists()).toBe(true);
  });

  it('shows empty state message when no proposal context produces actions', () => {
    const wrapper = mountModal({
      status: 'expired',
      available_transitions: [],
      uuid: null,
    });
    expect(wrapper.text()).toContain('No hay acciones disponibles');
  });
});

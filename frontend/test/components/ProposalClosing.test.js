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

// ── Modal flows (additions) ──────────────────────────────────────────────────

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const mockProposalActions = {
  respondToProposal: jest.fn(),
  commentOnProposal: jest.fn(),
  scheduleFollowup: jest.fn(),
};

describe('ProposalClosing modal flows', () => {
  beforeEach(() => {
    mockProposalActions.respondToProposal.mockReset().mockResolvedValue({ success: true });
    mockProposalActions.commentOnProposal.mockReset().mockResolvedValue({ success: true });
    mockProposalActions.scheduleFollowup.mockReset().mockResolvedValue({ success: true });
    global.useProposalStore = jest.fn(() => mockProposalActions);
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // ── Accept confirm modal ──────────────────────────────────────────────────

  it('opens the accept confirm modal when the accept button is clicked', async () => {
    const wrapper = mountProposalClosing();
    const acceptBtn = wrapper.findAll('button').find(b => b.text().includes('Acepto la propuesta'));
    await acceptBtn.trigger('click');

    expect(wrapper.text()).toContain('¡Perfecto');
  });

  it('calls respondToProposal with accepted when the confirm button is clicked', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('Acepto la propuesta')).trigger('click');
    await wrapper.findAll('button').find(b => b.text() === '¡Confirmar!').trigger('click');
    await flushPromises();

    expect(mockProposalActions.respondToProposal).toHaveBeenCalledWith(
      sentProposal.uuid,
      'accepted',
      expect.any(Object)
    );
  });

  // ── Negotiate modal ───────────────────────────────────────────────────────

  it('opens the negotiate modal when the Necesito ajustes button is clicked', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('Necesito ajustes')).trigger('click');

    expect(wrapper.text()).toContain('negociemos alcance');
  });

  it('calls respondToProposal with negotiating when the negotiate form is submitted', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('Necesito ajustes')).trigger('click');

    await wrapper.find('textarea').setValue('Quiero reducir el alcance');
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('Enviar solicitud'));
    await submitBtn.trigger('click');
    await flushPromises();

    expect(mockProposalActions.respondToProposal).toHaveBeenCalledWith(
      sentProposal.uuid,
      'negotiating',
      expect.any(Object)
    );
  });

  // ── Comment modal ─────────────────────────────────────────────────────────

  it('opens the comment modal when the Tengo comentarios button is clicked', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('Tengo comentarios')).trigger('click');

    expect(wrapper.text()).toContain('Enviar mensaje');
  });

  it('calls commentOnProposal when the comment is submitted', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('Tengo comentarios')).trigger('click');

    const textareas = wrapper.findAll('textarea');
    await textareas[textareas.length - 1].setValue('Tengo una duda sobre el alcance');
    const sendBtn = wrapper.findAll('button').find(b => b.text() === 'Enviar mensaje');
    await sendBtn.trigger('click');
    await flushPromises();

    expect(mockProposalActions.commentOnProposal).toHaveBeenCalled();
  });

  // ── Reject modal ──────────────────────────────────────────────────────────

  it('opens the reject modal when the No es el momento button is clicked', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('No es el momento')).trigger('click');

    expect(wrapper.text()).toContain('Lamentamos que no sea el momento');
  });

  it('calls respondToProposal with rejected when the reject form is confirmed', async () => {
    const wrapper = mountProposalClosing();
    await wrapper.findAll('button').find(b => b.text().includes('No es el momento')).trigger('click');

    await wrapper.findAll('button').find(b => b.text() === 'Confirmar rechazo').trigger('click');
    await flushPromises();

    expect(mockProposalActions.respondToProposal).toHaveBeenCalledWith(
      sentProposal.uuid,
      'rejected',
      expect.any(Object)
    );
  });

  // ── Payment milestones ────────────────────────────────────────────────────

  it('renders payment milestones when proposal has payment_options with milestones', () => {
    const wrapper = mountProposalClosing({
      proposal: {
        ...sentProposal,
        payment_options: {
          milestones: [
            { label: 'Pago inicial', amount: '$500.000' },
            { label: 'Entrega final', amount: '$990.000' },
          ],
        },
      },
    });

    expect(wrapper.text()).toContain('Pago inicial');
    expect(wrapper.text()).toContain('Entrega final');
  });

  // ── WhatsApp link ─────────────────────────────────────────────────────────

  it('renders the WhatsApp link when whatsappLink prop is provided', () => {
    const wrapper = mountProposalClosing({ whatsappLink: 'https://wa.me/123?text=hello' });

    const link = wrapper.find('a[href="https://wa.me/123?text=hello"]');
    expect(link.exists()).toBe(true);
  });
});

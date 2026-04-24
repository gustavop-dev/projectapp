/**
 * Tests for DiagnosticActionsModal.vue.
 *
 * Covers: visibility, all action conditions (send/resend/analyze/send-final/
 * preview/delete), emit behavior, suggested badge, empty state.
 */

jest.mock('../../utils/diagnosticNextAction', () => ({
  getDiagnosticNextAction: jest.fn(() => null),
}));

import { mount } from '@vue/test-utils';
import { getDiagnosticNextAction } from '../../utils/diagnosticNextAction';
import DiagnosticActionsModal from '../../components/WebAppDiagnostic/DiagnosticActionsModal.vue';

const draftDiagnostic = {
  status: 'draft',
  available_transitions: [],
  client: { email: 'client@example.com' },
  final_sent_at: null,
  public_url: null,
};

const sentDiagnostic = {
  status: 'sent',
  available_transitions: [],
  client: { email: 'client@example.com' },
  final_sent_at: null,
  public_url: null,
};

function mountModal(props = {}) {
  return mount(DiagnosticActionsModal, {
    props: { visible: true, diagnostic: draftDiagnostic, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('DiagnosticActionsModal', () => {
  beforeEach(() => {
    getDiagnosticNextAction.mockReturnValue(null);
  });

  // ── Visibility ────────────────────────────────────────────────────────────

  describe('visibility', () => {
    it('renders nothing when visible is false', () => {
      const wrapper = mountModal({ visible: false });

      expect(wrapper.text()).not.toContain('Acciones del diagnóstico');
    });

    it('renders modal title when visible is true', () => {
      const wrapper = mountModal({ visible: true });

      expect(wrapper.text()).toContain('Acciones del diagnóstico');
    });
  });

  // ── Close ─────────────────────────────────────────────────────────────────

  describe('close', () => {
    it('emits close when the close button is clicked', async () => {
      const wrapper = mountModal();
      await wrapper.find('button[aria-label="Cerrar"]').trigger('click');

      expect(wrapper.emitted('close')).toBeTruthy();
    });
  });

  // ── Action conditions ─────────────────────────────────────────────────────

  describe('send action', () => {
    it('shows send action when diagnostic is draft with a client email', () => {
      const wrapper = mountModal({ diagnostic: draftDiagnostic });

      expect(wrapper.find('[data-testid="diagnostic-action-send"]').exists()).toBe(true);
    });

    it('does not show send action when draft diagnostic has no client email', () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, client: {} },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-send"]').exists()).toBe(false);
    });
  });

  describe('resend action', () => {
    it('shows resend action when diagnostic status is sent', () => {
      const wrapper = mountModal({ diagnostic: sentDiagnostic });

      expect(wrapper.find('[data-testid="diagnostic-action-resend"]').exists()).toBe(true);
    });

    it('shows resend action when diagnostic status is viewed', () => {
      const wrapper = mountModal({
        diagnostic: { ...sentDiagnostic, status: 'viewed' },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-resend"]').exists()).toBe(true);
    });
  });

  describe('analyze action', () => {
    it('shows analyze action when negotiating is in available_transitions', () => {
      const wrapper = mountModal({
        diagnostic: { ...sentDiagnostic, available_transitions: ['negotiating'] },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-analyze"]').exists()).toBe(true);
    });
  });

  describe('send-final action', () => {
    it('shows send-final action when status is negotiating and final_sent_at is null', () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, status: 'negotiating', final_sent_at: null },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-send-final"]').exists()).toBe(true);
    });

    it('does not show send-final when final_sent_at is already set', () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, status: 'negotiating', final_sent_at: '2026-04-01' },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-send-final"]').exists()).toBe(false);
    });
  });

  describe('preview action', () => {
    it('renders preview as an anchor tag when public_url is set', () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, public_url: 'https://example.com/public/abc' },
      });

      const previewEl = wrapper.find('[data-testid="diagnostic-action-preview"]');
      expect(previewEl.exists()).toBe(true);
      expect(previewEl.element.tagName).toBe('A');
    });
  });

  describe('delete action', () => {
    it('shows delete action when diagnostic is not in a terminal state', () => {
      const wrapper = mountModal({ diagnostic: draftDiagnostic });

      expect(wrapper.find('[data-testid="diagnostic-action-delete"]').exists()).toBe(true);
    });

    it('does not show delete action when status is accepted', () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, status: 'accepted' },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-delete"]').exists()).toBe(false);
    });

    it('does not show delete action when status is rejected', () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, status: 'rejected' },
      });

      expect(wrapper.find('[data-testid="diagnostic-action-delete"]').exists()).toBe(false);
    });
  });

  // ── Emit on action click ──────────────────────────────────────────────────

  describe('action emits', () => {
    it('emits send when the send action button is clicked', async () => {
      const wrapper = mountModal({ diagnostic: draftDiagnostic });
      await wrapper.find('[data-testid="diagnostic-action-send"]').trigger('click');

      expect(wrapper.emitted('send')).toBeTruthy();
    });

    it('emits resend when the resend action button is clicked', async () => {
      const wrapper = mountModal({ diagnostic: sentDiagnostic });
      await wrapper.find('[data-testid="diagnostic-action-resend"]').trigger('click');

      expect(wrapper.emitted('resend')).toBeTruthy();
    });

    it('emits analyze when the analyze action button is clicked', async () => {
      const wrapper = mountModal({
        diagnostic: { ...sentDiagnostic, available_transitions: ['negotiating'] },
      });
      await wrapper.find('[data-testid="diagnostic-action-analyze"]').trigger('click');

      expect(wrapper.emitted('analyze')).toBeTruthy();
    });

    it('emits send-final when the send-final action button is clicked', async () => {
      const wrapper = mountModal({
        diagnostic: { ...draftDiagnostic, status: 'negotiating' },
      });
      await wrapper.find('[data-testid="diagnostic-action-send-final"]').trigger('click');

      expect(wrapper.emitted('send-final')).toBeTruthy();
    });

    it('emits delete when the delete action button is clicked', async () => {
      const wrapper = mountModal({ diagnostic: draftDiagnostic });
      await wrapper.find('[data-testid="diagnostic-action-delete"]').trigger('click');

      expect(wrapper.emitted('delete')).toBeTruthy();
    });

    it('emits close after any non-link action is clicked', async () => {
      const wrapper = mountModal({ diagnostic: draftDiagnostic });
      await wrapper.find('[data-testid="diagnostic-action-send"]').trigger('click');

      expect(wrapper.emitted('close')).toBeTruthy();
    });
  });

  // ── Suggested badge ───────────────────────────────────────────────────────

  describe('suggested badge', () => {
    it('marks the suggested action with Sugerido badge', () => {
      getDiagnosticNextAction.mockReturnValue({ key: 'send' });
      const wrapper = mountModal({ diagnostic: draftDiagnostic });

      expect(wrapper.find('[data-testid="diagnostic-action-send"]').text()).toContain('Sugerido');
    });

    it('does not show Sugerido badge when there is no suggested action', () => {
      getDiagnosticNextAction.mockReturnValue(null);
      const wrapper = mountModal({ diagnostic: draftDiagnostic });

      expect(wrapper.text()).not.toContain('Sugerido');
    });
  });

  // ── Empty state ───────────────────────────────────────────────────────────

  describe('empty state', () => {
    it('shows empty state message when no actions are available', () => {
      const wrapper = mountModal({
        diagnostic: { status: 'accepted', available_transitions: [], client: {}, final_sent_at: null, public_url: null },
      });

      expect(wrapper.text()).toContain('No hay acciones disponibles');
    });
  });
});

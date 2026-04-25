/**
 * Tests for ShareDiagnosticButton.vue.
 *
 * Covers: floating button render, modal open/close, URL display,
 * clipboard copy, copied-state reset, native share, language switching.
 */

import { mount } from '@vue/test-utils';
import ShareDiagnosticButton from '../../components/WebAppDiagnostic/public/ShareDiagnosticButton.vue';

function mountButton(props = {}) {
  return mount(ShareDiagnosticButton, {
    props: { diagnosticUuid: 'test-uuid', ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ShareDiagnosticButton', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    global.navigator.clipboard = { writeText: jest.fn().mockResolvedValue(undefined) };
    delete global.navigator.share;
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // ── Render ────────────────────────────────────────────────────────────────

  describe('rendering', () => {
    it('renders the floating share button', () => {
      const wrapper = mountButton();

      expect(wrapper.find('[data-testid="share-diagnostic-btn"]').exists()).toBe(true);
    });

    it('does not render modal content before the button is clicked', () => {
      const wrapper = mountButton();

      expect(wrapper.text()).not.toContain('Compartir diagnóstico');
    });

    it('renders Spanish labels when language prop is es', async () => {
      const wrapper = mountButton({ language: 'es' });
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      expect(wrapper.text()).toContain('Compartir diagnóstico');
      expect(wrapper.text()).toContain('Copiar enlace');
    });

    it('renders English labels when language prop is en', async () => {
      const wrapper = mountButton({ language: 'en' });
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      expect(wrapper.text()).toContain('Share diagnostic');
      expect(wrapper.text()).toContain('Copy link');
    });
  });

  // ── Modal open/close ──────────────────────────────────────────────────────

  describe('modal', () => {
    it('opens the modal when the floating button is clicked', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      expect(wrapper.text()).toContain('Compartir diagnóstico');
    });

    it('displays the current page URL inside the modal', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      // jsdom sets location.href to http://localhost/ — just verify it renders something
      expect(wrapper.text()).toContain('http://localhost');
    });

    it('closes the modal when the close button is clicked', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      const closeBtn = wrapper.findAll('button').find(b =>
        b.find('svg path[d*="M6 18L18"]').exists()
      );
      await closeBtn.trigger('click');

      expect(wrapper.text()).not.toContain('Compartir diagnóstico');
    });
  });

  // ── Clipboard ─────────────────────────────────────────────────────────────

  describe('copy link', () => {
    it('calls clipboard.writeText with the page URL when copy is clicked', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      const copyBtn = wrapper.findAll('button').find(b => b.text().includes('Copiar enlace'));
      await copyBtn.trigger('click');
      await Promise.resolve();

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.any(String));
    });

    it('shows the copied confirmation text after the link is copied', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      const copyBtn = wrapper.findAll('button').find(b => b.text().includes('Copiar enlace'));
      await copyBtn.trigger('click');
      await Promise.resolve();
      await wrapper.vm.$nextTick();

      expect(wrapper.text()).toContain('¡Copiado!');
    });

    it('resets the copied state after 2500 ms', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      const copyBtn = wrapper.findAll('button').find(b => b.text().includes('Copiar enlace'));
      await copyBtn.trigger('click');
      await Promise.resolve();
      await wrapper.vm.$nextTick();

      jest.advanceTimersByTime(2500);
      await wrapper.vm.$nextTick();

      expect(wrapper.text()).not.toContain('¡Copiado!');
    });
  });

  // ── Native share ──────────────────────────────────────────────────────────

  describe('native share', () => {
    it('shows native share button when navigator.share is available', async () => {
      global.navigator.share = jest.fn().mockResolvedValue(undefined);
      const wrapper = mountButton();
      await wrapper.vm.$nextTick();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      expect(wrapper.text()).toContain('Compartir vía apps');
    });

    it('hides native share button when navigator.share is unavailable', async () => {
      const wrapper = mountButton();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      expect(wrapper.text()).not.toContain('Compartir vía apps');
    });

    it('calls navigator.share when the share-via-apps button is clicked', async () => {
      global.navigator.share = jest.fn().mockResolvedValue(undefined);
      const wrapper = mountButton();
      await wrapper.vm.$nextTick();
      await wrapper.find('[data-testid="share-diagnostic-btn"]').trigger('click');

      const shareBtn = wrapper.findAll('button').find(b => b.text().includes('Compartir vía apps'));
      await shareBtn.trigger('click');

      expect(navigator.share).toHaveBeenCalledWith(
        expect.objectContaining({ url: expect.any(String) })
      );
    });
  });
});

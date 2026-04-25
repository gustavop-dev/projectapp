import { mount, flushPromises } from '@vue/test-utils';

const mockRouterReplace = jest.fn();
const mockRoute = { query: {} };

global.useLocalePath = jest.fn(() => (path) => path);
global.useRoute = jest.fn(() => mockRoute);
global.useRouter = jest.fn(() => ({ replace: mockRouterReplace }));
global.definePageMeta = jest.fn();

jest.mock('../../components/panel/defaults/ProposalDefaultsPanel.vue', () => ({
  name: 'ProposalDefaultsPanel',
  template: '<div data-testid="proposal-panel">ProposalPanel</div>',
}));

jest.mock('../../components/panel/defaults/DiagnosticDefaultsPanel.vue', () => ({
  name: 'DiagnosticDefaultsPanel',
  template: '<div data-testid="diagnostic-panel">DiagnosticPanel</div>',
}));

import DefaultsShell from '../../pages/panel/defaults.vue';

function mountShell(query = {}) {
  mockRoute.query = query;
  mockRouterReplace.mockClear();
  return mount(DefaultsShell, {
    global: {
      stubs: { NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' } },
    },
  });
}

describe('DefaultsShell — mode computed', () => {
  it('defaults to proposal mode when no query param', async () => {
    const wrapper = mountShell({});
    await flushPromises();

    expect(wrapper.find('[data-testid="defaults-mode-proposal"]').classes()).toContain('text-emerald-600');
    expect(wrapper.find('[data-testid="proposal-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="diagnostic-panel"]').exists()).toBe(false);
  });

  it('activates diagnostic mode when ?mode=diagnostic', async () => {
    const wrapper = mountShell({ mode: 'diagnostic' });
    await flushPromises();

    expect(wrapper.find('[data-testid="defaults-mode-diagnostic"]').classes()).toContain('text-emerald-600');
    expect(wrapper.find('[data-testid="diagnostic-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="proposal-panel"]').exists()).toBe(false);
  });

  it('ignores unknown mode values and falls back to proposal', async () => {
    const wrapper = mountShell({ mode: 'unknown' });
    await flushPromises();

    expect(wrapper.find('[data-testid="proposal-panel"]').exists()).toBe(true);
  });
});

describe('DefaultsShell — setMode', () => {
  it('calls router.replace with mode=diagnostic when switching to diagnostic', async () => {
    const wrapper = mountShell({});

    await wrapper.find('[data-testid="defaults-mode-diagnostic"]').trigger('click');

    expect(mockRouterReplace).toHaveBeenCalledWith(
      expect.objectContaining({ query: expect.objectContaining({ mode: 'diagnostic' }) }),
    );
  });

  it('does not call router.replace when clicking already-active mode', async () => {
    const wrapper = mountShell({ mode: 'proposal' });

    await wrapper.find('[data-testid="defaults-mode-proposal"]').trigger('click');

    expect(mockRouterReplace).not.toHaveBeenCalled();
  });

  it('clears tab param when switching modes', async () => {
    const wrapper = mountShell({ mode: 'proposal', tab: 'sections' });

    await wrapper.find('[data-testid="defaults-mode-diagnostic"]').trigger('click');

    const call = mockRouterReplace.mock.calls[0][0];
    expect(call.query.tab).toBeUndefined();
  });
});

describe('DefaultsShell — backLink', () => {
  it('shows "Volver a Propuestas" in proposal mode', () => {
    const wrapper = mountShell({});

    expect(wrapper.text()).toContain('Volver a Propuestas');
  });

  it('shows "Volver a Diagnósticos" in diagnostic mode', () => {
    const wrapper = mountShell({ mode: 'diagnostic' });

    expect(wrapper.text()).toContain('Volver a Diagnósticos');
  });
});

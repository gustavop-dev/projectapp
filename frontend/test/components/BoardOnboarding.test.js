import { mount } from '@vue/test-utils';
import BoardOnboarding from '../../components/platform/BoardOnboarding.vue';

function mountBoardOnboarding(props = {}) {
  return mount(BoardOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('BoardOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
    window.scrollTo = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('mounts without errors', () => {
    const wrapper = mountBoardOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountBoardOnboarding();

    expect(wrapper.text()).toBe('');
  });

  it('shows onboarding content after start() is called', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Progreso del proyecto');
  });

  it('does not start if already seen (localStorage key present)', async () => {
    localStorage.setItem('board_onboarding_seen', 'true');
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  // ── Step navigation ───────────────────────────────────────────────────────

  it('advances to the next step when the Siguiente button is clicked', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const siguienteBtn = wrapper.findAll('button').find(b => b.text() === 'Siguiente');
    await siguienteBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Columnas del tablero');
  });

  it('goes back to step 1 when the Atrás button is clicked on step 2', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // Advance to step 2
    await wrapper.findAll('button').find(b => b.text() === 'Siguiente').trigger('click');
    await wrapper.vm.$nextTick();

    // Go back
    await wrapper.findAll('button').find(b => b.text() === 'Atrás').trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Progreso del proyecto');
  });

  it('emits complete when Entendido is clicked on the last step', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // Advance to last step (step index 1 of 2 non-optional steps in jsdom)
    await wrapper.findAll('button').find(b => b.text() === 'Siguiente').trigger('click');
    await wrapper.vm.$nextTick();

    // Click Entendido on last step
    const entendidoBtn = wrapper.findAll('button').find(b => b.text() === 'Entendido');
    await entendidoBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  // ── Keyboard dismiss ──────────────────────────────────────────────────────

  it('dismisses the tour when Escape is pressed while visible', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  // ── localStorage ──────────────────────────────────────────────────────────

  it('writes board_onboarding_seen to localStorage when the tour is dismissed', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(localStorage.getItem('board_onboarding_seen')).toBe('true');
  });

  it('forceStart overrides localStorage blocking and shows the tour', async () => {
    localStorage.setItem('board_onboarding_seen', 'true');
    const wrapper = mountBoardOnboarding();

    wrapper.vm.forceStart();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Progreso del proyecto');
  });

  // ── Target absent ─────────────────────────────────────────────────────────

  it('renders the tooltip in center position when the tour target is not in the DOM', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // spotlightRect is null when target not found — tooltip should still render
    expect(wrapper.text()).toContain('Progreso del proyecto');
    expect(wrapper.vm.spotlightRect).toBeNull();
  });
});

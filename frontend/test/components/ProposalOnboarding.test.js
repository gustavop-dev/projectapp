import { mount } from '@vue/test-utils';
import ProposalOnboarding from '../../components/BusinessProposal/ProposalOnboarding.vue';

function mountProposalOnboarding(props = {}) {
  return mount(ProposalOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ProposalOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('mounts without errors', () => {
    const wrapper = mountProposalOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountProposalOnboarding();

    expect(wrapper.find('[data-testid="onboarding-backdrop"]').exists()).toBe(false);
  });

  it('shows onboarding content after start() is called', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="onboarding-step-progress"]').exists()).toBe(true);
  });

  it('does not start if already seen (localStorage key present)', async () => {
    localStorage.setItem('proposal_onboarding_seen', 'true');
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="onboarding-backdrop"]').exists()).toBe(false);
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  it('shows step progress indicator after start', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('/');
  });
});

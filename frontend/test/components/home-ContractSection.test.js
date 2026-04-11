import { mount } from '@vue/test-utils';

jest.mock('gsap', () => ({
  __esModule: true,
  default: {
    to: jest.fn().mockReturnThis(),
    from: jest.fn().mockReturnThis(),
    set: jest.fn().mockReturnThis(),
    fromTo: jest.fn().mockReturnThis(),
    timeline: jest.fn(() => ({
      to: jest.fn().mockReturnThis(),
      from: jest.fn().mockReturnThis(),
      add: jest.fn().mockReturnThis(),
      play: jest.fn().mockReturnThis(),
      kill: jest.fn().mockReturnThis(),
    })),
    registerPlugin: jest.fn(),
    killTweensOf: jest.fn(),
    context: jest.fn(() => ({ revert: jest.fn() })),
  },
  TextPlugin: {},
}));

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: {
      value: {
        contract: {
          playReel: 'Play Reel',
          priceSubtitle: 'Get a custom quote.',
          ctaButton: 'Start Project',
        },
      },
    },
  })),
}));

// Mock asset imports
jest.mock('../../assets/images/home/services/contract/card-landing-design.webp', () => '/img/card.webp', { virtual: true });
jest.mock('../../assets/videos/presentationMobile.mp4', () => '/video/mobile.mp4', { virtual: true });

import ContractSection from '../../components/home/ContractSection.vue';

function mountContractSection(props = {}) {
  return mount(ContractSection, {
    props,
    global: {
      stubs: {
        VideoModal: { template: '<div class="video-modal-stub" />' },
        NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' },
      },
    },
  });
}

describe('ContractSection', () => {
  it('renders the contract section element', () => {
    const wrapper = mountContractSection();

    expect(wrapper.find('.contract-section').exists()).toBe(true);
  });

  it('renders the Play Reel button', () => {
    const wrapper = mountContractSection();

    expect(wrapper.text()).toContain('Play Reel');
  });

  it('renders Design heading text', () => {
    const wrapper = mountContractSection();

    expect(wrapper.text()).toContain('Design');
  });

  it('renders the contract card with background', () => {
    const wrapper = mountContractSection();

    expect(wrapper.find('.contract-card').exists()).toBe(true);
  });
});

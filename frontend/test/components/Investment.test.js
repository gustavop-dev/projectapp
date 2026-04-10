import { mount } from '@vue/test-utils';

global.IntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useExpirationTimer', () => ({
  useExpirationTimer: jest.fn(() => ({
    daysRemaining: require('vue').ref(30),
    urgencyLevel: require('vue').ref('normal'),
  })),
}));

jest.mock('../../composables/useAnimatedNumber', () => ({
  useAnimatedNumber: jest.fn(() => ({
    animated: require('vue').ref(0),
  })),
}));

import Investment from '../../components/BusinessProposal/Investment.vue';

const defaultProps = {
  title: 'Inversión y Formas de Pago',
  introText: 'Conoce el detalle de tu inversión.',
  totalInvestment: '$1.490.000',
  currency: 'COP',
  index: '9',
};

function mountInvestment(props = {}) {
  return mount(Investment, {
    props: { ...defaultProps, ...props },
    global: {
      stubs: {
        InvestmentCalculatorModal: { template: '<div class="calculator-modal-stub" />' },
        InvestmentDetailedTeaser: { template: '<div class="teaser-stub" />' },
        Transition: true,
      },
    },
  });
}

describe('Investment', () => {
  it('renders the section element', () => {
    const wrapper = mountInvestment();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the title prop', () => {
    const wrapper = mountInvestment();

    expect(wrapper.text()).toContain('Inversión y Formas de Pago');
  });

  it('renders the intro text prop', () => {
    const wrapper = mountInvestment();

    expect(wrapper.text()).toContain('Conoce el detalle de tu inversión.');
  });

  it('renders the customize investment button', () => {
    const wrapper = mountInvestment({ modules: [{ id: 1, title: 'Module', optional: true }] });

    const btn = wrapper.findAll('button').find(b => b.text().includes('Personalizar'));
    expect(btn).toBeTruthy();
  });

  it('renders the InvestmentCalculatorModal stub', () => {
    const wrapper = mountInvestment();

    expect(wrapper.find('.calculator-modal-stub').exists()).toBe(true);
  });
});

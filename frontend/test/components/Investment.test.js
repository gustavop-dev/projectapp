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

  describe('hosting billing tiers', () => {
    const billingTiers = [
      { frequency: 'semiannual', months: 6, discountPercent: 20, label: 'Semestral', badge: '' },
      { frequency: 'quarterly', months: 3, discountPercent: 10, label: 'Trimestral', badge: '' },
      { frequency: 'monthly', months: 1, discountPercent: 0, label: 'Mensual', badge: '' },
    ];

    function hostingPlanWith(percent, tiers = billingTiers) {
      return {
        title: 'Hosting',
        description: '',
        specs: [],
        hostingPercent: percent,
        billingTiers: tiers,
      };
    }

    it('recomputes the monthly tier price from hostingPlan.hostingPercent', () => {
      const at30 = mountInvestment({
        totalInvestment: '$1.200.000',
        hostingPlan: hostingPlanWith(30),
      });
      const at50 = mountInvestment({
        totalInvestment: '$1.200.000',
        hostingPlan: hostingPlanWith(50),
      });

      // 1.200.000 * 30% / 12 = 30.000
      expect(at30.text()).toContain('$30.000');
      // 1.200.000 * 50% / 12 = 50.000
      expect(at50.text()).toContain('$50.000');
    });

    it('applies the quarterly discountPercent from billingTiers to the rendered tier', () => {
      const tiers = [
        { frequency: 'quarterly', months: 3, discountPercent: 25, label: 'Trimestral', badge: '' },
        { frequency: 'monthly', months: 1, discountPercent: 0, label: 'Mensual', badge: '' },
      ];
      const wrapper = mountInvestment({
        totalInvestment: '$1.200.000',
        hostingPlan: hostingPlanWith(30, tiers),
      });

      // 25% discount badge is rendered on the trimestral card
      expect(wrapper.text()).toContain('25%');
    });
  });
});

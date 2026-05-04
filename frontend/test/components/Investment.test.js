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

  // Bug fix: "Tres pagos flexibles" amounts must derive from the LABEL percent
  // applied to the currently displayed total — not from the stored description
  // amount × ratio (which double-scaled when the backend rebuilds descriptions
  // at effective×pct and the frontend then multiplies by effective/base).
  describe('payment options — split derived from label percent × displayed total', () => {
    const splitOptions = [
      { label: '40% al firmar el contrato ✍️', description: '$2.160.000 COP' },
      { label: '30% al aprobar el diseño final ✅', description: '$1.620.000 COP' },
      { label: '30% al desplegar el sitio web 🚀', description: '$1.620.000 COP' },
    ];

    it('renders amounts as effectiveTotal × labelPercent (sums to effectiveTotal)', () => {
      const wrapper = mountInvestment({
        totalInvestment: '$5.400.000',
        effectiveTotal: 9_720_000, // 5.400.000 × 1.8 (e.g. AI module 80%)
        paymentOptions: splitOptions,
      });
      const text = wrapper.text();
      // 9.720.000 × 0.4 = 3.888.000
      expect(text).toContain('$3.888.000');
      // 9.720.000 × 0.3 = 2.916.000
      expect(text).toContain('$2.916.000');
      // 3.888.000 + 2.916.000 + 2.916.000 === 9.720.000 (effective)
    });

    it('does not double-scale when stored descriptions are already effective-derived (Bug 87)', () => {
      // This is the production state for proposal 87 after a backend
      // _resync_investment_from_modules: descriptions saved at effective×pct.
      const storedAtEffective = [
        { label: '40% al firmar', description: '$3.888.000 COP' }, // already effective×0.4
        { label: '30% diseño',     description: '$2.916.000 COP' },
        { label: '30% final',      description: '$2.916.000 COP' },
      ];
      const wrapper = mountInvestment({
        totalInvestment: '$5.400.000',
        effectiveTotal: 9_720_000,
        paymentOptions: storedAtEffective,
      });
      const text = wrapper.text();
      // Same correct outputs as the base-derived case — no dependency on stored amount.
      expect(text).toContain('$3.888.000');
      expect(text).toContain('$2.916.000');
      // Old buggy behavior would have scaled $3.888.000 by 1.8 → $6.998.400.
      expect(text).not.toContain('$6.998.400');
    });

    it('falls back to base when no effectiveTotal prop is provided', () => {
      const wrapper = mountInvestment({
        totalInvestment: '$5.400.000',
        paymentOptions: splitOptions,
      });
      const text = wrapper.text();
      // 5.400.000 × 0.4 = 2.160.000
      expect(text).toContain('$2.160.000');
      // 5.400.000 × 0.3 = 1.620.000
      expect(text).toContain('$1.620.000');
    });

    it('leaves descriptions untouched when label has no parseable percent', () => {
      const wrapper = mountInvestment({
        totalInvestment: '$5.400.000',
        effectiveTotal: 9_720_000,
        paymentOptions: [
          { label: 'Cuota inicial fija', description: '$100.000 COP' },
        ],
      });
      // Free-form payment option should keep its original amount.
      expect(wrapper.text()).toContain('$100.000');
    });
  });
});

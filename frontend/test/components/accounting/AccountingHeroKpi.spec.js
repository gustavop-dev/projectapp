/**
 * Tests for AccountingHeroKpi.
 *
 * Covers: label + formatted value, tone class, clamped progressbar,
 * hidden progress, sparkline passthrough, and loading skeleton.
 */
import { mount } from '@vue/test-utils';
import AccountingHeroKpi from '../../../components/accounting/AccountingHeroKpi.vue';
import { formatMoney } from '../../../utils/formatMoney';

function mountHero(props = {}) {
  return mount(AccountingHeroKpi, {
    props: { label: 'Utilidad líquida 2026', value: 8400000, ...props },
  });
}

describe('AccountingHeroKpi', () => {
  it('renders the label and the formatted money value', () => {
    const wrapper = mountHero();

    expect(wrapper.text()).toContain('Utilidad líquida 2026');
    expect(wrapper.find('[data-testid="accounting-hero-value"]').text())
      .toBe(formatMoney(8400000, 'COP'));
  });

  it('applies the danger tone class to the value', () => {
    const wrapper = mountHero({ tone: 'danger', value: -100 });

    expect(wrapper.find('[data-testid="accounting-hero-value"]').classes())
      .toContain('text-danger-strong');
  });

  it('clamps the progressbar value between 0 and 100', () => {
    const wrapper = mountHero({ progress: 140, progressLabel: '140% recibido' });
    const bar = wrapper.find('[role="progressbar"]');

    expect(bar.attributes('aria-valuenow')).toBe('100');
    expect(wrapper.text()).toContain('140% recibido');
  });

  it('hides the progressbar when progress is null', () => {
    const wrapper = mountHero({ progress: null });

    expect(wrapper.find('[role="progressbar"]').exists()).toBe(false);
  });

  it('renders the sparkline when spark has at least 2 points', () => {
    const wrapper = mountHero({ spark: [1, 5, 3], sparkLabel: 'Utilidad mensual' });

    expect(wrapper.find('[data-testid="accounting-sparkline"]').exists()).toBe(true);
  });

  it('renders a skeleton without value while loading', () => {
    const wrapper = mountHero({ loading: true });

    expect(wrapper.find('[data-testid="accounting-hero-value"]').exists()).toBe(false);
    expect(wrapper.find('.motion-safe\\:animate-pulse').exists()).toBe(true);
  });
});

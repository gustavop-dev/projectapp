/**
 * Tests for AccountingSparkline.
 *
 * Covers: point normalization, flat-series midline, minimum-points guard,
 * accessibility roles, and stroke class passthrough.
 */
import { mount } from '@vue/test-utils';
import AccountingSparkline from '../../../components/accounting/AccountingSparkline.vue';

describe('AccountingSparkline', () => {
  it('normalizes points into the viewBox with 2px padding', () => {
    const wrapper = mount(AccountingSparkline, {
      props: { points: [0, 10], width: 120, height: 32 },
    });

    // min -> bottom (2 + 28), max -> top (2).
    expect(wrapper.find('polyline').attributes('points')).toBe('0,30 120,2');
  });

  it('draws a midline for a flat series', () => {
    const wrapper = mount(AccountingSparkline, {
      props: { points: [5, 5, 5], width: 100, height: 32 },
    });

    expect(wrapper.find('polyline').attributes('points')).toBe('0,16 50,16 100,16');
  });

  it('renders nothing with fewer than 2 numeric points', () => {
    const wrapper = mount(AccountingSparkline, { props: { points: [42] } });

    expect(wrapper.find('svg').exists()).toBe(false);
  });

  it('exposes role=img with the aria-label when provided', () => {
    const wrapper = mount(AccountingSparkline, {
      props: { points: [1, 2], ariaLabel: 'Utilidad mensual de 2026' },
    });
    const svg = wrapper.find('svg');

    expect(svg.attributes('role')).toBe('img');
    expect(svg.attributes('aria-label')).toBe('Utilidad mensual de 2026');
  });

  it('is marked decorative without an aria-label and applies strokeClass', () => {
    const wrapper = mount(AccountingSparkline, {
      props: { points: [1, 2], strokeClass: 'text-success-strong' },
    });
    const svg = wrapper.find('svg');

    expect(svg.attributes('aria-hidden')).toBe('true');
    expect(svg.classes()).toContain('text-success-strong');
  });
});

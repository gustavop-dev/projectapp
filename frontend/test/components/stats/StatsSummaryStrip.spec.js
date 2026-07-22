import { mount } from '@vue/test-utils';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';

describe('StatsSummaryStrip', () => {
  it('renders one cell per item with label, value and sub', () => {
    const wrapper = mount(StatsSummaryStrip, {
      props: {
        items: [
          { label: 'Total año', value: '$1.000.000 COP', sub: '12 registros' },
          { label: 'Promedio', value: '$83.333 COP' },
        ],
      },
    });

    const strip = wrapper.find('[data-testid="stats-summary-strip"]');
    expect(strip.exists()).toBe(true);
    expect(strip.text()).toContain('Total año');
    expect(strip.text()).toContain('$1.000.000 COP');
    expect(strip.text()).toContain('12 registros');
    expect(strip.text()).toContain('Promedio');
  });

  it('applies the tone class to the value', () => {
    const wrapper = mount(StatsSummaryStrip, {
      props: {
        items: [
          { label: 'Perdido', value: '$50.000 COP', tone: 'danger' },
          { label: 'Neutro', value: '$1 COP' },
        ],
      },
    });

    const values = wrapper.findAll('.tabular-nums');
    expect(values[0].classes()).toContain('text-danger-strong');
    expect(values[1].classes()).toContain('text-text-default');
  });
});

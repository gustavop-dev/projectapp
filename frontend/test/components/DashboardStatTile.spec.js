import { mount } from '@vue/test-utils';
import DashboardStatTile from '../../components/panel/dashboard/DashboardStatTile.vue';

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' },
  },
};

function mountTile(props = {}) {
  return mount(DashboardStatTile, {
    props: { label: 'Métrica', ...props },
    global: GLOBAL,
  });
}

describe('DashboardStatTile', () => {
  it('renders a dash when value is null', () => {
    const wrapper = mountTile({ value: null });

    expect(wrapper.find('[data-testid="dashboard-stat-value"]').text()).toBe('—');
  });

  it('formats currency values in es-CO', async () => {
    const wrapper = mountTile({ value: 1234567, format: 'currency' });
    // useAnimatedNumber starts at the initial target, so it renders directly.
    await wrapper.vm.$nextTick();

    expect(
      wrapper.find('[data-testid="dashboard-stat-value"]').text(),
    ).toBe('$1.234.567');
  });

  it('formats percent values keeping one decimal without count-up', () => {
    const wrapper = mountTile({ value: 95.2, format: 'percent' });

    expect(wrapper.find('[data-testid="dashboard-stat-value"]').text()).toBe('95.2%');
  });

  it('renders as a link when "to" is provided', () => {
    const wrapper = mountTile({ value: 3, to: '/panel/tasks' });

    expect(wrapper.find('a').exists()).toBe(true);
  });

  it('renders as a plain div without "to"', () => {
    const wrapper = mountTile({ value: 3 });

    expect(wrapper.find('a').exists()).toBe(false);
  });

  it('hides the sparkline below two points and shows it with enough data', () => {
    const single = mountTile({ value: 1, sparkline: [5] });
    const full = mountTile({ value: 1, sparkline: [5, 8, 3] });

    expect(single.find('[data-testid="accounting-sparkline"]').exists()).toBe(false);
    expect(full.find('[data-testid="accounting-sparkline"]').exists()).toBe(true);
  });

  it('applies the tone class to the value', () => {
    const wrapper = mountTile({ value: 2, tone: 'danger' });

    expect(
      wrapper.find('[data-testid="dashboard-stat-value"]').classes(),
    ).toContain('text-danger-strong');
  });
});

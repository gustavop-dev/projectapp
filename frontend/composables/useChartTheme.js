import { computed } from 'vue';
import { useDarkMode } from '~/composables/useDarkMode';

/**
 * Chart theming for the accounting ApexCharts.
 *
 * Series colors are fixed steps of the design-system ramps, validated
 * per mode with the dataviz palette validator (lightness band, chroma
 * floor, CVD separation and 3:1 contrast against each surface):
 * - measures: Esperado (blue) / Líquido (emerald) / Gastos (red)
 * - categorical: fixed order for per-card series (never cycled)
 * Text/grid inks come from the theme tokens so charts follow the mode.
 */
const LIGHT = {
  measures: ['#1D4ED8', '#059669', '#B91C1C'],
  categorical: ['#1D4ED8', '#B45309', '#059669', '#7C3AED'],
  text: '#6B7280',        // --color-text-muted (light)
  grid: '#F3F4F6',        // --color-border-muted (light)
};

const DARK = {
  measures: ['#3B82F6', '#059669', '#EF4444'],
  categorical: ['#3B82F6', '#D97706', '#059669', '#8B5CF6'],
  text: '#D1D5DB',        // --color-text-muted (dark)
  grid: 'rgba(255, 255, 255, 0.06)',  // --color-border-muted (dark)
};

export function useChartTheme() {
  const { isDark } = useDarkMode();

  const palette = computed(() => (isDark.value ? DARK : LIGHT));

  const baseOptions = computed(() => ({
    chart: {
      fontFamily: 'inherit',
      background: 'transparent',
      toolbar: { show: false },
      zoom: { enabled: false },
    },
    foreColor: palette.value.text,
    grid: { borderColor: palette.value.grid, strokeDashArray: 3 },
    stroke: { curve: 'smooth', width: 2 },
    dataLabels: { enabled: false },
    legend: {
      position: 'top',
      horizontalAlign: 'left',
      fontSize: '12px',
      markers: { size: 5 },
    },
    tooltip: { theme: isDark.value ? 'dark' : 'light' },
  }));

  return { isDark, palette, baseOptions };
}

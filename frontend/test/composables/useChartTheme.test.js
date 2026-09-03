import { ref } from 'vue';

let mockIsDark;
let mockReducedMotion;

jest.mock('../../composables/useDarkMode', () => ({
  useDarkMode: () => ({ isDark: mockIsDark }),
}));
jest.mock('../../composables/useReducedMotion', () => ({
  useReducedMotion: () => ({ reducedMotion: mockReducedMotion }),
}));

import { useChartTheme } from '../../composables/useChartTheme';

describe('useChartTheme', () => {
  beforeEach(() => {
    mockIsDark = ref(false);
    mockReducedMotion = ref(false);
  });

  it('places foreground contrast in the Apex chart contract', () => {
    const { baseOptions, palette } = useChartTheme();

    expect(baseOptions.value.chart.foreColor).toBe(palette.value.text);
    expect(baseOptions.value.foreColor).toBeUndefined();
  });

  it('uses the foreground contrast for legend labels', () => {
    const { baseOptions, palette } = useChartTheme();

    expect(baseOptions.value.legend.labels.colors).toBe(palette.value.text);
  });

  it('switches Apex theme mode with dark mode', () => {
    const { baseOptions } = useChartTheme();

    mockIsDark.value = true;

    expect(baseOptions.value.theme.mode).toBe('dark');
    expect(baseOptions.value.tooltip.theme).toBe('dark');
  });
});

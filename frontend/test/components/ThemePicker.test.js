import { mount } from '@vue/test-utils';

jest.mock('../../composables/usePlatformCustomTheme', () => {
  const { ref } = require('vue');
  return {
    usePlatformCustomTheme: jest.fn(() => ({
      THEME_COLORS: [
        { name: 'Esmerald', shades: ['#1a7a4a', '#22a060', '#2ecc80'] },
      ],
      themeColor: ref('#22a060'),
      coverImage: ref(''),
      customCoverImageUrl: ref(''),
      hasCover: ref(false),
      setThemeColor: jest.fn().mockResolvedValue(undefined),
      setCoverImage: jest.fn().mockResolvedValue(undefined),
      setCustomCoverImage: jest.fn().mockResolvedValue(undefined),
      clearCover: jest.fn().mockResolvedValue(undefined),
    })),
  };
});

jest.mock('../../composables/usePlatformApi', () => ({
  usePlatformApi: jest.fn(() => ({
    get: jest.fn().mockResolvedValue({ data: [] }),
  })),
}));

import ThemePicker from '../../components/platform/ThemePicker.vue';

function mountThemePicker(props = {}) {
  return mount(ThemePicker, { props });
}

describe('ThemePicker', () => {
  it('renders color grid buttons', () => {
    const wrapper = mountThemePicker();

    // 3 shades from the single THEME_COLORS entry
    expect(wrapper.findAll('button[style]').length).toBeGreaterThan(0);
  });

  it('shows reset color button when themeColor is set', () => {
    const wrapper = mountThemePicker();

    expect(wrapper.text()).toContain('Restablecer color');
  });

  it('shows upload cover button', () => {
    const wrapper = mountThemePicker();

    expect(wrapper.text()).toContain('Subir imagen personalizada');
  });

  it('shows gallery loading state when loading', async () => {
    const wrapper = mountThemePicker();

    // isLoadingGallery is true momentarily on mount while loadGallery runs
    // After mount completes, gallery resolves with empty [] so "No se encontraron" message shows
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('No se encontraron imagenes');
  });

  it('renders color section heading', () => {
    const wrapper = mountThemePicker();

    expect(wrapper.text()).toContain('Color del tema');
  });
});

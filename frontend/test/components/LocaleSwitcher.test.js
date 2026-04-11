import { mount } from '@vue/test-utils';

const mockSwitchLocale = jest.fn();
const mockIsActiveLocale = jest.fn((code) => code === 'es-co');

jest.mock('../../composables/useLocaleNavigation', () => ({
  useLocaleNavigation: jest.fn(() => ({
    switchLocale: mockSwitchLocale,
    isActiveLocale: mockIsActiveLocale,
    availableLocales: require('vue').ref([
      { code: 'es-co', name: 'Español', flag: '🇨🇴' },
      { code: 'en-us', name: 'English', flag: '🇺🇸' },
    ]),
  })),
}));

jest.mock('../../stores/language', () => ({
  useLanguageStore: jest.fn(() => ({ currentLocale: 'es-co' })),
}));

import LocaleSwitcher from '../../components/LocaleSwitcher.vue';

function mountSwitcher() {
  return mount(LocaleSwitcher);
}

describe('LocaleSwitcher', () => {
  beforeEach(() => {
    mockSwitchLocale.mockClear();
  });

  it('renders the current locale name', () => {
    const wrapper = mountSwitcher();

    expect(wrapper.text()).toContain('Español');
  });

  it('opens the dropdown when the toggle button is clicked', async () => {
    const wrapper = mountSwitcher();

    await wrapper.find('.locale-button').trigger('click');

    expect(wrapper.find('.dropdown-menu').exists()).toBe(true);
  });

  it('renders all available locales in the dropdown', async () => {
    const wrapper = mountSwitcher();

    await wrapper.find('.locale-button').trigger('click');

    const options = wrapper.findAll('.locale-option');
    expect(options).toHaveLength(2);
  });

  it('calls switchLocale when a non-active locale option is clicked', async () => {
    const wrapper = mountSwitcher();

    await wrapper.find('.locale-button').trigger('click');

    const options = wrapper.findAll('.locale-option');
    await options[1].trigger('click'); // en-us is not active

    expect(mockSwitchLocale).toHaveBeenCalledWith('en-us');
  });

  it('closes the dropdown after selecting a locale', async () => {
    const wrapper = mountSwitcher();

    await wrapper.find('.locale-button').trigger('click');
    const options = wrapper.findAll('.locale-option');
    await options[1].trigger('click');

    expect(wrapper.find('.dropdown-menu').exists()).toBe(false);
  });
});

import { mount } from '@vue/test-utils';
import { ref } from 'vue';

global.useLocalePath = jest.fn(() => (path) => path);
global.useI18n = jest.fn(() => ({ locale: ref('es-co') }));

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({ messages: require('vue').ref(null) })),
}));

import PrivacyPolicy from '../../components/pages/PrivacyPolicy.vue';

function mountPage() {
  return mount(PrivacyPolicy, {
    global: {
      stubs: { NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' } },
    },
  });
}

describe('PrivacyPolicy', () => {
  it('renders a main element', () => {
    const wrapper = mountPage();

    expect(wrapper.find('main').exists()).toBe(true);
  });

  it('renders the fallback title when messages are not loaded', () => {
    const wrapper = mountPage();

    expect(wrapper.text()).toContain('Privacy Policy');
  });

  it('renders the default contact email link', () => {
    const wrapper = mountPage();

    expect(wrapper.find('a[href="mailto:team@projectapp.co"]').exists()).toBe(true);
  });

  it('renders the Spanish back label when locale is es-co', () => {
    const wrapper = mountPage();

    expect(wrapper.text()).toContain('Volver al inicio');
  });
});

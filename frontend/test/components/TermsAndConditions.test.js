import { mount } from '@vue/test-utils';
import { ref } from 'vue';

global.useLocalePath = jest.fn(() => (path) => path);
global.useI18n = jest.fn(() => ({ locale: ref('en-us') }));

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({ messages: require('vue').ref(null) })),
}));

import TermsAndConditions from '../../components/pages/TermsAndConditions.vue';

function mountPage() {
  return mount(TermsAndConditions, {
    global: {
      stubs: { NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' } },
    },
  });
}

describe('TermsAndConditions', () => {
  it('renders a main element', () => {
    const wrapper = mountPage();

    expect(wrapper.find('main').exists()).toBe(true);
  });

  it('renders the fallback title when messages are not loaded', () => {
    const wrapper = mountPage();

    expect(wrapper.text()).toContain('Terms and Conditions');
  });

  it('renders the default contact email link', () => {
    const wrapper = mountPage();

    expect(wrapper.find('a[href="mailto:team@projectapp.co"]').exists()).toBe(true);
  });

  it('renders the English back label when locale is en-us', () => {
    const wrapper = mountPage();

    expect(wrapper.text()).toContain('Back to home');
  });
});

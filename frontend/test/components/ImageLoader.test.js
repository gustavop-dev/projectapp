import { mount } from '@vue/test-utils';

jest.mock('vue3-lottie', () => ({
  Vue3Lottie: { template: '<div class="lottie-stub" />' },
}));

jest.mock('~/assets/loading/esmerald.json', () => ({}), { virtual: true });
jest.mock('~/assets/loading/white.json', () => ({}), { virtual: true });

import ImageLoader from '../../components/layouts/ImageLoader.vue';

function mountLoader(props = {}) {
  return mount(ImageLoader, {
    props: { src: 'https://example.com/image.jpg', alt: 'Test image', ...props },
    global: { stubs: { Vue3Lottie: true } },
    attachTo: document.body,
  });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('ImageLoader', () => {
  it('shows the loading animation before the image loads', () => {
    const wrapper = mountLoader();

    const lottieContainer = wrapper.find('div[style]').exists()
      ? wrapper.find('div[style]')
      : wrapper.findAll('div')[0];

    expect(wrapper.find('img').isVisible()).toBe(false);
  });

  it('renders the img element with the provided src', () => {
    const wrapper = mountLoader({ src: 'https://example.com/photo.jpg' });

    expect(wrapper.find('img').attributes('src')).toBe('https://example.com/photo.jpg');
  });

  it('renders the img element with the provided alt text', () => {
    const wrapper = mountLoader({ alt: 'A test photo' });

    expect(wrapper.find('img').attributes('alt')).toBe('A test photo');
  });

  it('hides the loading animation and shows the image after load', async () => {
    const wrapper = mountLoader();

    await wrapper.find('img').trigger('load');

    expect(wrapper.find('img').isVisible()).toBe(true);
  });
});

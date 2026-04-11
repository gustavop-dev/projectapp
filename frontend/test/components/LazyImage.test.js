import { mount } from '@vue/test-utils';

jest.mock('../../composables/useIntersectionObserver', () => ({
  useIntersectionObserver: jest.fn(() => ({
    observe: jest.fn((el, cb) => cb()),
    unobserve: jest.fn(),
  })),
}));

jest.mock('../../composables/useAssetCache', () => ({
  useAssetCache: jest.fn(() => ({
    getAsset: jest.fn(() => Promise.resolve(null)),
  })),
}));

import LazyImage from '../../components/layouts/LazyImage.vue';

function mountLazyImage(props = {}) {
  return mount(LazyImage, {
    props: { src: '/images/test.jpg', alt: 'Test image', ...props },
  });
}

describe('LazyImage', () => {
  it('renders the image container', () => {
    const wrapper = mountLazyImage();

    expect(wrapper.find('.lazy-image-container').exists()).toBe(true);
  });

  it('shows the placeholder before the image loads', () => {
    const wrapper = mountLazyImage();

    expect(wrapper.find('.placeholder').exists()).toBe(true);
  });

  it('renders the img element with the correct src', async () => {
    const wrapper = mountLazyImage();

    // Wait for the async loadImage to complete
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('img').attributes('src')).toBe('/images/test.jpg');
  });

  it('renders the img element with the correct alt text', () => {
    const wrapper = mountLazyImage({ alt: 'My image' });

    expect(wrapper.find('img').attributes('alt')).toBe('My image');
  });

  it('hides the placeholder after the image loads', async () => {
    const wrapper = mountLazyImage();
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    await wrapper.find('img').trigger('load');

    expect(wrapper.find('.placeholder').exists()).toBe(false);
  });
});

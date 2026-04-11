import { mount } from '@vue/test-utils';
import VideoModal from '../../components/VideoModal.vue';

beforeAll(() => {
  HTMLVideoElement.prototype.play = jest.fn(() => Promise.resolve());
  HTMLVideoElement.prototype.pause = jest.fn();
});

function mountModal(props = {}) {
  return mount(VideoModal, {
    props: { isOpen: false, videoSrc: 'https://example.com/video.mp4', ...props },
    global: { stubs: { Teleport: true, Transition: true } },
  });
}

describe('VideoModal', () => {
  it('renders the video element when isOpen is true', () => {
    const wrapper = mountModal({ isOpen: true });

    expect(wrapper.find('video').exists()).toBe(true);
  });

  it('does not render the modal content when isOpen is false', () => {
    const wrapper = mountModal({ isOpen: false });

    expect(wrapper.find('video').exists()).toBe(false);
  });

  it('renders the video with the provided videoSrc', () => {
    const wrapper = mountModal({ isOpen: true });

    expect(wrapper.find('video').attributes('src')).toBe('https://example.com/video.mp4');
  });

  it('emits close when the close button is clicked', async () => {
    const wrapper = mountModal({ isOpen: true });

    await wrapper.find('button[aria-label="Close video"]').trigger('click');

    expect(wrapper.emitted('close')).toHaveLength(1);
  });

  it('emits close when the Escape key is pressed', async () => {
    const wrapper = mountModal({ isOpen: true });

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));

    expect(wrapper.emitted('close')).toHaveLength(1);
  });
});

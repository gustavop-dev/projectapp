import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import ReadingProgressBar from '../../components/blog/ReadingProgressBar.vue';

function mountBar(props = {}) {
  return mount(ReadingProgressBar, {
    props: { readTimeMinutes: 5, lang: 'es', ...props },
    global: { stubs: { Transition: true } },
  });
}

function simulateScroll(scrollY, scrollHeight, clientHeight) {
  Object.defineProperty(window, 'scrollY', { value: scrollY, configurable: true });
  Object.defineProperty(document.documentElement, 'scrollHeight', { value: scrollHeight, configurable: true });
  Object.defineProperty(document.documentElement, 'clientHeight', { value: clientHeight, configurable: true });
  window.dispatchEvent(new Event('scroll'));
}

afterEach(() => {
  Object.defineProperty(window, 'scrollY', { value: 0, configurable: true });
});

describe('ReadingProgressBar', () => {
  it('renders the progress bar with an initial width of 0%', () => {
    const wrapper = mountBar();

    expect(wrapper.find('[style*="width"]').attributes('style')).toContain('width: 0%');
  });

  it('shows "restantes" in Spanish when scrolled between 5% and 95%', async () => {
    const wrapper = mountBar({ lang: 'es' });

    simulateScroll(400, 1000, 500); // 80% of scrollable area
    await nextTick();

    expect(wrapper.text()).toContain('restantes');
  });

  it('shows "remaining" in English when scrolled between 5% and 95%', async () => {
    const wrapper = mountBar({ lang: 'en' });

    simulateScroll(400, 1000, 500);
    await nextTick();

    expect(wrapper.text()).toContain('remaining');
  });

  it('hides the remaining time indicator at the start before any scroll', () => {
    const wrapper = mountBar();

    expect(wrapper.text()).not.toContain('min');
  });
});

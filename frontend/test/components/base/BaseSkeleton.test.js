import { mount } from '@vue/test-utils';
import BaseSkeleton from '../../../components/base/BaseSkeleton.vue';

describe('BaseSkeleton', () => {
  it('renders a line placeholder by default, hidden from assistive tech', () => {
    const wrapper = mount(BaseSkeleton);
    expect(wrapper.classes()).toContain('h-3');
    expect(wrapper.classes()).toContain('motion-safe:animate-pulse');
    expect(wrapper.attributes('aria-hidden')).toBe('true');
  });

  it.each([
    ['card', 'rounded-xl'],
    ['circle', 'rounded-full'],
  ])('applies the %s variant shape', (variant, expectedClass) => {
    const wrapper = mount(BaseSkeleton, { props: { variant } });
    expect(wrapper.classes()).toContain(expectedClass);
  });
});

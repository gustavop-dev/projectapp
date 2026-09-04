import { mount } from '@vue/test-utils';
import ReceivableConfidenceDot from '~/components/accounting/ReceivableConfidenceDot.vue';

describe('ReceivableConfidenceDot', () => {
  it.each([
    ['high', 'bg-success-strong'],
    ['medium', 'bg-warning-strong'],
    ['low', 'bg-danger-strong'],
    ['', 'bg-text-subtle'],
  ])('renders the semantic tone for %s confidence', (confidence, expectedClass) => {
    const wrapper = mount(ReceivableConfidenceDot, { props: { confidence } });

    expect(wrapper.classes()).toContain(expectedClass);
    expect(wrapper.attributes('aria-hidden')).toBe('true');
  });
});

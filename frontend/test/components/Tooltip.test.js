import { mount } from '@vue/test-utils';
import Tooltip from '../../components/base/BaseTooltip.vue';

let outsideHandler = null;

jest.mock('@vueuse/core', () => ({
  onClickOutside: jest.fn((_, handler) => {
    outsideHandler = handler;
  }),
}));

function mountTooltip(props = {}) {
  outsideHandler = null;
  return mount(Tooltip, {
    props: { position: 'top', ...props },
    slots: { default: '<span>tip text</span>' },
    // Stub Transition to avoid leave-animation holding elements in DOM in jsdom
    global: { stubs: { Transition: true } },
  });
}

describe('Tooltip', () => {
  it('does not render tooltip content by default', () => {
    const wrapper = mountTooltip();

    expect(wrapper.text()).not.toContain('tip text');
  });

  it('shows tooltip after pointerenter from a non-touch pointer', async () => {
    const wrapper = mountTooltip();

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'mouse' });

    expect(wrapper.text()).toContain('tip text');
  });

  it('hides tooltip after pointerleave from a non-touch pointer', async () => {
    const wrapper = mountTooltip();

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'mouse' });
    await wrapper.find('.cursor-help').trigger('pointerleave', { pointerType: 'mouse' });

    expect(wrapper.text()).not.toContain('tip text');
  });

  it('does not show tooltip after pointerenter from a touch pointer', async () => {
    const wrapper = mountTooltip();

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'touch' });

    expect(wrapper.text()).not.toContain('tip text');
  });

  it('toggles tooltip visibility on click', async () => {
    const wrapper = mountTooltip();

    await wrapper.find('.cursor-help').trigger('click');
    expect(wrapper.text()).toContain('tip text');

    await wrapper.find('.cursor-help').trigger('click');
    expect(wrapper.text()).not.toContain('tip text');
  });

  it('applies bottom-full class to the tooltip bubble when position is top', async () => {
    const wrapper = mountTooltip({ position: 'top' });

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'mouse' });

    const bubble = wrapper.find('.absolute.z-10');
    expect(bubble.classes()).toContain('bottom-full');
    expect(bubble.classes()).toContain('mb-2');
  });

  it('applies top-full class to the tooltip bubble when position is bottom', async () => {
    const wrapper = mountTooltip({ position: 'bottom' });

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'mouse' });

    const bubble = wrapper.find('.absolute.z-10');
    expect(bubble.classes()).toContain('top-full');
    expect(bubble.classes()).toContain('mt-2');
  });

  it('applies right-full class to the tooltip bubble when position is left', async () => {
    const wrapper = mountTooltip({ position: 'left' });

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'mouse' });

    const bubble = wrapper.find('.absolute.z-10');
    expect(bubble.classes()).toContain('right-full');
    expect(bubble.classes()).toContain('mr-2');
  });

  it('applies left-full class to the tooltip bubble when position is right', async () => {
    const wrapper = mountTooltip({ position: 'right' });

    await wrapper.find('.cursor-help').trigger('pointerenter', { pointerType: 'mouse' });

    const bubble = wrapper.find('.absolute.z-10');
    expect(bubble.classes()).toContain('left-full');
    expect(bubble.classes()).toContain('ml-2');
  });
});

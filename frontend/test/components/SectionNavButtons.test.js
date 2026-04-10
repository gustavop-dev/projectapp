import { mount } from '@vue/test-utils';
import SectionNavButtons from '../../components/BusinessProposal/SectionNavButtons.vue';

function mountNav(props = {}) {
  return mount(SectionNavButtons, {
    props: {
      prevTitle: 'Anterior',
      nextTitle: 'Siguiente',
      isFirst: false,
      isLast: false,
      hideLeft: false,
      blinkNext: false,
      blinkPrev: false,
      ...props,
    },
  });
}

describe('SectionNavButtons', () => {
  it('renders the previous button when the section is not first', () => {
    const wrapper = mountNav({ isFirst: false });

    expect(wrapper.find('[data-testid="nav-prev"]').exists()).toBe(true);
  });

  it('hides the previous button when isFirst is true', () => {
    const wrapper = mountNav({ isFirst: true });

    expect(wrapper.find('[data-testid="nav-prev"]').exists()).toBe(false);
  });

  it('hides the previous button when hideLeft is true', () => {
    const wrapper = mountNav({ hideLeft: true });

    expect(wrapper.find('[data-testid="nav-prev"]').exists()).toBe(false);
  });

  it('emits prev when the previous button is clicked', async () => {
    const wrapper = mountNav();

    await wrapper.get('[data-testid="nav-prev"]').trigger('click');

    expect(wrapper.emitted('prev')).toHaveLength(1);
  });

  it('renders the next button when the section is not last', () => {
    const wrapper = mountNav({ isLast: false });

    expect(wrapper.find('[data-testid="nav-next"]').exists()).toBe(true);
  });

  it('hides the next button when isLast is true', () => {
    const wrapper = mountNav({ isLast: true });

    expect(wrapper.find('[data-testid="nav-next"]').exists()).toBe(false);
  });

  it('emits next when the next button is clicked', async () => {
    const wrapper = mountNav();

    await wrapper.get('[data-testid="nav-next"]').trigger('click');

    expect(wrapper.emitted('next')).toHaveLength(1);
  });

  it('applies nav-blink class to the previous button when blinkPrev is true', () => {
    const wrapper = mountNav({ blinkPrev: true });

    expect(wrapper.get('[data-testid="nav-prev"]').classes()).toContain('nav-blink');
  });

  it('applies nav-blink class to the next button when blinkNext is true', () => {
    const wrapper = mountNav({ blinkNext: true });

    expect(wrapper.get('[data-testid="nav-next"]').classes()).toContain('nav-blink');
  });
});

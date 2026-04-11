import { mount } from '@vue/test-utils';

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      study_cases: {
        title: 'Design and code made Simple',
        subtitle: 'Our team of experts is here to help',
        visit_project: 'Visit Project',
        taptag: { watch_video: 'Watch video' },
      },
    }),
  })),
}));

import StudyCases from '../../components/home/StudyCases.vue';

function mountStudyCases() {
  return mount(StudyCases, {
    global: {
      stubs: {
        ClientOnly: { template: '<div><slot /></div>' },
        AnimatedTestimonials: { template: '<div class="animated-testimonials-stub" />' },
        VideoModal: true,
      },
    },
  });
}

describe('StudyCases', () => {
  it('renders the section element', () => {
    const wrapper = mountStudyCases();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the section title', () => {
    const wrapper = mountStudyCases();

    expect(wrapper.text()).toContain('Design and code made Simple');
  });

  it('renders the subtitle', () => {
    const wrapper = mountStudyCases();

    expect(wrapper.text()).toContain('Our team of experts is here to help');
  });

  it('renders the AnimatedTestimonials component area', () => {
    const wrapper = mountStudyCases();

    expect(wrapper.find('.animated-testimonials-stub').exists()).toBe(true);
  });
});

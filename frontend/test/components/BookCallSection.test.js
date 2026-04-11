import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));
global.useLocalePath = jest.fn(() => (path) => path);

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: {
      book_call: {
        title: 'Book a 15-min intro call',
        cta: "Let's Talk",
        prefer_email: 'Prefer to email?',
        say_hi: 'Say hi!',
      },
    },
  })),
}));

import BookCallSection from '../../components/home/BookCallSection.vue';

function mountSection() {
  return mount(BookCallSection);
}

describe('BookCallSection', () => {
  it('renders the section element', () => {
    const wrapper = mountSection();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the book call title', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain('Book a 15-min intro call');
  });

  it('renders the CTA button', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain("Let's Talk");
  });

  it('renders two cards in the grid', () => {
    const wrapper = mountSection();

    // Two card divs inside the grid
    const grid = wrapper.find('.grid');
    expect(grid.exists()).toBe(true);
    expect(grid.findAll(':scope > div')).toHaveLength(2);
  });

  it('renders the Say hi! button', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain('Say hi!');
  });
});

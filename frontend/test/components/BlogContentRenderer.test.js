import { mount } from '@vue/test-utils';
import BlogContentRenderer from '../../components/blog/BlogContentRenderer.vue';

const sampleContentJson = {
  intro: 'This is the introduction paragraph.',
  sections: [
    {
      heading: 'Section One Heading',
      content: 'Content for section one.',
    },
    {
      heading: 'Section with List',
      list: ['List item A', 'List item B'],
    },
    {
      heading: 'Section with Subsections',
      subsections: [
        { title: 'Sub One', description: 'Sub one description.' },
      ],
    },
  ],
  conclusion: 'Final conclusion text.',
  cta: 'Contact us today.',
};

describe('BlogContentRenderer', () => {
  it('renders intro text from contentJson', () => {
    const wrapper = mount(BlogContentRenderer, {
      props: { contentJson: sampleContentJson },
    });

    expect(wrapper.text()).toContain('This is the introduction paragraph.');
  });

  it('renders section headings', () => {
    const wrapper = mount(BlogContentRenderer, {
      props: { contentJson: sampleContentJson },
    });

    expect(wrapper.text()).toContain('Section One Heading');
  });

  it('renders list items', () => {
    const wrapper = mount(BlogContentRenderer, {
      props: { contentJson: sampleContentJson },
    });

    expect(wrapper.text()).toContain('List item A');
    expect(wrapper.text()).toContain('List item B');
  });

  it('renders the conclusion block', () => {
    const wrapper = mount(BlogContentRenderer, {
      props: { contentJson: sampleContentJson },
    });

    expect(wrapper.text()).toContain('Final conclusion text.');
  });

  it('renders htmlContent fallback when contentJson has no intro or sections', () => {
    const wrapper = mount(BlogContentRenderer, {
      props: { htmlContent: '<p>Fallback HTML content</p>' },
    });

    expect(wrapper.html()).toContain('Fallback HTML content');
  });
});

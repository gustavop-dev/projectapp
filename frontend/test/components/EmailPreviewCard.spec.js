import { mount } from '@vue/test-utils';
import EmailPreviewCard from '../../components/EmailPreviewCard.vue';

describe('EmailPreviewCard', () => {
  it('renders greeting, sections and footer', () => {
    const wrapper = mount(EmailPreviewCard, {
      props: {
        greeting: 'Hola Ana',
        sections: [{ id: 1, text: 'Primera sección' }, { id: 2, text: 'Segunda' }],
        footer: 'Un abrazo',
        attachments: [],
      },
    });
    expect(wrapper.text()).toContain('Hola Ana');
    expect(wrapper.text()).toContain('Primera sección');
    expect(wrapper.text()).toContain('Segunda');
    expect(wrapper.text()).toContain('Un abrazo');
    expect(wrapper.text()).toContain('Project App.');
  });

  it('shows placeholders for empty greeting/sections', () => {
    const wrapper = mount(EmailPreviewCard, {
      props: { greeting: '', sections: [{ id: 1, text: '' }], footer: '', attachments: [] },
    });
    expect(wrapper.text()).toContain('(sin saludo)');
    expect(wrapper.text()).toContain('(sección vacía)');
  });

  it('lists attachment names when present', () => {
    const wrapper = mount(EmailPreviewCard, {
      props: { greeting: 'Hola', sections: [], footer: '', attachments: [{ name: 'contrato.pdf' }] },
    });
    expect(wrapper.text()).toContain('Archivos adjuntos');
    expect(wrapper.text()).toContain('contrato.pdf');
  });
});

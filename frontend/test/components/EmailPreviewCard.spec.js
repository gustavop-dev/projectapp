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
  });

  it('mirrors the branded template design (not the legacy green card)', () => {
    const wrapper = mount(EmailPreviewCard, {
      props: { greeting: 'Hola', sections: [], footer: '', attachments: [] },
    });
    // Brand marks of emails/branded_email.html
    expect(wrapper.text()).toContain('App.');
    expect(wrapper.text()).toContain('Mensaje del equipo');
    expect(wrapper.text()).toContain('Equipo · Proyecto');
    expect(wrapper.text()).toContain('Cualquier cosa, respóndenos directo a este correo.');
    expect(wrapper.text()).toContain('projectapp.co');
    expect(wrapper.text()).toContain('team@projectapp.co');
    expect(wrapper.text()).toContain('© 2026 ProjectApp · Desarrollo de software a la medida · Bogotá, Colombia');
    // Legacy green design must be gone
    expect(wrapper.html()).not.toContain('#059669');
    expect(wrapper.text()).not.toContain('Transformación Digital');
  });

  it('falls back to "Hola" like the Django template when greeting is empty', () => {
    const wrapper = mount(EmailPreviewCard, {
      props: { greeting: '', sections: [{ id: 1, text: '' }], footer: '', attachments: [] },
    });
    expect(wrapper.text()).toContain('Hola.');
    expect(wrapper.text()).toContain('(sección vacía)');
  });

  it('lists attachment names when present', () => {
    const wrapper = mount(EmailPreviewCard, {
      props: { greeting: 'Hola', sections: [], footer: '', attachments: [{ name: 'contrato.pdf' }] },
    });
    expect(wrapper.text()).toContain('contrato.pdf');
  });

  it('renders the default signature and accepts overrides', () => {
    const withDefaults = mount(EmailPreviewCard, {
      props: { greeting: 'Hola', sections: [], footer: '', attachments: [] },
    });
    expect(withDefaults.text()).toContain('Vanessa Rodríguez');
    expect(withDefaults.text()).toContain('Asistente Comercial · ProjectApp.');

    const overridden = mount(EmailPreviewCard, {
      props: {
        greeting: 'Hola',
        sections: [],
        footer: '',
        attachments: [],
        signatureName: 'Gustavo Pérez',
        signatureRole: 'CEO · ProjectApp.',
      },
    });
    expect(overridden.text()).toContain('Gustavo Pérez');
    expect(overridden.text()).toContain('CEO · ProjectApp.');
  });
});

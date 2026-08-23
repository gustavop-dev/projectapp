import { mount } from '@vue/test-utils';
import EmailHistoryList from '../../components/EmailHistoryList.vue';

const entry = {
  id: 7,
  subject: 'Seguimiento',
  recipient: 'ana@example.com',
  status: 'sent',
  sent_at: '2026-04-01T10:00:00Z',
  metadata: { greeting: 'Hola Ana', sections: ['Primer bloque'], footer: 'Saludos', attachment_names: ['x.pdf'] },
  copies: [],
};

describe('EmailHistoryList', () => {
  it('shows the empty label when there is no history', () => {
    const wrapper = mount(EmailHistoryList, {
      props: { history: [], loading: false, hasNextPage: false, emptyLabel: 'Sin correos.' },
    });
    expect(wrapper.text()).toContain('Sin correos.');
  });

  it('renders each entry with subject, recipient and status label', () => {
    const wrapper = mount(EmailHistoryList, { props: { history: [entry] } });
    expect(wrapper.text()).toContain('Seguimiento');
    expect(wrapper.text()).toContain('ana@example.com');
    expect(wrapper.text()).toContain('Enviado');
  });

  it('toggles the entry body via aria-hidden (BaseCollapse stays in the DOM)', async () => {
    const wrapper = mount(EmailHistoryList, { props: { history: [entry] } });
    const body = () => wrapper.findAll('[aria-hidden]').find((n) => n.text().includes('Primer bloque'));
    expect(body().attributes('aria-hidden')).toBe('true');

    await wrapper.find('button').trigger('click');
    expect(body().attributes('aria-hidden')).toBe('false');
  });

  it('emits load-more when the pagination button is clicked', async () => {
    const wrapper = mount(EmailHistoryList, { props: { history: [entry], hasNextPage: true } });
    const loadMore = wrapper.findAll('button').find((b) => b.text().includes('Cargar más'));
    await loadMore.trigger('click');
    expect(wrapper.emitted('load-more')).toHaveLength(1);
  });

  it('renders the entry-meta slot', () => {
    const wrapper = mount(EmailHistoryList, {
      props: { history: [entry] },
      slots: { 'entry-meta': '<span>· Plantilla</span>' },
    });
    expect(wrapper.text()).toContain('· Plantilla');
  });

  it('shows a failed BCC attempt inside the expanded entry', async () => {
    const copy = {
      id: 12,
      recipient: 'audit@example.com',
      status: 'failed',
      error_message: 'SMTP timeout',
    };
    const wrapper = mount(EmailHistoryList, {
      props: { history: [{ ...entry, copies: [copy] }] },
    });

    await wrapper.find('button').trigger('click');

    const copies = wrapper.get('[data-testid="email-copy-list-7"]');
    expect(copies.text()).toContain('audit@example.com');
    expect(copies.text()).toContain('SMTP timeout');
  });
});

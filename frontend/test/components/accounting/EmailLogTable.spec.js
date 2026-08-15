import { mount } from '@vue/test-utils';
import EmailLogTable from '~/components/accounting/EmailLogTable.vue';

const SENT = {
  id: 1,
  template_key: 'accounting_change',
  template_label: 'Cambio contable',
  recipient: 'ana@test.com',
  subject: '[Contabilidad] Hosting creado: Kore',
  status: 'sent',
  status_label: 'Enviado',
  error_message: '',
  sent_at: '2026-08-15T09:00:00-05:00',
  targets: [
    {
      entity_type: 'hosting',
      entity_type_label: 'Hosting',
      object_id: 4,
      object_repr: 'Kore',
    },
  ],
  has_body: true,
  is_retryable: false,
  retry_blocked_reason: '',
  retry_of: null,
};

const FAILED = {
  ...SENT,
  id: 2,
  recipient: 'zoe@test.com',
  status: 'failed',
  status_label: 'Fallido',
  error_message: 'SMTP timeout',
  has_body: false,
  is_retryable: true,
};

const DIGEST_FAILED = {
  ...FAILED,
  id: 3,
  template_key: 'accounting_payment_calendar',
  template_label: 'Calendario de cobros y pagos',
  is_retryable: false,
  retry_blocked_reason: 'Este aviso resume varios registros del día.',
};

function mountTable(entries, props = {}) {
  return mount(EmailLogTable, { props: { entries, ...props } });
}

describe('EmailLogTable', () => {
  it('offers the message only for the sends that kept one', () => {
    const wrapper = mountTable([SENT, FAILED]);

    expect(wrapper.find('[data-testid="email-log-view-body-1"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="email-log-view-body-2"]').exists()).toBe(false);
  });

  it('emits the row when the message is opened', async () => {
    const wrapper = mountTable([SENT]);

    await wrapper.get('[data-testid="email-log-view-body-1"]').trigger('click');

    expect(wrapper.emitted('view-body')[0]).toEqual([SENT]);
  });

  it('offers a retry only on a failure', () => {
    const wrapper = mountTable([SENT, FAILED]);

    expect(wrapper.find('[data-testid="email-log-retry-1"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="email-log-retry-2"]').exists()).toBe(true);
  });

  it('shows the digest button disabled, carrying its reason', () => {
    const wrapper = mountTable([DIGEST_FAILED]);
    const button = wrapper.get('[data-testid="email-log-retry-3"]');

    // Disabled and explained, rather than absent: a missing button reads as
    // "this failure cannot be acted on" without saying why.
    expect(button.attributes('disabled')).toBeDefined();
    expect(button.attributes('title')).toContain('resume varios registros');
  });

  it('blocks a second click while a retry is in flight', () => {
    const wrapper = mountTable([FAILED], { retryingId: 2 });

    expect(
      wrapper.get('[data-testid="email-log-retry-2"]').attributes('disabled'),
    ).toBeDefined();
  });

  it('names the records the email was about when the row is expanded', async () => {
    const wrapper = mountTable([SENT]);

    await wrapper.get('[data-testid="email-log-row-1"]').trigger('click');

    const detail = wrapper.get('[data-testid="email-log-detail-1"]');
    expect(detail.text()).toContain('Hosting: Kore');
  });

  it('still shows the failure reason it always showed', async () => {
    const wrapper = mountTable([FAILED]);

    await wrapper.get('[data-testid="email-log-row-2"]').trigger('click');

    expect(wrapper.get('[data-testid="email-log-detail-2"]').text())
      .toContain('SMTP timeout');
  });

  it('points a retry back at what it retried', async () => {
    const wrapper = mountTable([{ ...SENT, id: 9, retry_of: 2, targets: [] }]);

    await wrapper.get('[data-testid="email-log-row-9"]').trigger('click');

    expect(wrapper.get('[data-testid="email-log-detail-9"]').text())
      .toContain('Reintento del envío #2');
  });

  it('does not expand a row that has nothing more to say', async () => {
    const wrapper = mountTable([{ ...SENT, targets: [], error_message: '' }]);

    await wrapper.get('[data-testid="email-log-row-1"]').trigger('click');

    expect(wrapper.find('[data-testid="email-log-detail-1"]').exists()).toBe(false);
  });
});

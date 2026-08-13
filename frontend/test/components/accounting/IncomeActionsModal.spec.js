import { mount } from '@vue/test-utils';
import IncomeActionsModal from '~/components/accounting/IncomeActionsModal.vue';

const EXPECTED = {
  id: 42,
  concept: 'Hosting: Trimestral',
  kind: 'expected',
  kind_label: 'Esperado',
  client_name: 'Daniel Felipe Corredor Castiblanco',
  project_name: 'MIMITTOS',
  total_amount: '233280.00',
  payment_status: 'pending',
  reminders_muted: false,
  has_collection_account: false,
};

function mountModal(record) {
  return mount(IncomeActionsModal, {
    props: { open: true, record },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['close'],
          template: '<div><slot /></div>',
        },
        BaseButton: {
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
}

function actionIds(wrapper) {
  return wrapper.findAll('[data-testid^="income-action-"]')
    .map((node) => node.attributes('data-testid').replace(`-${EXPECTED.id}`, ''))
    .map((id) => id.replace('income-action-', ''));
}

describe('IncomeActionsModal', () => {
  it('names the income being acted on, with its client and project', () => {
    const wrapper = mountModal(EXPECTED);

    const header = wrapper.get('[data-testid="income-actions-modal"]').text();
    expect(header).toContain('Hosting: Trimestral');
    expect(header).toContain('Daniel Felipe Corredor Castiblanco');
    expect(header).toContain('MIMITTOS');
  });

  it('offers the full set for a pending expected income', () => {
    const wrapper = mountModal(EXPECTED);

    expect(actionIds(wrapper)).toEqual([
      'detail', 'edit', 'duplicate', 'liquidate', 'generate-collection',
      'toggle-mute', 'write-off', 'delete',
    ]);
  });

  it('offers silenciar avisos, which the classic table had silently lost', () => {
    const wrapper = mountModal(EXPECTED);

    expect(wrapper.get('[data-testid="income-action-toggle-mute-42"]').text())
      .toBe('Silenciar avisos');
  });

  it('flips the mute entry once the reminders are already silenced', () => {
    const wrapper = mountModal({ ...EXPECTED, reminders_muted: true });

    expect(wrapper.get('[data-testid="income-action-toggle-mute-42"]').text())
      .toBe('Reactivar avisos');
  });

  it('swaps generar for ver when the income already has a cuenta', () => {
    const wrapper = mountModal({
      ...EXPECTED,
      has_collection_account: true,
      collection_account_number: 'PA-MIMITTOS-001',
    });

    expect(actionIds(wrapper)).toContain('view-collection');
    expect(actionIds(wrapper)).not.toContain('generate-collection');
    expect(wrapper.get('[data-testid="income-action-view-collection-42"]').text())
      .toContain('PA-MIMITTOS-001');
  });

  it('drops liquidar, avisos and perdido for a liquid income', () => {
    const wrapper = mountModal({
      ...EXPECTED, kind: 'liquid', payment_status: null,
    });

    expect(actionIds(wrapper)).toEqual([
      'detail', 'edit', 'duplicate', 'generate-collection', 'delete',
    ]);
  });

  it('offers no cuenta de cobro on a written-off income', () => {
    const wrapper = mountModal({ ...EXPECTED, kind: 'lost' });

    expect(actionIds(wrapper)).toEqual(['detail', 'edit', 'duplicate', 'delete']);
  });

  it('offers duplicar whatever the state, since the usual case is a collected one', async () => {
    const liquid = { ...EXPECTED, kind: 'liquid', payment_status: null };
    const wrapper = mountModal(liquid);

    await wrapper.get('[data-testid="income-action-duplicate-42"]').trigger('click');

    expect(wrapper.emitted('duplicate')[0]).toEqual([liquid]);
    expect(wrapper.emitted('close')).toHaveLength(1);
  });

  it('hides marcar perdido once the income is partially collected', () => {
    const wrapper = mountModal({ ...EXPECTED, payment_status: 'partial' });

    // Asserted as the full set rather than a bare absence: a menu that
    // failed to render would satisfy "does not contain write-off" too.
    expect(actionIds(wrapper)).toEqual([
      'detail', 'edit', 'duplicate', 'liquidate', 'generate-collection',
      'toggle-mute', 'delete',
    ]);
  });

  it('emits the action and closes, so the row never stays half-acted-on', async () => {
    const wrapper = mountModal(EXPECTED);

    await wrapper.get('[data-testid="income-action-liquidate-42"]').trigger('click');

    expect(wrapper.emitted('liquidate')[0]).toEqual([EXPECTED]);
    expect(wrapper.emitted('close')).toHaveLength(1);
  });
});

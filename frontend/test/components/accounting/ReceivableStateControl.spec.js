import { mount } from '@vue/test-utils';
import ReceivableStateControl from '~/components/accounting/ReceivableStateControl.vue';

const expectedRow = (overrides = {}) => ({
  id: 7,
  concept: 'Kore - Entrega',
  kind: 'expected',
  ledger: 'company',
  payment_status: 'pending',
  is_receivable_candidate: false,
  collection_confidence: '',
  ...overrides,
});

describe('ReceivableStateControl', () => {
  it('emits candidate selection from the switch', async () => {
    const wrapper = mount(ReceivableStateControl, { props: { row: expectedRow() } });

    await wrapper.get('[role="switch"]').trigger('click');

    expect(wrapper.emitted('change')).toEqual([[{ is_receivable_candidate: true }]]);
  });

  it('emits confidence selection from the semaforo', async () => {
    const wrapper = mount(ReceivableStateControl, { props: { row: expectedRow() } });

    await wrapper.get('select').setValue('high');

    expect(wrapper.emitted('change')).toEqual([[{ collection_confidence: 'high' }]]);
  });

  it('shows a neutral circle beside an unclassified forecast', () => {
    const wrapper = mount(ReceivableStateControl, { props: { row: expectedRow() } });

    expect(wrapper.get('[data-testid="receivable-confidence-dot"]').classes())
      .toContain('bg-text-subtle');
    expect(wrapper.get('select').element.value).toBe('');
  });

  it('keeps the full confidence label beside its circle', () => {
    const wrapper = mount(ReceivableStateControl, {
      props: { row: expectedRow({ collection_confidence: 'medium' }) },
    });

    expect(wrapper.get('[data-testid="receivable-confidence-dot"]').classes())
      .toContain('bg-warning-strong');
    expect(wrapper.get('select').text()).toContain('Cobro incierto (50/50)');
  });

  it('disables controls during persistence', () => {
    const wrapper = mount(ReceivableStateControl, {
      props: { row: expectedRow(), busy: true },
    });

    expect(wrapper.get('[role="switch"]').attributes('disabled')).toBe('');
    expect(wrapper.get('select').attributes('disabled')).toBe('');
  });

  it('hides controls for liquid income', () => {
    const wrapper = mount(ReceivableStateControl, {
      props: { row: expectedRow({ kind: 'liquid' }) },
    });

    expect(wrapper.find('[role="switch"]').exists()).toBe(false);
    expect(wrapper.text()).toBe('—');
  });
});

/**
 * Tests for AccountingErrorState.
 *
 * Covers: default title, custom detail, retry emit, retrying state,
 * and the danger alert variant.
 */
import { mount } from '@vue/test-utils';
import AccountingErrorState from '../../../components/accounting/AccountingErrorState.vue';

describe('AccountingErrorState', () => {
  it('renders the default title and a custom detail', () => {
    const wrapper = mount(AccountingErrorState, {
      props: { detail: 'El servidor no respondió.' },
    });

    expect(wrapper.text()).toContain('No se pudieron cargar los datos');
    expect(wrapper.text()).toContain('El servidor no respondió.');
  });

  it('emits retry when the button is clicked', async () => {
    const wrapper = mount(AccountingErrorState);

    await wrapper.find('[data-testid="accounting-error-retry"]').trigger('click');

    expect(wrapper.emitted('retry')).toHaveLength(1);
  });

  it('disables the button and changes the label while retrying', () => {
    const wrapper = mount(AccountingErrorState, { props: { retrying: true } });
    const button = wrapper.find('[data-testid="accounting-error-retry"]');

    expect(button.attributes('disabled')).toBeDefined();
    expect(button.text()).toContain('Reintentando...');
  });

  it('uses the danger alert variant', () => {
    const wrapper = mount(AccountingErrorState);

    expect(wrapper.find('[role="alert"]').classes().join(' ')).toContain('bg-danger-soft');
  });
});

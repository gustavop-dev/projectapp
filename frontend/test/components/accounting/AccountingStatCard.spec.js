import { mount } from '@vue/test-utils';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';

function mountCard(props = {}) {
  return mount(AccountingStatCard, {
    props: { label: 'Ingresos del mes', value: '$1.500.000 COP', ...props },
  });
}

describe('AccountingStatCard', () => {
  it('renders label and value', () => {
    const wrapper = mountCard();

    expect(wrapper.text()).toContain('Ingresos del mes');
    expect(wrapper.text()).toContain('$1.500.000 COP');
  });

  it('renders the sub line only when provided', () => {
    const withSub = mountCard({ sub: '12 registros' });
    expect(withSub.text()).toContain('12 registros');

    const withoutSub = mountCard();
    expect(withoutSub.findAll('p')).toHaveLength(2);
  });

  it('uses the default tone class when no tone is given', () => {
    const wrapper = mountCard();

    expect(wrapper.find('[data-testid="accounting-stat-value"]').classes()).toContain(
      'text-text-default',
    );
  });

  it.each([
    ['success', 'text-success-strong'],
    ['warning', 'text-warning-strong'],
    ['danger', 'text-danger-strong'],
    ['brand', 'text-text-brand'],
  ])('applies the %s tone class to the value', (tone, expectedClass) => {
    const wrapper = mountCard({ tone });

    expect(wrapper.find('[data-testid="accounting-stat-value"]').classes()).toContain(
      expectedClass,
    );
  });
});

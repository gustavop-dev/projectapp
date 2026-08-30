import { mount } from '@vue/test-utils';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';

function mountCard(props = {}) {
  return mount(AccountingStatCard, {
    props: { label: 'Ingresos del mes', value: '$1.500.000 COP', ...props },
  });
}

describe('AccountingStatCard', () => {
  it('renders label and value', () => {
    // Falla si el wrapper deja de entregar la pregunta o el monto al indicador base.
    const wrapper = mountCard();

    expect(wrapper.get('[data-testid="indicator-label"]').text()).toBe('Ingresos del mes');
    expect(wrapper.get('[data-testid="accounting-stat-value"]').text()).toBe('$1.500.000 COP');
  });

  it('forwards sub copy to the visible support row', () => {
    // Falla si el contexto de registros deja de aparecer debajo del monto.
    const wrapper = mountCard({ sub: '12 registros' });

    expect(wrapper.get('[data-testid="indicator-support"]').text()).toBe('12 registros');
  });

  it('keeps the reserved sub line when no copy is provided', () => {
    // Falla si la tarjeta sin apoyo pierde la fila que iguala su altura.
    const wrapper = mountCard();

    expect(wrapper.get('[data-testid="indicator-support"]').element.textContent).toBe('\u00a0');
    expect(wrapper.get('[data-testid="indicator-support"]').attributes('aria-hidden'))
      .toBe('true');
  });

  it('forwards the compact horizontal layout without an empty sub line', () => {
    // Falla si el wrapper contable pierde el layout solicitado por Proyectos.
    const wrapper = mountCard({ layout: 'compact-horizontal' });

    expect(wrapper.get('article').attributes('data-layout')).toBe('compact-horizontal');
    expect(wrapper.find('[data-testid="indicator-support"]').exists()).toBe(false);
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

  it('stays informational when not clickable', () => {
    // Falla si una tarjeta informativa adquiere una acción engañosa por defecto.
    const wrapper = mountCard();

    expect(wrapper.find('[aria-label="Ver estadísticas de Ingresos del mes"]').exists()).toBe(false);
    expect(wrapper.get('article').attributes('aria-label')).toBeUndefined();
  });

  it('renders an accessible button that emits click when clickable', async () => {
    // Falla si los consumidores existentes con clickable dejan de abrir sus estadísticas.
    const wrapper = mountCard({ clickable: true });
    const button = wrapper.get('[aria-label="Ver estadísticas de Ingresos del mes"]');

    expect(button.element.tagName).toBe('BUTTON');
    expect(button.attributes('type')).toBe('button');

    await button.trigger('click');

    expect(wrapper.emitted('click')).toEqual([[]]);
  });

  it('uses the explicit action label instead of the compatibility fallback', async () => {
    // Falla si una acción declarada muestra una intención distinta a la configurada por la pantalla.
    const wrapper = mountCard({
      clickable: true,
      action: 'filter',
      actionLabel: 'Filtrar ingresos del mes',
    });
    const button = wrapper.get('[aria-label="Filtrar ingresos del mes"]');

    expect(button.element.tagName).toBe('BUTTON');

    await button.trigger('click');

    expect(wrapper.emitted('click')).toEqual([[]]);
  });
});

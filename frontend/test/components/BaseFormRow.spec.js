import { mount } from '@vue/test-utils';

import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseFormRow from '~/components/base/BaseFormRow.vue';

/**
 * These assert the layout contract through the classes the components emit,
 * because jsdom does not lay anything out — `getComputedStyle` would happily
 * report two misaligned inputs as identical. The geometry itself (both inputs
 * sharing a `y`, with one label wrapped and the other not) is covered by the
 * Playwright specs; what is checked here is that the row hands out the bands
 * and every field claims them, which is the part that silently regresses when
 * someone reverts a row to a hand-written `<div class="grid grid-cols-2">`.
 */
const LONG = 'Código de facturación (opcional)';
const SHORT = 'NIT (opcional)';

const Harness = {
  components: { BaseFormField, BaseFormRow },
  props: {
    rowProps: { type: Object, default: () => ({}) },
    fields: { type: Array, default: () => [{ label: SHORT }, { label: LONG }] },
  },
  template: `
    <BaseFormRow v-bind="rowProps">
      <BaseFormField v-for="(field, i) in fields" :key="i" v-bind="field">
        <input :data-testid="'field-' + i" />
      </BaseFormField>
    </BaseFormRow>
  `,
};

function mountRow(rowProps = {}, fields) {
  return mount(Harness, { props: { rowProps, ...(fields ? { fields } : {}) } });
}

const bands = (wrapper) => wrapper.findComponent(BaseFormRow).classes();
const fieldsOf = (wrapper) => wrapper.findAllComponents(BaseFormField);

describe('BaseFormRow', () => {
  it('puts every field on the same bands so the controls start at one height', () => {
    const wrapper = mountRow();

    // The row owns the bands...
    expect(bands(wrapper)).toEqual(
      expect.arrayContaining(['sm:grid-cols-2', 'sm:grid-rows-[auto_auto_auto]']),
    );

    // ...and each field inherits them rather than stacking on its own, which is
    // what stops the longer label from pushing only its own input down.
    const rendered = fieldsOf(wrapper);
    expect(rendered).toHaveLength(2);
    rendered.forEach((field) => {
      expect(field.classes()).toEqual(
        expect.arrayContaining(['sm:grid', 'sm:grid-rows-subgrid', 'sm:row-span-3']),
      );
    });
  });

  it('zeroes the gap inside a field, not on the row', () => {
    const wrapper = mountRow({ gap: 4 });

    // A subgrid inherits the row's gutters. Left inherited, the label would sit
    // a whole row-gap away from its own control instead of the 4px margin.
    fieldsOf(wrapper).forEach((field) => {
      expect(field.classes()).toContain('sm:gap-y-0');
    });

    // The row keeps its own gap, which is what still separates one wrapped line
    // of fields from the next.
    expect(bands(wrapper)).toContain('gap-4');
    expect(bands(wrapper).join(' ')).not.toContain('gap-y-0');
  });

  it('lines up each wrapped line of fields on its own', () => {
    const wrapper = mountRow({ cols: 2 }, [
      { label: SHORT }, { label: LONG }, { label: 'Tercero' }, { label: 'Cuarto' },
    ]);

    // Four fields in two columns wrap onto two lines; every one of them claims
    // the bands, so each line aligns independently.
    const rendered = fieldsOf(wrapper);
    expect(rendered).toHaveLength(4);
    rendered.forEach((field) => {
      expect(field.classes()).toContain('sm:row-span-3');
    });
  });

  it('gives each field a label, a control and a hint band', () => {
    const wrapper = mountRow();

    fieldsOf(wrapper).forEach((field) => {
      expect(field.element.children).toHaveLength(3);
    });
  });

  it('reserves the label band even when a field has no label', () => {
    const wrapper = mountRow({}, [{ label: SHORT }, {}]);

    // Without the empty cell the unlabelled field would pull its control up
    // into the label band and sit above its neighbour.
    const [, unlabelled] = fieldsOf(wrapper);
    expect(unlabelled.element.children).toHaveLength(3);
    expect(unlabelled.element.children[0].textContent.trim()).toBe('');
    expect(unlabelled.find('input').exists()).toBe(true);
  });

  it('keeps both fields on the same bands when only one carries a hint', () => {
    const wrapper = mountRow({}, [
      { label: SHORT, hint: 'Para cuentas de cobro' },
      { label: LONG },
    ]);

    // The hint band is as tall as the tallest cell, so the row below stays square.
    fieldsOf(wrapper).forEach((field) => {
      expect(field.classes()).toContain('sm:row-span-3');
    });
    expect(wrapper.text()).toContain('Para cuentas de cobro');
  });

  it('stacks in one column below the breakpoint without reserving bands', () => {
    const wrapper = mountRow();

    const row = bands(wrapper);
    expect(row).toContain('grid-cols-1');
    expect(row).toContain('gap-3');
    // Every band class is breakpoint-scoped, so nothing is reserved on mobile.
    row
      .filter((cls) => cls.includes('grid-rows') || cls.includes('gap-y'))
      .forEach((cls) => expect(cls.startsWith('sm:')).toBe(true));
  });

  it('keeps the fields in document order when they stack', () => {
    const wrapper = mountRow();

    const order = wrapper.findAll('input').map((input) => input.attributes('data-testid'));
    expect(order).toEqual(['field-0', 'field-1']);
  });

  it('does not align a single-column row, where there is nothing to line up', () => {
    const wrapper = mountRow({ cols: 1, gap: 4 });

    expect(bands(wrapper)).toContain('gap-4');
    expect(bands(wrapper).join(' ')).not.toContain('grid-rows');
    fieldsOf(wrapper).forEach((field) => {
      expect(field.classes().join(' ')).not.toContain('row-span');
    });
  });

  it('honours the breakpoint a row was already using', () => {
    const wrapper = mountRow({ at: 'md' });

    expect(bands(wrapper)).toEqual(
      expect.arrayContaining(['md:grid-cols-2', 'md:grid-rows-[auto_auto_auto]']),
    );
    fieldsOf(wrapper).forEach((field) => {
      expect(field.classes()).toContain('md:row-span-3');
    });
  });

  it('can widen again on large screens without losing the bands', () => {
    const wrapper = mountRow({ cols: 2, lg: 5 });

    expect(bands(wrapper)).toEqual(
      expect.arrayContaining(['sm:grid-cols-2', 'lg:grid-cols-5', 'sm:grid-rows-[auto_auto_auto]']),
    );
  });

  it('can be the form element itself', () => {
    const wrapper = mountRow({ as: 'form' });

    expect(wrapper.findComponent(BaseFormRow).element.tagName).toBe('FORM');
    expect(bands(wrapper)).toContain('sm:grid-cols-2');
  });

  it('lets a field opt out when it is not a direct child of the row', () => {
    const wrapper = mountRow({}, [{ label: SHORT }, { label: LONG, standalone: true }]);

    const [joined, opted] = fieldsOf(wrapper);
    expect(joined.classes()).toContain('sm:row-span-3');
    expect(opted.classes().join(' ')).not.toContain('row-span');
  });
});

describe('BaseFormField outside a row', () => {
  it('renders as it did before the bands existed', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: SHORT, hint: 'Para cuentas de cobro' },
      slots: { default: '<input data-testid="solo" />' },
    });

    // No grid on the root, and the three wrappers stay out of the box tree, so
    // the 29 files that use the field outside a row are untouched by this change.
    expect(wrapper.classes().join(' ')).not.toContain('grid');
    Array.from(wrapper.element.children).forEach((cell) => {
      expect(cell.className).toBe('contents');
    });
    expect(wrapper.find('label').text()).toContain(SHORT);
    expect(wrapper.find('[data-testid="solo"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Para cuentas de cobro');
  });
});

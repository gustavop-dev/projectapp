/**
 * Tests for StatementAliasTable inline editing of learned merchants.
 *
 * Covers: the empty state, the three click-to-edit columns (descriptor,
 * merchant, category), picking a merchant from the catalog, deleting, and an
 * in-flight save locking its own cell.
 */
import { mount } from '@vue/test-utils';
import StatementAliasTable from '../../../components/accounting/StatementAliasTable.vue';

const CATEGORY_OPTIONS = [
  { value: 'software', label: 'Software y suscripciones' },
  { value: 'fuel', label: 'Gasolina' },
];

function makeAlias(overrides = {}) {
  return {
    id: 7,
    match_text: 'PAYU NETFLIX',
    merchant_name: 'Netflix',
    default_category: 'software',
    default_category_label: 'Software y suscripciones',
    ...overrides,
  };
}

function mountTable(props = {}) {
  return mount(StatementAliasTable, {
    props: {
      aliases: [makeAlias()],
      categoryOptions: CATEGORY_OPTIONS,
      ...props,
    },
  });
}

function cell(wrapper, field, aliasId = 7) {
  return wrapper.find(`[data-testid="alias-cell-${field}-${aliasId}"]`);
}

describe('StatementAliasTable', () => {
  it('shows the empty state instead of the table when there are no aliases', () => {
    const wrapper = mountTable({ aliases: [] });

    expect(wrapper.text()).toContain('Aún no hay alias aprendidos');
    expect(wrapper.find('table').exists()).toBe(false);
  });

  it('renders the descriptor, the merchant and the category label', () => {
    const wrapper = mountTable();

    expect(cell(wrapper, 'match_text').text()).toContain('PAYU NETFLIX');
    expect(cell(wrapper, 'merchant_name').text()).toContain('Netflix');
    expect(cell(wrapper, 'default_category').text()).toContain('Software y suscripciones');
  });

  it('a click on the descriptor edits it and emits inline-save', async () => {
    const wrapper = mountTable();
    const td = cell(wrapper, 'match_text');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    const input = td.find('input');
    await input.setValue('netflix com');
    await input.trigger('keydown.enter');

    const emitted = wrapper.emitted('inline-save');
    expect(emitted).toHaveLength(1);
    const [alias, field, value] = emitted[0];
    expect(alias.id).toBe(7);
    expect(field).toBe('match_text');
    expect(value).toBe('netflix com');
  });

  it('category cell shows the label but emits the option value', async () => {
    const wrapper = mountTable();
    const td = cell(wrapper, 'default_category');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    await td.find('select').setValue('fuel');

    const [, field, value] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('default_category');
    expect(value).toBe('fuel');
  });

  it('renames the merchant from the catalog combobox', async () => {
    const wrapper = mountTable({
      merchantOptions: [
        { value: 'Terpel', category: 'fuel', categoryLabel: 'Gasolina' },
      ],
    });
    const td = cell(wrapper, 'merchant_name');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    // The cell opens holding the current name, so the catalog only suggests
    // again once the owner starts typing the new one.
    await td.find('input').setValue('Terp');
    await td.find('[data-testid="merchant-input-option-0"]').trigger('mousedown');

    const [, field, value] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('merchant_name');
    expect(value).toBe('Terpel');
  });

  it('emits delete with the alias of the clicked row', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="statement-alias-7"] button').trigger('click');

    expect(wrapper.emitted('delete')[0][0].id).toBe(7);
  });

  it('does not open the editor on the cell whose save is in flight', async () => {
    const wrapper = mountTable({ inlineSavingKey: '7:merchant_name' });
    const td = cell(wrapper, 'merchant_name');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');

    expect(td.find('input').exists()).toBe(false);
  });
});

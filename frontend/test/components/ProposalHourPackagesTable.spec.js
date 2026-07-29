/**
 * ProposalHourPackagesTable — the hour-package table of the «Tarifa por hora» tab.
 *
 * Read-only in automatic mode; in manual every cell is click-to-edit and rows
 * can be added and removed. An edit emits to the parent — it never saves by
 * itself, unlike the accounting tables this borrows the cell from.
 */
import { mount } from '@vue/test-utils';

import ProposalHourPackagesTable from '../../components/panel/proposal/ProposalHourPackagesTable.vue';

const PACKAGES = [
  { id: 7, name: 'Pro', note: 'nota pro', hours: 60, discountPercent: 10, hourlyRate: 30000 },
  { id: 8, name: 'Ágil', note: '', hours: 20, discountPercent: 0, hourlyRate: 45000 },
];

function mountTable(props = {}) {
  return mount(ProposalHourPackagesTable, {
    props: {
      packages: PACKAGES, editable: true, currency: 'COP', baseRate: 30000, ...props,
    },
  });
}

const cell = (wrapper, field, idx) => wrapper.find(`[data-testid="hour-package-cell-${field}-${idx}"]`);

async function editCell(wrapper, field, idx, value) {
  const target = cell(wrapper, field, idx);
  await target.find('[data-testid="inline-cell-display"]').trigger('click');
  const input = target.find('input');
  await input.setValue(value);
  await input.trigger('keydown.enter');
}

describe('ProposalHourPackagesTable', () => {
  it('shows the rate the admin sets and the discounted one the client gets', () => {
    const wrapper = mountTable();

    // Pro: 30.000 with 10% off → 27.000/h to the client, 60h → 1.620.000
    expect(cell(wrapper, 'rate', 0).text()).toContain('30.000');
    expect(wrapper.find('[data-testid="hour-rate-rate-7"]').text()).toContain('27.000');
    expect(wrapper.find('[data-testid="hour-rate-total-7"]').text()).toContain('1.620.000');
  });

  it('emits an update for each edited field instead of saving by itself', async () => {
    const wrapper = mountTable();

    await editCell(wrapper, 'name', 0, 'Renombrado');
    await editCell(wrapper, 'hours', 0, '80');
    await editCell(wrapper, 'discount', 0, '25');
    await editCell(wrapper, 'rate', 0, '50.000');

    expect(wrapper.emitted('update')).toEqual([
      [0, 'name', 'Renombrado'],
      [0, 'hours', 80],
      [0, 'discountPercent', 25],
      [0, 'hourlyRate', 50000],
    ]);
  });

  it('clamps the discount to a percentage', async () => {
    const wrapper = mountTable();

    await editCell(wrapper, 'discount', 1, '250');

    expect(wrapper.emitted('update')[0]).toEqual([1, 'discountPercent', 100]);
  });

  it('emits remove and add for the row actions', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="hour-package-delete-1"]').trigger('click');
    await wrapper.find('[data-testid="hour-packages-add"]').trigger('click');

    expect(wrapper.emitted('remove')).toEqual([[1]]);
    expect(wrapper.emitted('add')).toHaveLength(1);
  });

  it('refuses to remove the last remaining package', () => {
    const wrapper = mountTable({ packages: [PACKAGES[0]] });

    expect(wrapper.find('[data-testid="hour-package-delete-0"]').element.disabled).toBe(true);
  });

  it('is read-only in automatic mode', () => {
    const wrapper = mountTable({ editable: false });

    expect(wrapper.find('[data-testid="inline-cell-display"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="hour-packages-add"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="hour-package-delete-0"]').exists()).toBe(false);
    // The numbers are still there, just not editable.
    expect(wrapper.find('[data-testid="hour-rate-rate-7"]').text()).toContain('27.000');
  });

  it('prices a package with no rate of its own from the base rate', () => {
    const wrapper = mountTable({
      packages: [{ id: 9, name: 'Sin tarifa', hours: 10, discountPercent: 0 }],
      baseRate: 20000,
    });

    expect(wrapper.find('[data-testid="hour-rate-rate-9"]').text()).toContain('20.000');
    expect(wrapper.find('[data-testid="hour-rate-total-9"]').text()).toContain('200.000');
  });
});

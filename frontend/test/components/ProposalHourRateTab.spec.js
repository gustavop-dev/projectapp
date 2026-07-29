/**
 * ProposalHourRateTab — per-proposal hour packages (auto / manual).
 *
 * Auto mirrors the live catalog. Manual makes the proposal the owner of its own
 * package list: rows can be edited, added and removed, and the catalog stops
 * feeding it until «Restablecer» is used. A separate toggle decides whether the
 * block is printed at all.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';

import ProposalHourRateTab from '../../components/panel/proposal/ProposalHourRateTab.vue';
import { useProposalStore } from '../../stores/proposals';
import { useHourPackagesStore } from '../../stores/hour_packages';

const CATALOG = [
  {
    id: 7, name_es: 'Pro', name_en: 'Pro', note_es: '', note_en: '',
    hours: 60, hourly_rate: '30000', discount_percent: 10,
    is_active: true, order: 1, currency: 'COP',
  },
  {
    id: 8, name_es: 'Ágil', name_en: 'Agile', note_es: 'nota', note_en: 'note',
    hours: 20, hourly_rate: '45000', discount_percent: 0,
    is_active: true, order: 2, currency: 'COP',
  },
  {
    id: 9, name_es: 'Inactivo', name_en: 'Inactive', hours: 5,
    hourly_rate: '99000', discount_percent: 0,
    is_active: false, order: 3, currency: 'COP',
  },
];

const PROPOSAL = { id: 3, nationality: 'COL', language: 'es', currency: 'COP' };
const MANUAL = { hourPackagesMode: 'manual', manualCurrency: 'COP' };

function buildSection(content = {}) {
  return {
    id: 42,
    section_type: 'commercial_conditions',
    title: 'Condiciones comerciales',
    is_enabled: true,
    is_wide_panel: false,
    content_json: {
      title: 'Condiciones comerciales',
      scopeTitle: 'Alcance',
      currency: 'COP',
      hourlyRate: 30000,
      packages: [
        { id: 7, name: 'Pro', note: '', hours: 60, discountPercent: 10, hourlyRate: 30000 },
        { id: 8, name: 'Ágil', note: 'nota', hours: 20, discountPercent: 0, hourlyRate: 45000 },
      ],
      ...content,
    },
  };
}

async function mountTab({ content = {}, catalog = CATALOG, section = undefined } = {}) {
  setActivePinia(createPinia());
  const proposalStore = useProposalStore();
  const hourPackagesStore = useHourPackagesStore();

  const resolved = section === null ? null : (section || buildSection(content));
  proposalStore.currentProposal = { ...PROPOSAL, sections: resolved ? [resolved] : [] };
  proposalStore.updateSection = jest.fn().mockResolvedValue({ success: true });
  proposalStore.createSection = jest.fn().mockResolvedValue({ success: true });
  hourPackagesStore.fetchAdminPackages = jest.fn().mockImplementation(async () => {
    hourPackagesStore.packages = catalog;
    return { success: true };
  });

  const wrapper = mount(ProposalHourRateTab, { props: { proposal: PROPOSAL } });
  await flushPromises();
  return { wrapper, proposalStore };
}

const rowRate = (wrapper, key) => wrapper.find(`[data-testid="hour-rate-rate-${key}"]`).text();
const savedJson = (store) => store.updateSection.mock.calls[0][1].content_json;

async function editCell(wrapper, field, idx, value) {
  const target = wrapper.find(`[data-testid="hour-package-cell-${field}-${idx}"]`);
  await target.find('[data-testid="inline-cell-display"]').trigger('click');
  const input = target.find('input');
  await input.setValue(value);
  await input.trigger('keydown.enter');
  await flushPromises();
}

describe('ProposalHourRateTab', () => {
  it('auto mode prices every row from the live catalog, ordered and active-only', async () => {
    const { wrapper } = await mountTab();

    const rows = wrapper.findAll('[data-testid^="hour-package-row-"]');
    expect(rows).toHaveLength(2);
    expect(rows[0].text()).toContain('Pro');   // order 1 before order 2
    expect(rows[1].text()).toContain('Ágil');
    expect(rowRate(wrapper, 7)).toContain('27.000');  // 30.000 −10%
    // Read-only: no editing affordance in auto.
    expect(wrapper.find('[data-testid="inline-cell-display"]').exists()).toBe(false);
  });

  it('the mode switch flips between automatic and manual', async () => {
    const { wrapper } = await mountTab();
    expect(wrapper.find('[data-testid="hour-rate-manual-input"]').exists()).toBe(false);

    await wrapper.find('[data-testid="hour-rate-mode-manual"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="hour-rate-manual-input"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="hour-rate-mode-hint"]').text()).toContain('sus propios paquetes');
  });

  it('manual edits the proposal package list and saves it verbatim', async () => {
    const { wrapper, proposalStore } = await mountTab({ content: MANUAL });

    await editCell(wrapper, 'name', 0, 'Pro a medida');
    await editCell(wrapper, 'hours', 0, '80');
    await wrapper.find('[data-testid="hour-rate-save"]').trigger('click');
    await flushPromises();

    const json = savedJson(proposalStore);
    expect(json.hourPackagesMode).toBe('manual');
    expect(json.packages[0]).toMatchObject({ name: 'Pro a medida', hours: 80 });
    // Fields this tab does not own survive untouched.
    expect(json.scopeTitle).toBe('Alcance');
  });

  it('typing the base rate alone leaves the table untouched', async () => {
    // Regression: the field used to look live and move nothing, because every
    // package already carried its own rate and the base was only a fallback.
    const { wrapper } = await mountTab({ content: MANUAL });

    await wrapper.find('[data-testid="hour-rate-manual-input"]').setValue('90.000');
    await flushPromises();

    expect(rowRate(wrapper, 7)).toContain('27.000');
    expect(rowRate(wrapper, 8)).toContain('45.000');
  });

  it('applying the base rate rewrites every package and reprices the rows', async () => {
    const { wrapper, proposalStore } = await mountTab({ content: MANUAL });

    await wrapper.find('[data-testid="hour-rate-manual-input"]').setValue('90.000');
    await wrapper.find('[data-testid="hour-rate-apply-base-all"]').trigger('click');
    await flushPromises();

    // Each row keeps its own discount on top of the shared rate.
    expect(rowRate(wrapper, 7)).toContain('81.000');   // 90.000 −10%
    expect(rowRate(wrapper, 8)).toContain('90.000');   // sin descuento

    await wrapper.find('[data-testid="hour-rate-save"]').trigger('click');
    await flushPromises();
    expect(savedJson(proposalStore).packages.map((p) => p.hourlyRate)).toEqual([90000, 90000]);
  });

  it('the apply button is off with no base rate and once every row already charges it', async () => {
    const { wrapper } = await mountTab({ content: MANUAL });
    const apply = () => wrapper.find('[data-testid="hour-rate-apply-base-all"]');

    await wrapper.find('[data-testid="hour-rate-manual-input"]').setValue('');
    await flushPromises();
    expect(apply().element.disabled).toBe(true);

    await wrapper.find('[data-testid="hour-rate-manual-input"]').setValue('90.000');
    await flushPromises();
    expect(apply().element.disabled).toBe(false);

    await apply().trigger('click');
    await flushPromises();
    expect(apply().element.disabled).toBe(true);
  });

  it('adds and removes packages, never dropping the last one', async () => {
    const { wrapper } = await mountTab({ content: MANUAL });
    expect(wrapper.findAll('[data-testid^="hour-package-row-"]')).toHaveLength(2);

    await wrapper.find('[data-testid="hour-packages-add"]').trigger('click');
    await flushPromises();
    expect(wrapper.findAll('[data-testid^="hour-package-row-"]')).toHaveLength(3);

    await wrapper.find('[data-testid="hour-package-delete-2"]').trigger('click');
    await wrapper.find('[data-testid="hour-package-delete-1"]').trigger('click');
    await flushPromises();

    const rows = wrapper.findAll('[data-testid^="hour-package-row-"]');
    expect(rows).toHaveLength(1);
    expect(wrapper.find('[data-testid="hour-package-delete-0"]').element.disabled).toBe(true);
  });

  it('keeps the manual list when switching to automatic and back', async () => {
    const { wrapper } = await mountTab({ content: MANUAL });
    await editCell(wrapper, 'name', 0, 'Mío');

    await wrapper.find('[data-testid="hour-rate-mode-auto"]').trigger('click');
    await flushPromises();
    // Auto shows the catalog again.
    expect(wrapper.findAll('[data-testid^="hour-package-row-"]')[0].text()).toContain('Pro');

    await wrapper.find('[data-testid="hour-rate-mode-manual"]').trigger('click');
    await flushPromises();
    expect(wrapper.findAll('[data-testid^="hour-package-row-"]')[0].text()).toContain('Mío');
  });

  it('restoring pulls the whole list back from the catalog', async () => {
    const { wrapper } = await mountTab({ content: MANUAL });
    await editCell(wrapper, 'name', 0, 'Mío');
    await wrapper.find('[data-testid="hour-package-delete-1"]').trigger('click');
    await flushPromises();

    await wrapper.find('[data-testid="hour-rate-reset-catalog"]').trigger('click');
    await flushPromises();

    const rows = wrapper.findAll('[data-testid^="hour-package-row-"]');
    expect(rows).toHaveLength(2);
    expect(rows[0].text()).toContain('Pro');
    // Each package keeps its own catalog rate rather than being flattened.
    expect(rowRate(wrapper, 7)).toContain('27.000');
    expect(rowRate(wrapper, 8)).toContain('45.000');
    expect(wrapper.find('[data-testid="hour-rate-reset-catalog"]').element.disabled).toBe(true);
  });

  it('the print toggle travels in the payload without touching the packages', async () => {
    const { wrapper, proposalStore } = await mountTab();
    expect(wrapper.find('[data-testid="hour-rate-print-label"]').text()).toContain('se imprimen');

    await wrapper.find('[aria-label="Incluir los paquetes por horas en el PDF"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="hour-rate-print-label"]').text()).toContain('NO se imprimen');

    await wrapper.find('[data-testid="hour-rate-save"]').trigger('click');
    await flushPromises();
    expect(savedJson(proposalStore).hourPackagesEnabled).toBe(false);
  });

  it('opens a legacy manual proposal at the price it is being quoted', async () => {
    // The production shape before manual owned its packages: a base rate and
    // packages carrying no rate of their own.
    const { wrapper, proposalStore } = await mountTab({
      content: {
        ...MANUAL,
        manualHourlyRate: 33000,
        packages: [{ name: 'Ágil', note: '', hours: 20, discountPercent: 10 }],
      },
    });

    expect(rowRate(wrapper, 'row-0')).toContain('29.700');  // 33.000 −10%

    // Merely opening it is not a change, so nothing is saved and the stored
    // legacy shape keeps working. The consolidation lands on the next real edit.
    expect(wrapper.find('[data-testid="hour-rate-save"]').element.disabled).toBe(true);

    await editCell(wrapper, 'hours', 0, '30');
    await wrapper.find('[data-testid="hour-rate-save"]').trigger('click');
    await flushPromises();

    const json = savedJson(proposalStore);
    expect(json.packages[0]).toMatchObject({ hours: 30, hourlyRate: 33000 });
    expect('manualHourlyRate' in json).toBe(false);
    expect('manualPackageRates' in json).toBe(false);
  });

  it('falls back to auto and warns when the manual rate was set in another currency', async () => {
    const { wrapper } = await mountTab({
      content: { hourPackagesMode: 'manual', manualCurrency: 'USD' },
    });

    expect(wrapper.find('[data-testid="hour-rate-currency-mismatch"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="hour-rate-manual-input"]').exists()).toBe(false);
  });

  it('offers to create the section when the proposal has none', async () => {
    const { wrapper, proposalStore } = await mountTab({ section: null });

    expect(wrapper.find('[data-testid="hour-rate-no-section"]').exists()).toBe(true);
    await wrapper.find('[data-testid="hour-rate-create-section"]').trigger('click');
    expect(proposalStore.createSection).toHaveBeenCalledWith(3, 'commercial_conditions');
  });

  it('warns and previews from the stored snapshot when the catalog is empty', async () => {
    const { wrapper } = await mountTab({ catalog: [] });

    expect(wrapper.find('[data-testid="hour-rate-empty-catalog"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid^="hour-package-row-"]')).toHaveLength(2);
  });

  it('warns when the section is disabled and will not reach the PDF', async () => {
    const section = buildSection();
    section.is_enabled = false;
    const { wrapper } = await mountTab({ section });

    expect(wrapper.find('[data-testid="hour-rate-disabled-warning"]').exists()).toBe(true);
  });
});

/**
 * ProposalHourRateTab — per-proposal hourly rate (auto / manual).
 *
 * Auto mirrors the catalog; manual overrides only the rate while names, hours
 * and discounts keep coming from the catalog. The manual value must survive a
 * switch back to auto, and saving must never write catalog-owned keys.
 */
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';

import ProposalHourRateTab from '../../components/panel/proposal/ProposalHourRateTab.vue';
import { useProposalStore } from '../../stores/proposals';
import { useHourPackagesStore } from '../../stores/hour_packages';

const CATALOG = [
  {
    id: 8,
    name_es: 'Ágil',
    name_en: 'Agile',
    note_es: 'nota',
    note_en: 'note',
    hours: 20,
    hourly_rate: '30000',
    discount_percent: 0,
    is_active: true,
    order: 2,
    currency: 'COP',
  },
  {
    id: 7,
    name_es: 'Pro',
    name_en: 'Pro',
    note_es: '',
    note_en: '',
    hours: 60,
    hourly_rate: '30000',
    discount_percent: 10,
    is_active: true,
    order: 1,
    currency: 'COP',
  },
  {
    id: 9,
    name_es: 'Inactivo',
    name_en: 'Inactive',
    hours: 5,
    hourly_rate: '99000',
    discount_percent: 0,
    is_active: false,
    order: 3,
    currency: 'COP',
  },
];

const PROPOSAL = { id: 3, nationality: 'COL', language: 'es', currency: 'COP' };

function buildSection(content = {}) {
  return {
    id: 42,
    section_type: 'commercial_conditions',
    title: 'Condiciones comerciales',
    is_enabled: true,
    is_wide_panel: false,
    content_json: {
      title: 'Condiciones comerciales',
      currency: 'COP',
      hourlyRate: 30000,
      packages: [],
      ...content,
    },
  };
}

async function mountTab({ content = {}, catalog = CATALOG, section = undefined } = {}) {
  setActivePinia(createPinia());
  const proposalStore = useProposalStore();
  const hourPackagesStore = useHourPackagesStore();

  const resolvedSection = section === null ? null : (section || buildSection(content));
  proposalStore.currentProposal = {
    ...PROPOSAL,
    sections: resolvedSection ? [resolvedSection] : [],
  };
  proposalStore.updateSection = jest.fn().mockResolvedValue({ success: true });
  proposalStore.createSection = jest.fn().mockResolvedValue({ success: true });
  hourPackagesStore.fetchAdminPackages = jest.fn().mockImplementation(async () => {
    hourPackagesStore.packages = catalog;
    return { success: true };
  });

  const wrapper = mount(ProposalHourRateTab, { props: { proposal: PROPOSAL } });
  await flushPromises();
  return { wrapper, proposalStore, hourPackagesStore };
}

const rowRate = (wrapper, id) => wrapper.find(`[data-testid="hour-rate-rate-${id}"]`).text();
const rowTotal = (wrapper, id) => wrapper.find(`[data-testid="hour-rate-total-${id}"]`).text();

describe('ProposalHourRateTab', () => {
  it('auto mode prices every row from the live catalog, ordered and active-only', async () => {
    const { wrapper } = await mountTab();

    const rows = wrapper.findAll('[data-testid^="hour-rate-row-"]');
    expect(rows).toHaveLength(2);
    // order=1 (Pro) comes before order=2 (Ágil); the inactive one is excluded.
    expect(rows[0].text()).toContain('Pro');
    expect(rows[1].text()).toContain('Ágil');

    // Pro: 30.000 with 10% off → 27.000/h, 60h → 1.620.000
    expect(rowRate(wrapper, 7)).toContain('27.000');
    expect(rowTotal(wrapper, 7)).toContain('1.620.000');
  });

  it('switching to manual prefills from the catalog and reprices every row', async () => {
    const { wrapper } = await mountTab();

    await wrapper.find('[data-testid="hour-rate-mode-manual"]').trigger('click');
    await flushPromises();

    const input = wrapper.find('[data-testid="hour-rate-manual-input"]');
    expect(input.exists()).toBe(true);

    await input.setValue('60.000');
    await flushPromises();

    // Pro: 60.000 with 10% off → 54.000/h, 60h → 3.240.000
    expect(rowRate(wrapper, 7)).toContain('54.000');
    expect(rowTotal(wrapper, 7)).toContain('3.240.000');
    // Ágil keeps its catalog hours/discount, only the rate changed.
    expect(rowRate(wrapper, 8)).toContain('60.000');
    expect(rowTotal(wrapper, 8)).toContain('1.200.000');
  });

  it('a per-package override beats the manual base rate', async () => {
    const { wrapper } = await mountTab({
      content: { hourPackagesMode: 'manual', manualHourlyRate: 60000, manualCurrency: 'COP' },
    });

    await wrapper.find('[data-testid="hour-rate-override-8"]').setValue('100.000');
    await flushPromises();

    expect(rowRate(wrapper, 8)).toContain('100.000');
    // The other package still follows the base rate.
    expect(rowRate(wrapper, 7)).toContain('54.000');
  });

  it('keeps the manual rate when switching back to auto and restores it on re-enable', async () => {
    const { wrapper } = await mountTab({
      content: { hourPackagesMode: 'manual', manualHourlyRate: 60000, manualCurrency: 'COP' },
    });
    expect(rowRate(wrapper, 8)).toContain('60.000');

    await wrapper.find('[data-testid="hour-rate-mode-auto"]').trigger('click');
    await flushPromises();
    // Auto rules while it is on: back to the catalog rate.
    expect(rowRate(wrapper, 8)).toContain('30.000');

    await wrapper.find('[data-testid="hour-rate-mode-manual"]').trigger('click');
    await flushPromises();
    expect(rowRate(wrapper, 8)).toContain('60.000');
  });

  it('saves only the rate keys and never the catalog-owned ones', async () => {
    const { wrapper, proposalStore } = await mountTab();

    await wrapper.find('[data-testid="hour-rate-mode-manual"]').trigger('click');
    await wrapper.find('[data-testid="hour-rate-manual-input"]').setValue('60.000');
    await wrapper.find('[data-testid="hour-rate-override-8"]').setValue('100.000');
    await flushPromises();
    await wrapper.find('[data-testid="hour-rate-save"]').trigger('click');
    await flushPromises();

    expect(proposalStore.updateSection).toHaveBeenCalledTimes(1);
    const [sectionId, payload] = proposalStore.updateSection.mock.calls[0];
    expect(sectionId).toBe(42);
    expect(payload.content_json).toMatchObject({
      hourPackagesMode: 'manual',
      manualHourlyRate: 60000,
      manualCurrency: 'COP',
      manualPackageRates: [{ packageId: 8, hourlyRate: 100000 }],
    });
    // Catalog-owned values are passed through as they were, never recomputed.
    expect(payload.content_json.hourlyRate).toBe(30000);
    expect(payload.content_json.currency).toBe('COP');
  });

  it('falls back to auto and warns when the manual rate was set in another currency', async () => {
    const { wrapper } = await mountTab({
      content: {
        hourPackagesMode: 'manual',
        manualHourlyRate: 60000,
        manualCurrency: 'USD',
      },
    });

    expect(wrapper.find('[data-testid="hour-rate-currency-mismatch"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="hour-rate-manual-input"]').exists()).toBe(false);
    expect(rowRate(wrapper, 8)).toContain('30.000');
  });

  it('offers to create the section when the proposal has none', async () => {
    const { wrapper, proposalStore } = await mountTab({ section: null });

    expect(wrapper.find('[data-testid="hour-rate-no-section"]').exists()).toBe(true);
    await wrapper.find('[data-testid="hour-rate-create-section"]').trigger('click');
    expect(proposalStore.createSection).toHaveBeenCalledWith(3, 'commercial_conditions');
  });

  it('warns and previews from the stored snapshot when the catalog is empty', async () => {
    const { wrapper } = await mountTab({
      catalog: [],
      content: {
        packages: [
          { name: 'Snapshot', hours: 10, discountPercent: 0, note: '', hourlyRate: 20000 },
        ],
      },
    });

    expect(wrapper.find('[data-testid="hour-rate-empty-catalog"]').exists()).toBe(true);
    const rows = wrapper.findAll('[data-testid^="hour-rate-row-"]');
    expect(rows).toHaveLength(1);
    expect(rows[0].text()).toContain('Snapshot');
    expect(rows[0].text()).toContain('200.000');
  });

  it('warns when the section is disabled and will not reach the PDF', async () => {
    const section = buildSection();
    section.is_enabled = false;
    const { wrapper } = await mountTab({ section });

    expect(wrapper.find('[data-testid="hour-rate-disabled-warning"]').exists()).toBe(true);
  });
});

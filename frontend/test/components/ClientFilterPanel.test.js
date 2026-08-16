import { mount } from '@vue/test-utils';
import ClientFilterPanel from '../../components/clients/ClientFilterPanel.vue';

const emptyFilters = {
  lastStatuses: [], projectTypes: [], marketTypes: [],
  totalProposalsMin: null, totalProposalsMax: null,
  acceptedMin: null, acceptedMax: null,
  lastActivityAfter: null, lastActivityBefore: null,
  hostingStatus: '', projectStatus: '', billingData: '',
  documentsStatus: '', diagnosticStatus: '', emailStatus: '',
};

function mountPanel(props = {}, { stubChoice = true } = {}) {
  const stubs = { ProposalFilterDropdown: true, ProposalFilterRangeDropdown: true };
  if (stubChoice) stubs.ProposalFilterChoiceDropdown = true;
  return mount(ClientFilterPanel, {
    props: { modelValue: emptyFilters, isOpen: true, filterCount: 0, ...props },
    global: { stubs },
  });
}

const resetButton = (wrapper) =>
  wrapper.findAll('button').find((b) => b.text().includes('Limpiar todo'));

describe('ClientFilterPanel', () => {
  it('shows the filter panel content when isOpen is true', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.find('div').isVisible()).toBe(true);
  });

  it('hides the filter panel content when isOpen is false', () => {
    const wrapper = mountPanel({ isOpen: false });

    expect(wrapper.find('div').isVisible()).toBe(false);
  });

  it('shows "Limpiar todo" button when filterCount is greater than zero', () => {
    const wrapper = mountPanel({ filterCount: 2 });

    expect(wrapper.text()).toContain('Limpiar todo');
  });

  it('hides "Limpiar todo" button when filterCount is zero', () => {
    const wrapper = mountPanel({ filterCount: 0 });

    // The panel itself must still be there, or an empty render would pass.
    expect(wrapper.text()).toContain('Propuestas');
    expect(wrapper.text()).not.toContain('Limpiar todo');
  });

  it('emits reset when the "Limpiar todo" button is clicked', async () => {
    const wrapper = mountPanel({ filterCount: 1 });

    await resetButton(wrapper).trigger('click');

    expect(wrapper.emitted('reset')).toHaveLength(1);
  });

  it('labels the proposal-status control by what it filters', () => {
    // It reads the last proposal's status, not the client's own state — the
    // ambiguous "Estado" is what made the two look like the same filter.
    const wrapper = mountPanel();

    expect(wrapper.html()).toContain('Estado de propuesta');
  });

  it('offers a composable control for every predefined filter', () => {
    const wrapper = mountPanel({}, { stubChoice: false });

    expect(wrapper.find('[data-testid="client-filter-hosting-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="client-filter-project-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="client-filter-billing-data"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="client-filter-documents-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="client-filter-diagnostic-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="client-filter-email-status"]').exists()).toBe(true);
  });

  it('names the diagnostic and email modules on their chips too', () => {
    const wrapper = mountPanel({
      modelValue: {
        ...emptyFilters,
        diagnosticStatus: 'unconverted',
        emailStatus: 'failed',
      },
      filterCount: 2,
    });

    expect(wrapper.text()).toContain('Diagnóstico: Diagnóstico sin propuesta posterior');
    expect(wrapper.text()).toContain('Emails: Con envíos fallidos');
  });

  it('clearing the diagnostic chip emits the filters without it', async () => {
    // CHIP_RESET is the one entry in this slice with no derivation behind it.
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, diagnosticStatus: 'unconverted' },
      filterCount: 1,
    });

    await wrapper.get('[data-testid="client-filter-chip-diagnosticStatus"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0][0].diagnosticStatus).toBe('');
  });

  it('clearing the email chip emits the filters without it', async () => {
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, emailStatus: 'cold' },
      filterCount: 1,
    });

    await wrapper.get('[data-testid="client-filter-chip-emailStatus"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0][0].emailStatus).toBe('');
  });

  it('names the module each active chip comes from', () => {
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, lastStatuses: ['draft'], hostingStatus: 'charged' },
      filterCount: 2,
    });

    expect(wrapper.text()).toContain('Propuestas:');
    expect(wrapper.text()).toContain('Hosting: Con hosting cobrado');
  });

  it('clearing a subfilter chip emits the filters without it', async () => {
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, hostingStatus: 'charged' },
      filterCount: 1,
    });

    await wrapper.get('[data-testid="client-filter-chip-hostingStatus"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0][0].hostingStatus).toBe('');
  });

  it('clearing one chip leaves the other cuts alone', async () => {
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, hostingStatus: 'charged', billingData: 'missing' },
      filterCount: 2,
    });

    await wrapper.get('[data-testid="client-filter-chip-hostingStatus"]').trigger('click');

    const emitted = wrapper.emitted('update:modelValue')[0][0];
    expect(emitted.hostingStatus).toBe('');
    expect(emitted.billingData).toBe('missing');
  });
});

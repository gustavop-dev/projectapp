jest.mock('../../stores/diagnostics_constants', () => ({
  STATUS_META: {
    draft:       { label: 'Borrador',      cls: '' },
    sent:        { label: 'Enviada',       cls: '' },
    accepted:    { label: 'Aceptada',      cls: '' },
    rejected:    { label: 'Rechazada',     cls: '' },
  },
}));

import { mount } from '@vue/test-utils';
import DiagnosticFilterPanel from '../../components/WebAppDiagnostic/DiagnosticFilterPanel.vue';

function emptyFilter() {
  return {
    statuses: [],
    investmentMin: null,
    investmentMax: null,
    createdAfter: null,
    createdBefore: null,
  };
}

function mountPanel(propsOverrides = {}) {
  return mount(DiagnosticFilterPanel, {
    props: {
      modelValue: emptyFilter(),
      isOpen: false,
      filterCount: 0,
      ...propsOverrides,
    },
    global: {
      stubs: {
        ProposalFilterDropdown: {
          template: '<div data-testid="filter-dropdown"></div>',
          props: ['label', 'options', 'modelValue'],
          emits: ['update:modelValue'],
        },
        ProposalFilterRangeDropdown: {
          template: '<div data-testid="filter-range-dropdown"></div>',
          props: ['label', 'type', 'minPlaceholder', 'maxPlaceholder', 'minValue', 'maxValue'],
          emits: ['update:minValue', 'update:maxValue'],
        },
      },
    },
  });
}

describe('DiagnosticFilterPanel', () => {
  // ── Visibility ─────────────────────────────────────────────────────────────

  it('hides the panel when isOpen is false', () => {
    const wrapper = mountPanel({ isOpen: false });

    expect(wrapper.find('.mb-4').isVisible()).toBe(false);
  });

  it('shows the panel when isOpen is true', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.find('.mb-4').isVisible()).toBe(true);
  });

  // ── filterCount ────────────────────────────────────────────────────────────

  it('does not render the clear button when filterCount is zero', () => {
    const wrapper = mountPanel({ isOpen: true, filterCount: 0 });
    const buttons = wrapper.findAll('button').filter((b) => b.text().includes('Limpiar'));

    expect(buttons).toHaveLength(0);
  });

  it('renders the clear button when filterCount is greater than zero', () => {
    const wrapper = mountPanel({ isOpen: true, filterCount: 2 });
    const clearBtn = wrapper.findAll('button').find((b) => b.text().includes('Limpiar'));

    expect(clearBtn).toBeTruthy();
  });

  it('emits reset when the clear button is clicked', async () => {
    const wrapper = mountPanel({ isOpen: true, filterCount: 1 });
    const clearBtn = wrapper.findAll('button').find((b) => b.text().includes('Limpiar'));

    await clearBtn.trigger('click');

    expect(wrapper.emitted('reset')).toBeTruthy();
  });

  // ── activeChips ────────────────────────────────────────────────────────────

  it('renders no chips when all filter values are empty', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.findAll('[class*="rounded-full"]')).toHaveLength(0);
  });

  it('renders a status chip when statuses filter is non-empty', () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), statuses: ['draft'] },
    });

    expect(wrapper.text()).toContain('Estado:');
    expect(wrapper.text()).toContain('Borrador');
  });

  it('renders an investment chip using ≥ operator when only min is set', () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), investmentMin: 500 },
    });

    expect(wrapper.text()).toContain('Inversión:');
    expect(wrapper.text()).toContain('≥ 500');
  });

  it('renders an investment chip using ≤ operator when only max is set', () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), investmentMax: 1000 },
    });

    expect(wrapper.text()).toContain('≤ 1000');
  });

  it('renders an investment chip with range when both min and max are set', () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), investmentMin: 100, investmentMax: 500 },
    });

    expect(wrapper.text()).toContain('100–500');
  });

  it('renders a created-date chip when createdAfter is set', () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), createdAfter: '2025-01-01' },
    });

    expect(wrapper.text()).toContain('Creado:');
    expect(wrapper.text()).toContain('desde 2025-01-01');
  });

  it('renders a created-date chip with arrow format when both dates are set', () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), createdAfter: '2025-01-01', createdBefore: '2025-12-31' },
    });

    expect(wrapper.text()).toContain('2025-01-01 → 2025-12-31');
  });

  // ── clearChip ──────────────────────────────────────────────────────────────

  it('clearChip emits update:modelValue resetting statuses to empty array', async () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), statuses: ['draft'] },
    });
    const chipClose = wrapper.find('button[class*="hover:text-red"]');

    await chipClose.trigger('click');

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].statuses).toEqual([]);
  });

  it('clearChip emits update:modelValue resetting investment range to null', async () => {
    const wrapper = mountPanel({
      isOpen: true,
      modelValue: { ...emptyFilter(), investmentMin: 200, investmentMax: 800 },
    });
    const chipClose = wrapper.find('button[class*="hover:text-red"]');

    await chipClose.trigger('click');

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    const payload = events[events.length - 1][0];
    expect(payload.investmentMin).toBeNull();
    expect(payload.investmentMax).toBeNull();
  });

  // ── child components ───────────────────────────────────────────────────────

  it('renders ProposalFilterDropdown for the status field', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.find('[data-testid="filter-dropdown"]').exists()).toBe(true);
  });

  it('renders ProposalFilterRangeDropdown stubs for investment and date fields', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.findAll('[data-testid="filter-range-dropdown"]')).toHaveLength(2);
  });
});

/**
 * ProjectCatalogSelect: the catalog-wide combobox behind the bulk bar's
 * Proyecto target.
 *
 * Unlike ProjectSelect it searches EVERY project (by name or client),
 * fetches the catalog lazily on first open, lists actives first, and emits
 * the FULL row — the assignment plan needs `client.profile_id` to name the
 * rows the action must not touch.
 */
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ProjectCatalogSelect from '../../../components/accounting/ProjectCatalogSelect.vue';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}));

jest.mock('@vueuse/core', () => ({
  ...jest.requireActual('@vueuse/core'),
  onClickOutside: jest.fn(),
}));

const { get_request } = require('../../../stores/services/request_http');

const CATALOG = {
  data: {
    results: [
      {
        id: 40, name: 'Kore Web', status: 'decommissioned', status_label: 'Dado de baja',
        current_state: {
          id: 6, name: 'Dado de baja', operational_effect: 'decommissioned', color: 'gray',
        },
        client: { profile_id: 7, name: 'Kore SAS' },
      },
      {
        id: 41, name: 'Vastago', status: 'active', status_label: 'Activo',
        current_state: { id: 2, name: 'Activo', operational_effect: 'operating', color: 'emerald' },
        client: { profile_id: 9, name: 'Deivis Ríos' },
      },
    ],
    meta: {},
  },
};

function mountSelect(props = {}) {
  setActivePinia(createPinia());
  return mount(ProjectCatalogSelect, { props });
}

const input = (wrapper) => wrapper.find('[data-testid="project-catalog-select"]');

describe('ProjectCatalogSelect', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    get_request.mockResolvedValue(CATALOG);
  });

  it('loads the catalog lazily with operational projects before closed projects', async () => {
    const wrapper = mountSelect();
    expect(get_request).not.toHaveBeenCalled();

    await input(wrapper).trigger('focus');
    await flushPromises();

    expect(get_request).toHaveBeenCalledWith('projects/?scope=all');
    const options = wrapper.findAll('[role="option"]');
    // Operating Vastago outranks decommissioned Kore Web despite the alphabet.
    expect(options.map((option) => option.text())).toEqual([
      'Vastago · Deivis Ríos',
      'Kore Web · Kore SAS · Dado de baja',
    ]);
  });

  it('filters by project name OR client name', async () => {
    const wrapper = mountSelect();
    await input(wrapper).trigger('focus');
    await flushPromises();

    await input(wrapper).setValue('kore');
    await input(wrapper).trigger('input');

    expect(wrapper.find('[data-testid="project-catalog-select-option-40"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="project-catalog-select-option-41"]').exists()).toBe(false);

    await input(wrapper).setValue('deivis');
    await input(wrapper).trigger('input');

    expect(wrapper.find('[data-testid="project-catalog-select-option-41"]').exists()).toBe(true);
  });

  it('selecting emits the id and the FULL catalog row, clearing emits null', async () => {
    const wrapper = mountSelect();
    await input(wrapper).trigger('focus');
    await flushPromises();

    await wrapper.find('[data-testid="project-catalog-select-option-41"]').trigger('click');

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([41]);
    expect(wrapper.emitted('select').at(-1)[0]).toMatchObject({
      id: 41,
      name: 'Vastago',
      client: { profile_id: 9, name: 'Deivis Ríos' },
    });

    await wrapper.setProps({ modelValue: 41 });
    await wrapper.find('[data-testid="project-catalog-select-clear"]').trigger('click');

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([null]);
    expect(wrapper.emitted('select').at(-1)).toEqual([null]);
  });
});

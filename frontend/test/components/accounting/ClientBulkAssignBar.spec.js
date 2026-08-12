import { mount, flushPromises } from '@vue/test-utils';
import ClientBulkAssignBar from '../../../components/accounting/ClientBulkAssignBar.vue';

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'testId', 'placeholder'],
  emits: ['update:modelValue', 'select'],
  template: '<div data-testid="client-autocomplete-stub" />',
};

const ENTITY = { singular: 'hosting', plural: 'hostings' };

const ROWS = [
  { id: 1, client: null, client_name: 'Kore - Marca', domain_url: 'kore.com.co' },
  { id: 2, client: null, client_name: 'Huella - Marca', domain_url: 'tuhuella.co' },
  { id: 3, client: 7, client_display_name: 'Kore SAS', domain_url: 'a.com' },
];

function mountBar(props = {}) {
  return mount(ClientBulkAssignBar, {
    props: {
      rows: ROWS,
      selected: [1, 2],
      filteredIds: [1, 2, 3],
      entity: ENTITY,
      testidPrefix: 'hostings',
      recordLabel: (row) => row.domain_url,
      ...props,
    },
    global: {
      stubs: {
        ClientAutocomplete: ClientAutocompleteStub,
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          template: '<div v-if="modelValue" data-testid="modal"><slot /></div>',
        },
      },
    },
  });
}

/** Pick a client the way ClientAutocomplete does: id via v-model, then `select`. */
async function pickClient(wrapper, client = { id: 5, name: 'Ana Pérez' }) {
  const picker = wrapper.findComponent(ClientAutocompleteStub);
  await picker.vm.$emit('update:modelValue', client.id);
  await picker.vm.$emit('select', client);
  await flushPromises();
}

async function confirm(wrapper) {
  await wrapper.find('[data-testid="confirm-modal-confirm"]').trigger('click');
  await flushPromises();
}

describe('ClientBulkAssignBar — the two actions are separate', () => {
  it('keeps Asignar disabled with the reason on screen until a client is picked', async () => {
    const wrapper = mountBar();

    expect(wrapper.find('[data-testid="hostings-bulk-assign"]').attributes('disabled'))
      .toBeDefined();
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Elige un cliente para poder asignar');

    await pickClient(wrapper);

    expect(wrapper.find('[data-testid="hostings-bulk-assign"]').attributes('disabled'))
      .toBeUndefined();
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').exists()).toBe(false);
  });

  it('blocks Asignar and says why when every selected row already has that client', async () => {
    const wrapper = mountBar({ selected: [3] });

    await pickClient(wrapper, { id: 7, name: 'Kore SAS' });

    expect(wrapper.find('[data-testid="hostings-bulk-assign"]').attributes('disabled'))
      .toBeDefined();
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Todo lo seleccionado ya tiene a Kore SAS');
  });

  it('hides Desvincular when nothing selected has a client to lose', () => {
    const wrapper = mountBar({ selected: [1, 2] });

    expect(wrapper.find('[data-testid="hostings-bulk-unlink"]').exists()).toBe(false);
  });

  it('shows Desvincular as soon as a selected row is linked', () => {
    const wrapper = mountBar({ selected: [1, 3] });

    expect(wrapper.find('[data-testid="hostings-bulk-unlink"]').exists()).toBe(true);
  });
});

describe('ClientBulkAssignBar — nothing runs without confirmation', () => {
  it('breaks a mixed selection into its two halves instead of one flat count', async () => {
    const wrapper = mountBar({ selected: [1, 2, 3] });
    await pickClient(wrapper);

    await wrapper.find('[data-testid="hostings-bulk-assign"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="modal"]').text())
      .toContain('Se asignará Ana Pérez a 3 hostings: 2 sin cliente y 1 que cambia de cliente');
    expect(wrapper.find('[data-testid="client-bulk-summary-assign"]').text())
      .toBe('2 sin cliente pasan a Ana Pérez');
    expect(wrapper.find('[data-testid="client-bulk-summary-reassign"]').text())
      .toBe('1 cambia de cliente a Ana Pérez');
  });

  it('names every affected record and writes nothing until the operator confirms', async () => {
    const wrapper = mountBar({ selected: [1, 2, 3] });
    await pickClient(wrapper);

    await wrapper.find('[data-testid="hostings-bulk-assign"]').trigger('click');
    await flushPromises();

    // A mass edit has to show its scope, not just its size.
    expect(wrapper.find('[data-testid="client-bulk-summary-list"]').text())
      .toContain('kore.com.co');
    expect(wrapper.find('[data-testid="client-bulk-summary-list"]').text())
      .toContain('tuhuella.co');
    expect(wrapper.emitted('submit')).toBeUndefined();

    await confirm(wrapper);

    expect(wrapper.emitted('submit')[0][0]).toMatchObject({
      ids: [1, 2, 3],
      client: 5,
      mode: 'assign',
    });
  });

  it('leaves the rows already on the target out of the payload', async () => {
    const wrapper = mountBar({ selected: [1, 3] });
    await pickClient(wrapper, { id: 7, name: 'Kore SAS' });

    await wrapper.find('[data-testid="hostings-bulk-assign"]').trigger('click');
    await flushPromises();
    await confirm(wrapper);

    expect(wrapper.emitted('submit')[0][0].ids).toEqual([1]);
  });

  it('names the client the rows are being taken from before unlinking', async () => {
    const wrapper = mountBar({ selected: [1, 3] });

    await wrapper.find('[data-testid="hostings-bulk-unlink"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="modal"]').text())
      .toContain('1 hosting quedará sin cliente: 1 de Kore SAS.');
    // Singular breakdown: a single row does not read as "1 quedan".
    expect(wrapper.find('[data-testid="client-bulk-summary-unlink"]').text())
      .toBe('1 queda sin cliente');
    expect(wrapper.find('[data-testid="client-bulk-summary-unchanged"]').text())
      .toBe('1 sin cambios');

    await confirm(wrapper);

    expect(wrapper.emitted('submit')[0][0]).toMatchObject({
      ids: [3],
      client: null,
      mode: 'unlink',
    });
  });

  it('emits nothing when the confirmation is cancelled', async () => {
    const wrapper = mountBar({ selected: [1, 3] });

    await wrapper.find('[data-testid="hostings-bulk-unlink"]').trigger('click');
    await flushPromises();
    await wrapper.findAll('button').find((b) => b.text() === 'Cancelar').trigger('click');
    await flushPromises();

    expect(wrapper.emitted('submit')).toBeUndefined();
  });
});

describe('ClientBulkAssignBar — selection plumbing', () => {
  it('hands the parent every filtered id when asked to select them all', async () => {
    const wrapper = mountBar({ selected: [1] });

    await wrapper.find('[data-testid="hostings-select-all-filtered"]').trigger('click');

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([1, 2, 3]);
  });

  it('drops the offer once everything filtered is already selected', () => {
    const wrapper = mountBar({ selected: [1, 2, 3] });

    expect(wrapper.find('[data-testid="hostings-select-all-filtered"]').exists()).toBe(false);
  });

  it('forgets the picked client when the parent clears the selection', async () => {
    const wrapper = mountBar({ selected: [1] });
    await pickClient(wrapper);
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').exists()).toBe(false);

    await wrapper.setProps({ selected: [] });
    await wrapper.setProps({ selected: [1] });

    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Elige un cliente para poder asignar');
  });

  // The selection survives a filter change and the action still runs on all of
  // it, so the count alone would disagree with what the table is showing.
  it('flags the selected rows the active filter no longer shows', () => {
    const wrapper = mountBar({ selected: [1, 2], filteredIds: [1] });

    expect(wrapper.find('[data-testid="hostings-bulk-outside"]').text())
      .toContain('1 fuera del filtro actual');
  });

  it('says nothing about the filter while the whole selection passes it', () => {
    const wrapper = mountBar({ selected: [1, 2], filteredIds: [1, 2, 3] });

    expect(wrapper.find('[data-testid="hostings-bulk-outside"]').exists()).toBe(false);
  });
});

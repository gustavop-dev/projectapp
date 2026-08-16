import { mount, flushPromises } from '@vue/test-utils';
import BulkAssignBar from '../../../components/accounting/BulkAssignBar.vue';

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'testId', 'placeholder', 'showLinkedHint'],
  emits: ['update:modelValue', 'select'],
  template: '<div data-testid="client-autocomplete-stub" />',
};

const ProjectCatalogSelectStub = {
  name: 'ProjectCatalogSelect',
  props: ['modelValue', 'testId', 'placeholder'],
  emits: ['update:modelValue', 'select'],
  template: '<div data-testid="project-catalog-select-stub" />',
};

const ENTITY = { singular: 'hosting', plural: 'hostings' };

const ROWS = [
  { id: 1, client: null, project: null, client_name: 'Kore - Marca', domain_url: 'kore.com.co' },
  { id: 2, client: null, project: null, client_name: 'Huella - Marca', domain_url: 'tuhuella.co' },
  { id: 3, client: 7, project: null, client_display_name: 'Kore SAS', domain_url: 'a.com' },
  {
    id: 4,
    client: 7,
    project: 41,
    project_name: 'Vieja Web',
    client_display_name: 'Kore SAS',
    domain_url: 'b.com',
  },
];

function mountBar(props = {}) {
  return mount(BulkAssignBar, {
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
        ProjectCatalogSelect: ProjectCatalogSelectStub,
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

describe('BulkAssignBar — the two actions are separate', () => {
  it('keeps Asignar disabled with the reason on screen until a client is picked', async () => {
    const wrapper = mountBar();

    expect(wrapper.find('[data-testid="hostings-bulk-assign"]').attributes('disabled'))
      .toBeDefined();
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Elige un cliente para poder asignar');

    await pickClient(wrapper);

    expect(wrapper.find('[data-testid="hostings-bulk-assign"]').attributes('disabled'))
      .toBeUndefined();
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Cliente enlazado: Ana Pérez (#5)');
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

describe('BulkAssignBar — the row holds its line', () => {
  // El hint del picker crecía DENTRO de la celda del flex y, con
  // `sm:items-center`, re-centraba la fila entera: el input subía y los
  // botones se quedaban abajo. La barra dibuja esa línea ella misma, fuera
  // de la fila, y le pide al picker que no dibuje la suya.
  it('confirms the linked client in its own line, not inside the picker', async () => {
    const wrapper = mountBar({ selected: [1] });

    await pickClient(wrapper);

    expect(wrapper.findComponent(ClientAutocompleteStub).props('showLinkedHint'))
      .toBe(false);
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Cliente enlazado: Ana Pérez (#5)');
  });

  // El salto reportado ocurría justo acá: al elegir y al limpiar. Si la línea
  // pudiera quedar vacía en cualquiera de los dos extremos, la barra cambiaría
  // de alto — así que el ciclo completo tiene que dejarla siempre con texto.
  it('keeps the status line populated through picking and clearing a client', async () => {
    const wrapper = mountBar({ selected: [1] });
    const hint = () => wrapper.find('[data-testid="hostings-bulk-hint"]');

    expect(hint().text()).toContain('Elige un cliente para poder asignar');

    await pickClient(wrapper);
    expect(hint().text()).toContain('Cliente enlazado: Ana Pérez (#5)');

    // Desvincular (la X del picker) suelta el id sin re-emitir `select`.
    // Escribir encima ya NO lo suelta: buscar no es desvincular.
    await wrapper.findComponent(ClientAutocompleteStub).vm.$emit('update:modelValue', null);
    await flushPromises();
    expect(hint().text()).toContain('Elige un cliente para poder asignar');
  });

  // Sin fondo el botón se leía como texto plano y sólo aparecía al pasar el
  // cursor: una acción destructiva no puede depender del hover para existir.
  it('gives Desvincular a destructive background of its own', () => {
    const wrapper = mountBar({ selected: [1, 3] });

    expect(wrapper.find('[data-testid="hostings-bulk-unlink"]').classes())
      .toContain('bg-danger-strong');
  });
});

describe('BulkAssignBar — nothing runs without confirmation', () => {
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

describe('BulkAssignBar — selection plumbing', () => {
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
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Cliente enlazado');

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

const PROJECT = {
  id: 40,
  name: 'Kore Web',
  status: 'active',
  status_label: 'Activo',
  client: { profile_id: 7, name: 'Kore SAS' },
};

async function switchToProject(wrapper) {
  await wrapper
    .find('[data-testid="hostings-bulk-target"]')
    .findAll('button')
    .find((button) => button.text() === 'Proyecto')
    .trigger('click');
  await flushPromises();
}

/** Pick a project the way ProjectCatalogSelect does: id, then the full row. */
async function pickProject(wrapper, project = PROJECT) {
  const picker = wrapper.findComponent(ProjectCatalogSelectStub);
  await picker.vm.$emit('update:modelValue', project.id);
  await picker.vm.$emit('select', project);
  await flushPromises();
}

describe('BulkAssignBar — the Proyecto target', () => {
  it('offers the toggle only where the page enables it', () => {
    expect(mountBar().find('[data-testid="hostings-bulk-target"]').exists())
      .toBe(false);
    expect(
      mountBar({ projectEnabled: true })
        .find('[data-testid="hostings-bulk-target"]').exists(),
    ).toBe(true);
  });

  it('switching targets swaps the picker and keeps the status line talking', async () => {
    const wrapper = mountBar({ projectEnabled: true, selected: [3, 4] });

    await switchToProject(wrapper);

    expect(wrapper.findComponent(ProjectCatalogSelectStub).exists()).toBe(true);
    expect(wrapper.findComponent(ClientAutocompleteStub).exists()).toBe(false);
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('Elige un proyecto para poder asignar');
  });

  it('confirms against the plan and leaves the foreign-client rows out', async () => {
    const wrapper = mountBar({ projectEnabled: true, selected: [1, 3, 4] });
    await switchToProject(wrapper);
    await pickProject(wrapper);

    await wrapper.find('[data-testid="hostings-bulk-assign-project"]').trigger('click');
    await flushPromises();

    // Row 1 has no client: named apart, never in the payload.
    expect(wrapper.find('[data-testid="project-bulk-summary-blocked"]').text())
      .toContain('kore.com.co');
    expect(wrapper.find('[data-testid="project-bulk-summary-list"]').text())
      .toContain('Vieja Web');
    expect(wrapper.emitted('submit-project')).toBeUndefined();

    await confirm(wrapper);

    expect(wrapper.emitted('submit-project')[0][0]).toMatchObject({
      ids: [3, 4],
      project: 40,
      mode: 'assign',
    });
  });

  it('blocks Asignar with the ownership reason when nothing can change', async () => {
    const wrapper = mountBar({ projectEnabled: true, selected: [1, 2] });
    await switchToProject(wrapper);
    await pickProject(wrapper);

    expect(
      wrapper.find('[data-testid="hostings-bulk-assign-project"]').attributes('disabled'),
    ).toBeDefined();
    expect(wrapper.find('[data-testid="hostings-bulk-hint"]').text())
      .toContain('pertenece a otro cliente');
  });

  it('offers Quitar proyecto only when the selection has one to lose', async () => {
    const without = mountBar({ projectEnabled: true, selected: [1, 3] });
    await switchToProject(without);
    expect(without.find('[data-testid="hostings-bulk-unlink-project"]').exists())
      .toBe(false);

    const wrapper = mountBar({ projectEnabled: true, selected: [4] });
    await switchToProject(wrapper);
    await wrapper.find('[data-testid="hostings-bulk-unlink-project"]').trigger('click');
    await flushPromises();
    await confirm(wrapper);

    expect(wrapper.emitted('submit-project')[0][0]).toMatchObject({
      ids: [4],
      project: null,
      mode: 'unlink',
    });
  });
});

/**
 * A record can leave the selection two ways, and the bar must not confuse
 * them: the filters can stop showing it (kept, and announced) or it can stop
 * existing (dropped by the page, and gone from every count). The page owns the
 * pruning — these pin what the bar does with the result of it.
 */
describe('BulkAssignBar — a deleted record is not a filtered one', () => {
  it('counts only what the page still holds once the deleted id is pruned', () => {
    // Row 2 was deleted: gone from `rows`, gone from `filteredIds`, and the
    // page has already dropped it from the selection.
    const wrapper = mountBar({
      rows: [ROWS[0], ROWS[2]],
      selected: [1],
      filteredIds: [1, 3],
    });

    expect(wrapper.find('[data-testid="hostings-bulk-bar"]').text())
      .toContain('1 seleccionado');
    // The deleted row must not resurface as "fuera del filtro actual" — that
    // notice is about records that still exist.
    expect(wrapper.find('[data-testid="hostings-bulk-outside"]').exists()).toBe(false);
  });

  it('leaves on its own when the pruning empties the selection', async () => {
    const wrapper = mountBar({ selected: [1], filteredIds: [1] });
    expect(wrapper.find('[data-testid="hostings-bulk-bar"]').exists()).toBe(true);

    await wrapper.setProps({ rows: [ROWS[2]], selected: [], filteredIds: [3] });

    // No reload, no Cancelar.
    expect(wrapper.find('[data-testid="hostings-bulk-bar"]').exists()).toBe(false);
  });

  it('keeps a still-existing row that the filter hides, and says so', () => {
    // Same shape as the case above, except row 2 was only filtered out. It
    // stays selected and stays counted.
    const wrapper = mountBar({ selected: [1, 2], filteredIds: [1] });

    expect(wrapper.find('[data-testid="hostings-bulk-bar"]').text())
      .toContain('2 seleccionados');
    expect(wrapper.find('[data-testid="hostings-bulk-outside"]').text())
      .toContain('1 fuera del filtro actual');
  });

  it('leaves a stale id out of the payload it submits', async () => {
    // The safety net for the window the page cannot close: the confirmation
    // freezes the plan when it opens, and a row can vanish while it is up.
    const wrapper = mountBar({ selected: [1, 99] });
    await pickClient(wrapper);

    await wrapper.find('[data-testid="hostings-bulk-assign"]').trigger('click');
    await flushPromises();
    await confirm(wrapper);

    expect(wrapper.emitted('submit')[0][0].ids).toEqual([1]);
  });
});

/**
 * ProjectSelect: the per-client project combobox with on-the-fly creation.
 *
 * Covers the local filtering over the fetched list (no server search), the
 * create affordance appearing only when nothing matches, the inline panel
 * that creates + auto-selects (and stays open on a 400), and the guard that
 * clears the selection when the client changes.
 */
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import ProjectSelect from '../../components/accounting/ProjectSelect.vue';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request,
  create_request,
} = require('../../stores/services/request_http');

const mountedWrappers = [];

const PROJECTS = [
  {
    id: 11,
    name: 'Kore',
    status: 'active',
    status_label: 'Activo',
    current_state: { id: 2, name: 'Activo', operational_effect: 'operating', color: 'emerald' },
  },
  {
    id: 12,
    name: 'Vástago',
    status: 'paused',
    status_label: 'Pausado',
    current_state: { id: 3, name: 'Pausado', operational_effect: 'paused', color: 'yellow' },
  },
];

function mountSelect(props = {}) {
  setActivePinia(createPinia());
  const wrapper = mount(ProjectSelect, {
    props: { clientProfileId: 7, clientLabel: 'Deivis Ríos', ...props },
    global: {
      plugins: [createPinia()],
      stubs: {
        Teleport: true,
        BaseFormField: {
          props: ['label', 'hint'],
          template: '<div><label v-if="label">{{ label }}</label><slot /></div>',
        },
        BaseInput: {
          props: ['modelValue', 'placeholder'],
          emits: ['update:modelValue'],
          template:
            '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseButton: {
          props: ['variant', 'size', 'disabled', 'type'],
          // `emits` declared so the parent's @click doesn't ALSO fall through
          // as a native listener (it would double-fire every handler).
          emits: ['click'],
          template:
            '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
  mountedWrappers.push(wrapper);
  return wrapper;
}

const input = (wrapper) => wrapper.find('[data-testid="project-select"]');

describe('ProjectSelect', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    get_request.mockResolvedValue({ data: { results: PROJECTS } });
  });

  afterEach(() => {
    mountedWrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  });

  it('stays disabled until a client is chosen', async () => {
    const wrapper = mountSelect({ clientProfileId: null });
    await flushPromises();

    expect(input(wrapper).attributes('disabled')).toBeDefined();
    expect(input(wrapper).attributes('placeholder')).toBe('Elige un cliente primero');
    expect(get_request).not.toHaveBeenCalled();
  });

  it('filters the fetched list locally while typing', async () => {
    const wrapper = mountSelect();
    await flushPromises();

    await input(wrapper).trigger('focus');
    expect(wrapper.find('[data-testid="project-select-option-11"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="project-select-option-12"]').exists()).toBe(true);

    await input(wrapper).setValue('vasta');
    await input(wrapper).trigger('input');

    expect(wrapper.find('[data-testid="project-select-option-11"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="project-select-option-12"]').exists()).toBe(true);
    // Local filtering: still the single fetch from mount.
    expect(get_request).toHaveBeenCalledTimes(1);
  });

  it('selecting an option commits the numeric id and closes', async () => {
    const wrapper = mountSelect();
    await flushPromises();

    await input(wrapper).trigger('focus');
    await wrapper.find('[data-testid="project-select-option-12"]').trigger('click');

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([12]);
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false);
  });

  it('offers creation only when nothing matches, seeded with the term', async () => {
    const wrapper = mountSelect();
    await flushPromises();

    await input(wrapper).trigger('focus');
    expect(wrapper.find('[data-testid="project-select-create-new"]').exists()).toBe(false);

    await input(wrapper).setValue('Crushme');
    await input(wrapper).trigger('input');
    const createRow = wrapper.find('[data-testid="project-select-create-new"]');
    expect(createRow.text()).toContain('Crear proyecto "Crushme"');

    await createRow.trigger('click');
    expect(wrapper.find('[data-testid="project-select-inline-create"]').exists()).toBe(true);
    expect(
      wrapper.find('[data-testid="project-select-inline-name"]').element.value,
    ).toBe('Crushme');
  });

  it('creating inline auto-selects the new project', async () => {
    create_request.mockResolvedValueOnce({
      data: {
        id: 31,
        name: 'Crushme',
        status: 'active',
        status_label: 'Activo',
        unlinked_hostings_count: 2,
        unlinked_incomes_count: 1,
      },
    });
    const wrapper = mountSelect();
    await flushPromises();

    await input(wrapper).trigger('focus');
    await input(wrapper).setValue('Crushme');
    await input(wrapper).trigger('input');
    await wrapper.find('[data-testid="project-select-create-new"]').trigger('click');
    await wrapper.find('[data-testid="project-select-inline-create-save"]').trigger('click');
    await flushPromises();

    expect(create_request).toHaveBeenCalledWith('projects/create/', {
      name: 'Crushme',
      client_profile_id: 7,
    });
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([31]);
    // The full annotated row travels with `created`: the page decides the
    // backlog offer from these counters.
    expect(wrapper.emitted('created')[0][0]).toMatchObject({
      id: 31,
      name: 'Crushme',
      unlinked_hostings_count: 2,
      unlinked_incomes_count: 1,
    });
    expect(wrapper.find('[data-testid="project-select-inline-create"]').exists()).toBe(false);
  });

  it('a rejected create keeps the panel open with the backend message', async () => {
    create_request.mockRejectedValueOnce({
      response: { status: 400, data: { name: ['Este campo no puede estar en blanco.'] } },
    });
    const wrapper = mountSelect();
    await flushPromises();

    await input(wrapper).trigger('focus');
    await input(wrapper).setValue('Crushme');
    await input(wrapper).trigger('input');
    await wrapper.find('[data-testid="project-select-create-new"]').trigger('click');
    await wrapper.find('[data-testid="project-select-inline-create-save"]').trigger('click');
    await flushPromises();

    expect(create_request).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[data-testid="project-select-inline-create"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="project-select-inline-create-error"]').text())
      .toBe('Este campo no puede estar en blanco.');
    expect(wrapper.emitted('update:modelValue')?.at(-1)).not.toEqual([31]);
  });

  it('warns inline about a same-name project without blocking the save', async () => {
    // Typing an accent/case variant matches the local filter (so no create
    // row); the collision is reachable by editing the inline name instead.
    const wrapper = mountSelect();
    await flushPromises();

    await input(wrapper).trigger('focus');
    await input(wrapper).setValue('Vastago 2');
    await input(wrapper).trigger('input');
    await wrapper.find('[data-testid="project-select-create-new"]').trigger('click');
    await wrapper.find('[data-testid="project-select-inline-name"]').setValue('vastago');

    expect(wrapper.find('[data-testid="project-select-duplicate-warning"]').text())
      .toContain('Vástago');
    expect(
      wrapper.find('[data-testid="project-select-inline-create-save"]').attributes('disabled'),
    ).toBeUndefined();
  });

  describe('autoSelectSingle (PA-51: proposing is pre-filling)', () => {
    it('pre-selects the only available project of the client', async () => {
      // PROJECTS has one operating project and one paused project.
      const wrapper = mountSelect({ autoSelectSingle: true });
      await flushPromises();

      expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([11]);
      expect(input(wrapper).element.value).toBe('Kore');
    });

    it('leaves the field empty when two projects are available', async () => {
      get_request.mockResolvedValue({
        data: {
          results: [
            {
              id: 11,
              name: 'Kore',
              status: 'active',
              status_label: 'Activo',
              current_state: { id: 2, name: 'Activo', operational_effect: 'operating' },
            },
            {
              id: 13,
              name: 'Crushme',
              status: 'development',
              status_label: 'En desarrollo',
              current_state: { id: 1, name: 'En desarrollo', operational_effect: 'development' },
            },
          ],
        },
      });
      const wrapper = mountSelect({ autoSelectSingle: true });
      await flushPromises();

      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('leaves the field empty when the only project is unavailable', async () => {
      get_request.mockResolvedValue({
        data: {
          results: [
            {
              id: 12,
              name: 'Vástago',
              status: 'paused',
              status_label: 'Pausado',
              current_state: { id: 3, name: 'Pausado', operational_effect: 'paused' },
            },
          ],
        },
      });
      const wrapper = mountSelect({ autoSelectSingle: true });
      await flushPromises();

      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('never overwrites a committed value (edits stay untouched)', async () => {
      const wrapper = mountSelect({ autoSelectSingle: true, modelValue: 12 });
      await flushPromises();

      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('a deliberate clear stays cleared instead of refilling itself', async () => {
      const wrapper = mountSelect({ autoSelectSingle: true });
      await flushPromises();
      expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([11]);

      await wrapper.find('[data-testid="project-select-clear"]').trigger('click');
      await flushPromises();

      expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([null]);
      expect(input(wrapper).element.value).toBe('');
    });
  });

  it('changing the client clears a selection the backend would reject', async () => {
    const wrapper = mountSelect({ modelValue: 11 });
    await flushPromises();

    // La lista del cliente nuevo no contiene el proyecto 11: el par sería
    // rechazado por el backend, así que el picker lo limpia tras recargar.
    get_request.mockResolvedValue({
      data: {
        results: [{ id: 21, name: 'Otro', status: 'active', status_label: 'Activo' }],
      },
    });
    await wrapper.setProps({ clientProfileId: 8 });
    await flushPromises();

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([null]);
  });

  // Escribir filtra la lista; desvincular es la X. Antes un caracter soltaba el
  // id (y marcaba userCleared), así que rozar el campo ensuciaba el formulario
  // y al guardar desvinculaba el proyecto.
  it('keeps the committed project while typing and restores its name on close', async () => {
    const wrapper = mountSelect({ modelValue: 11 });
    await flushPromises();
    expect(input(wrapper).element.value).toBe('Kore');

    await input(wrapper).setValue('vasta');
    await input(wrapper).trigger('input');

    expect(wrapper.emitted('update:modelValue')).toBeUndefined();

    await input(wrapper).trigger('keydown.esc');

    expect(input(wrapper).element.value).toBe('Kore');
  });

  it('commits the new project when one is picked after typing over another', async () => {
    const wrapper = mountSelect({ modelValue: 11 });
    await flushPromises();

    await input(wrapper).setValue('vasta');
    await input(wrapper).trigger('input');
    await wrapper.find('[data-testid="project-select-option-12"]').trigger('click');

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([12]);
    expect(input(wrapper).element.value).toBe('Vástago');
  });

  describe('allowNoClient (cascada inversa: proyecto primero)', () => {
    const OWNED = [
      {
        id: 11, name: 'Kore', status: 'active', status_label: 'Activo',
        client_profile_id: 7, client_display_name: 'Deivis Ríos',
      },
      {
        id: 12, name: 'Vástago', status: 'paused', status_label: 'Pausado',
        client_profile_id: 9, client_display_name: 'Ana Pérez',
      },
    ];

    it('lists every project with its owner when no client is fixed', async () => {
      get_request.mockResolvedValue({ data: { results: OWNED } });
      const wrapper = mountSelect({ clientProfileId: null, allowNoClient: true });
      await flushPromises();

      expect(input(wrapper).attributes('disabled')).toBeUndefined();
      expect(input(wrapper).attributes('placeholder')).toBe('Buscar un proyecto...');
      expect(get_request).toHaveBeenCalledWith('accounting/projects/');

      await input(wrapper).trigger('focus');
      expect(wrapper.find('[data-testid="project-select-owner-11"]').text())
        .toContain('Deivis Ríos');
    });

    it('emits the full row on select so the parent can autofill the client', async () => {
      get_request.mockResolvedValue({ data: { results: OWNED } });
      const wrapper = mountSelect({ clientProfileId: null, allowNoClient: true });
      await flushPromises();

      await input(wrapper).trigger('focus');
      await wrapper.find('[data-testid="project-select-option-11"]').trigger('click');

      expect(wrapper.emitted('select').at(-1)[0]).toMatchObject({
        id: 11, client_profile_id: 7, client_display_name: 'Deivis Ríos',
      });
      expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([11]);
    });

    it('keeps the selection when the new client still owns the project', async () => {
      const wrapper = mountSelect({
        clientProfileId: null, allowNoClient: true, modelValue: 11,
      });
      await flushPromises();

      // El padre autocompleta el cliente DESDE el proyecto elegido; 11 está
      // en la lista del cliente 7, así que la recarga no borra la elección.
      await wrapper.setProps({ clientProfileId: 7 });
      await flushPromises();

      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('hides the create affordance while no client is fixed', async () => {
      get_request.mockResolvedValue({ data: { results: [] } });
      const wrapper = mountSelect({ clientProfileId: null, allowNoClient: true });
      await flushPromises();

      await input(wrapper).trigger('focus');
      expect(wrapper.find('[role="listbox"]').text()).toContain('No hay proyectos todavía');
      expect(wrapper.find('[data-testid="project-select-create-new"]').exists()).toBe(false);
    });
  });
});

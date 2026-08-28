import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import ClientAutocomplete from '../../components/ui/ClientAutocomplete.vue';

const mockStore = {
  searchClients: jest.fn(),
};

jest.mock('../../stores/proposal_clients', () => ({
  useProposalClientsStore: () => mockStore,
}));

jest.mock('@vueuse/core', () => ({
  useDebounceFn: (fn) => fn,
}));

const mountedWrappers = [];

function mountAutocomplete(props = { modelValue: null }) {
  const wrapper = mount(ClientAutocomplete, {
    props,
    global: {
      mocks: {
        $t: (key) => key,
      },
      stubs: {
        Teleport: true,
        NuxtLink: { template: '<a><slot /></a>' },
      },
    },
  });
  mountedWrappers.push(wrapper);
  return wrapper;
}

function clickOutside() {
  document.body.dispatchEvent(new MouseEvent('pointerdown', { bubbles: true }));
}

describe('ClientAutocomplete', () => {
  beforeEach(() => {
    mockStore.searchClients.mockReset();
    localStorage.clear();
  });

  afterEach(() => {
    mountedWrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  });

  describe('catalog presentation', () => {
    it('loads the alphabetical catalog without waiting for focus', async () => {
      mockStore.searchClients.mockResolvedValueOnce({
        success: true,
        data: [
          { id: 901, name: 'Amanda', email: 'amanda@example.com', phone: '', company: 'Alfa', is_email_placeholder: false },
        ],
      });

      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();

      expect(mockStore.searchClients).toHaveBeenCalledWith('', {
        offset: 0,
        limit: 20,
        order: 'name',
      });
      expect(wrapper.get('[data-testid="client-catalog"]').isVisible()).toBe(true);
      expect(wrapper.get('[data-testid="client-autocomplete-option-901"]').text())
        .toContain('Amanda');
    });

    it('preserves catalog state after a client is selected', async () => {
      const client = {
        id: 902,
        name: 'Beatriz Bravo',
        email: 'beatriz@example.com',
        phone: '',
        company: 'Beta',
        is_email_placeholder: false,
      };
      mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [client] });
      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();

      const input = wrapper.get('[data-testid="client-autocomplete-input"]');
      mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [client] });
      await input.setValue('bea');
      await flushPromises();
      await wrapper.get('[data-testid="client-autocomplete-option-902"]').trigger('click');

      expect(wrapper.emitted('update:modelValue')).toEqual([[902]]);
      expect(input.element.value).toBe('bea');
      expect(wrapper.get('[data-testid="client-catalog"]').isVisible()).toBe(true);
    });

    it('persists the descending choice from the name header', async () => {
      mockStore.searchClients
        .mockResolvedValueOnce({ success: true, data: [] })
        .mockResolvedValueOnce({ success: true, data: [] });
      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();

      await wrapper.get('[data-testid="client-catalog-sort-name"]').trigger('click');
      await flushPromises();

      expect(mockStore.searchClients).toHaveBeenLastCalledWith('', {
        offset: 0,
        limit: 20,
        order: '-name',
      });
      expect(localStorage.getItem('projectapp-client-catalog-sort-direction')).toBe('desc');
    });

    it('restores the saved direction on a later opening', async () => {
      localStorage.setItem('projectapp-client-catalog-sort-direction', 'desc');
      mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });

      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();

      expect(mockStore.searchClients).toHaveBeenLastCalledWith('', {
        offset: 0,
        limit: 20,
        order: '-name',
      });
      expect(wrapper.get('[data-testid="client-catalog-sort-name"]').attributes('aria-label'))
        .toContain('A a Z');
    });

    it('loads the next catalog page from its own scroll region', async () => {
      mockStore.searchClients
        .mockResolvedValueOnce({
          success: true,
          data: [
            { id: 903, name: 'Carolina', email: 'carolina@example.com', phone: '', company: '', is_email_placeholder: false },
          ],
          hasMore: true,
          nextOffset: 1,
        })
        .mockResolvedValueOnce({
          success: true,
          data: [
            { id: 904, name: 'Diana', email: '', phone: '', company: 'Delta', is_email_placeholder: true },
          ],
          hasMore: false,
          nextOffset: 2,
        });
      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();
      const catalog = wrapper.get('[data-testid="client-catalog-scroll"]');
      Object.defineProperty(catalog.element, 'scrollHeight', { configurable: true, value: 400 });
      Object.defineProperty(catalog.element, 'clientHeight', { configurable: true, value: 320 });
      Object.defineProperty(catalog.element, 'scrollTop', { configurable: true, value: 80 });

      await catalog.trigger('scroll');
      await flushPromises();

      expect(mockStore.searchClients).toHaveBeenLastCalledWith('', {
        offset: 1,
        limit: 20,
        order: 'name',
      });
      expect(wrapper.get('[data-testid="client-autocomplete-option-904"]').exists()).toBe(true);
    });

    it('marks a catalog client whose email is missing', async () => {
      mockStore.searchClients.mockResolvedValueOnce({
        success: true,
        data: [
          { id: 905, name: 'Elena', email: '', phone: '', company: 'Épsilon', is_email_placeholder: true },
        ],
      });
      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();

      expect(wrapper.get('[data-testid="client-autocomplete-option-905"]').text())
        .toContain('Sin correo');
    });

    it('offers client creation inside an empty catalog', async () => {
      mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });
      const wrapper = mountAutocomplete({ modelValue: null, presentation: 'catalog' });
      await flushPromises();

      expect(wrapper.text()).toContain('No hay clientes registrados.');
      await wrapper.get('[data-testid="client-autocomplete-create-new"]').trigger('click');

      expect(wrapper.emitted('create-new')).toEqual([['']]);
      expect(wrapper.get('[data-testid="client-catalog"]').isVisible()).toBe(true);
    });
  });

  it('searches when the user types and renders matching options', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 301, name: 'Sandra Gomez', email: 'sandra@example.com', phone: '', company: 'Sandra SAS', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('san');
    await flushPromises();

    expect(mockStore.searchClients).toHaveBeenCalledWith('san', { offset: 0, limit: 20 });
    expect(wrapper.get('[data-testid="client-autocomplete-option-301"]').text()).toContain('Sandra Gomez');
  });

  it('emits the selected client when an option is clicked', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 401, name: 'Ana Ruiz', email: 'ana@example.com', phone: '+57 300', company: 'AnaCo', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('ana');
    await flushPromises();
    await wrapper.get('[data-testid="client-autocomplete-option-401"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[401]]);
    expect(wrapper.emitted('select')).toEqual([[
      expect.objectContaining({ id: 401, name: 'Ana Ruiz' }),
    ]]);
  });

  it('shows the create-new action when the search returns no results', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('Nombre Nuevo');
    await flushPromises();

    expect(wrapper.get('[data-testid="client-autocomplete-create-new"]').text()).toContain('Nombre Nuevo');

    await wrapper.get('[data-testid="client-autocomplete-create-new"]').trigger('click');

    expect(wrapper.emitted('create-new')).toEqual([['Nombre Nuevo']]);
  });

  it('warns before selection when a client has no real email', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 501, name: 'Cliente Temporal', email: 'cliente_501@temp.example.com', phone: '', company: '', is_email_placeholder: true },
      ],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('cliente');
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain('Sin correo');
    expect(wrapper.text()).toContain('Correo pendiente');
    expect(wrapper.text()).toContain('habrá que agregarlo para enviar');
  });

  it('selects the highlighted option when enter is pressed', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 601, name: 'Carlos Uno', email: 'uno@example.com', phone: '', company: '', is_email_placeholder: false },
        { id: 602, name: 'Carlos Dos', email: 'dos@example.com', phone: '', company: '', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete();

    const input = wrapper.get('[data-testid="client-autocomplete-input"]');
    await input.setValue('carlos');
    await flushPromises();
    await input.trigger('keydown.down');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('update:modelValue')).toEqual([[602]]);
    expect(wrapper.emitted('select')).toEqual([[
      expect.objectContaining({ id: 602, name: 'Carlos Dos' }),
    ]]);
  });

  // Escribir es buscar, no desvincular: desvincular tiene su propio botón (la X).
  // Antes un solo caracter soltaba el id, y el form quedaba sucio —y al guardar
  // desvinculaba al cliente— por un cambio que nadie pidió.
  it('keeps the committed client while typing and restores its name when the dropdown closes', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [],
    });

    const wrapper = mountAutocomplete({ modelValue: 42, initialLabel: 'Cliente Actual' });

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('nuevo');
    await flushPromises();

    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    // El hint sigue nombrando al cliente enlazado, no lo que se está tecleando.
    expect(wrapper.get('[data-testid="client-autocomplete-linked"]').text()).toContain('Cliente Actual');

    clickOutside();
    await nextTick();

    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('Cliente Actual');
  });

  it('commits the new client when one is picked after typing over another', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 77, name: 'Otro Cliente', email: 'otro@example.com', phone: '', company: '', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete({ modelValue: 42, initialLabel: 'Cliente Actual' });

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('otro');
    await flushPromises();
    await wrapper.get('[data-testid="client-autocomplete-option-77"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[77]]);
    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('Otro Cliente');
  });

  it('leaves the typed text alone when closing without any committed client', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });

    const wrapper = mountAutocomplete({ modelValue: null });

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('algo');
    await flushPromises();
    clickOutside();
    await nextTick();

    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('algo');
  });

  // El texto tecleado ES el nombre del cliente nuevo: restaurarlo acá borraría
  // lo que el padre necesita para prellenar el formulario de creación.
  it('keeps the typed name when create-new is chosen over a committed client', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });

    const wrapper = mountAutocomplete({ modelValue: 42, initialLabel: 'Cliente Actual' });

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('Cliente Nuevo');
    await flushPromises();
    await wrapper.get('[data-testid="client-autocomplete-create-new"]').trigger('click');

    expect(wrapper.emitted('create-new')).toEqual([['Cliente Nuevo']]);
    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('Cliente Nuevo');
  });

  it('loads the initial client list on focus', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 901, name: 'Amanda', email: 'amanda@example.com', phone: '', company: 'Alfa', is_email_placeholder: false },
      ],
    });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();

    expect(mockStore.searchClients).toHaveBeenCalledWith('', { offset: 0, limit: 20 });
    expect(wrapper.get('[data-testid="client-autocomplete-option-901"]').text()).toContain('Amanda');
  });

  it('offers client creation when the initial catalog is empty', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();

    expect(wrapper.text()).toContain('No hay clientes registrados.');
    expect(wrapper.get('[data-testid="client-autocomplete-create-new"]').text())
      .toContain('Crear un cliente');
  });

  it('ignores cancelled search results without opening options', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ cancelled: true });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();

    expect(wrapper.find('[role="option"]').exists()).toBe(false);
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false);
  });

  it('shows a retry action when the search response is unsuccessful', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: false });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('fallo');
    await flushPromises();

    expect(wrapper.find('[role="option"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="client-autocomplete-error"]').text())
      .toContain('No se pudo cargar la lista de clientes.');
    expect(wrapper.find('[data-testid="client-autocomplete-retry"]').exists()).toBe(true);
  });

  it('loads the next result page near the list end', async () => {
    mockStore.searchClients
      .mockResolvedValueOnce({
        success: true,
        data: [
          { id: 910, name: 'Amanda', email: 'amanda@example.com', phone: '', company: 'Alfa', is_email_placeholder: false },
        ],
        hasMore: true,
        nextOffset: 1,
      })
      .mockResolvedValueOnce({
        success: true,
        data: [
          { id: 911, name: 'Beatriz', email: 'beatriz@example.com', phone: '', company: 'Beta', is_email_placeholder: false },
        ],
        hasMore: false,
        nextOffset: 2,
      });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();
    const listbox = wrapper.get('[role="listbox"]');
    Object.defineProperty(listbox.element, 'scrollHeight', { configurable: true, value: 400 });
    Object.defineProperty(listbox.element, 'clientHeight', { configurable: true, value: 320 });
    Object.defineProperty(listbox.element, 'scrollTop', { configurable: true, value: 80 });
    await listbox.trigger('scroll');
    await flushPromises();

    expect(mockStore.searchClients).toHaveBeenNthCalledWith(2, '', { offset: 1, limit: 20 });
    expect(wrapper.find('[data-testid="client-autocomplete-option-911"]').exists()).toBe(true);
  });

  it('falls back to an empty result list when a successful search omits data', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('sin-data');
    await flushPromises();

    expect(wrapper.find('[role="option"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('No se encontraron clientes con "sin-data".');
  });

  it('skips the focus search when a committed selection already exists', async () => {
    const wrapper = mountAutocomplete({ modelValue: 7, initialLabel: 'Cliente fijo' });

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();

    expect(mockStore.searchClients).not.toHaveBeenCalled();
  });

  it('clears the selection state and focuses the input when the clear button is clicked', async () => {
    const focusSpy = jest.spyOn(HTMLInputElement.prototype, 'focus').mockImplementation(() => {});
    const wrapper = mountAutocomplete({ modelValue: 9, initialLabel: 'Cliente X' });

    await wrapper.get('button[aria-label="clients.autocomplete.clear"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[null]]);
    expect(wrapper.emitted('select')).toEqual([[null]]);
    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('');
    expect(focusSpy).toHaveBeenCalled();

    focusSpy.mockRestore();
  });

  it('opens the dropdown when ArrowDown is pressed while it is closed', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });
    const wrapper = mountAutocomplete();
    const input = wrapper.get('[data-testid="client-autocomplete-input"]');

    await input.trigger('keydown.down');
    await flushPromises();

    expect(wrapper.find('[role="listbox"]').exists()).toBe(true);
  });

  it('moves the highlight upward when ArrowUp is pressed with open results', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 701, name: 'Primero', email: 'uno@example.com', phone: '', company: '', is_email_placeholder: false },
        { id: 702, name: 'Segundo', email: 'dos@example.com', phone: '', company: '', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete();
    const input = wrapper.get('[data-testid="client-autocomplete-input"]');

    await input.setValue('seg');
    await flushPromises();
    await input.trigger('keydown.up');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('update:modelValue')).toEqual([[702]]);
    expect(wrapper.emitted('select')).toEqual([[
      expect.objectContaining({ id: 702, name: 'Segundo' }),
    ]]);
  });

  it('does nothing on ArrowDown when the dropdown is open without results', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [],
    });

    const wrapper = mountAutocomplete();
    const input = wrapper.get('[data-testid="client-autocomplete-input"]');

    await input.setValue('vacio');
    await flushPromises();
    await input.trigger('keydown.down');

    expect(wrapper.emitted('select')).toBeUndefined();
    expect(wrapper.find('[role="listbox"]').exists()).toBe(true);
  });

  it('does nothing on ArrowUp when the dropdown is closed', async () => {
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('keydown.up');

    expect(wrapper.find('[role="listbox"]').exists()).toBe(false);
  });

  it('emits create-new when enter is pressed after an empty search result', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [],
    });

    const wrapper = mountAutocomplete();
    const input = wrapper.get('[data-testid="client-autocomplete-input"]');

    await input.setValue('Cliente Nuevo');
    await flushPromises();
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('create-new')).toEqual([['Cliente Nuevo']]);
  });

  it('does nothing on Enter when the dropdown is closed', async () => {
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('keydown.enter');

    expect(wrapper.emitted('select')).toBeUndefined();
    expect(wrapper.emitted('create-new')).toBeUndefined();
  });

  it('syncs a later initialLabel into the empty input', async () => {
    const wrapper = mountAutocomplete({ modelValue: null, initialLabel: '' });

    await wrapper.setProps({ initialLabel: 'Cliente Precargado' });
    await nextTick();

    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('Cliente Precargado');
  });

  // La página real hidrata DESPUÉS del montaje: el documento se pide por red,
  // así que el picker nace con `initialLabel` vacío y la etiqueta llega luego.
  // Los demás tests montan con la etiqueta ya puesta, que inicializa
  // `committedLabel` por constructor y nunca ejerce el watcher — por eso este
  // camino podía romperse sin que ninguno se enterara.
  it('adopts a late initialLabel as the committed one, so blur restores it', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });

    const wrapper = mountAutocomplete({ modelValue: null, initialLabel: '' });
    await wrapper.setProps({ modelValue: 7, initialLabel: 'Kore SAS' });
    await nextTick();

    // El hint nombra al cliente enlazado: si `committedLabel` quedó vacío,
    // acá se lee "Cliente enlazado: (#7)" sin nombre.
    expect(wrapper.get('[data-testid="client-autocomplete-linked"]').text()).toContain('Kore SAS');

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('otra');
    await flushPromises();
    clickOutside();
    await nextTick();

    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value).toBe('Kore SAS');
  });

  it('renders the client id beside the name in each option', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 802, name: 'María García', email: 'maria@example.com', phone: '', company: 'Acme', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('mar');
    await flushPromises();

    expect(wrapper.get('[data-testid="client-autocomplete-option-802"]').text()).toContain('(#802)');
  });

  it('shows the linked-client hint with the id when a client is selected', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [
        { id: 803, name: 'Pedro Páez', email: 'pedro@example.com', phone: '', company: '', is_email_placeholder: false },
      ],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('ped');
    await flushPromises();
    expect(wrapper.find('[data-testid="client-autocomplete-linked"]').exists()).toBe(false);

    await wrapper.get('[data-testid="client-autocomplete-option-803"]').trigger('click');
    // Mirror the v-model round-trip the parent would perform.
    await wrapper.setProps({ modelValue: wrapper.emitted('update:modelValue').at(-1)[0] });
    await nextTick();

    const hint = wrapper.get('[data-testid="client-autocomplete-linked"]');
    expect(hint.text()).toContain('Pedro Páez');
    expect(hint.text()).toContain('(#803)');
  });

  it('shows the linked-client hint for a pre-selected client', () => {
    const wrapper = mountAutocomplete({ modelValue: 55, initialLabel: 'Cliente Precargado' });

    const hint = wrapper.get('[data-testid="client-autocomplete-linked"]');
    expect(hint.text()).toContain('Cliente Precargado');
    expect(hint.text()).toContain('(#55)');
  });

  // El hint suma alto al picker. Dentro de una fila flex eso arrastra al input
  // fuera de línea con lo que tenga al lado, así que los layouts de barra lo
  // apagan y dibujan esa confirmación en su propia línea de estado.
  it('hides the linked-client hint when the parent draws its own', () => {
    const wrapper = mountAutocomplete({
      modelValue: 55,
      initialLabel: 'Cliente Precargado',
      showLinkedHint: false,
    });

    // El cliente sigue seleccionado y el input lo sigue mostrando: lo único
    // que desaparece es el renglón que hacía crecer al picker.
    expect(wrapper.get('[data-testid="client-autocomplete-input"]').element.value)
      .toBe('Cliente Precargado');
    expect(wrapper.find('[data-testid="client-autocomplete-linked"]').exists()).toBe(false);
  });

  it('closes the dropdown when a pointer press happens outside', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [{ id: 1, name: 'Cliente', email: 'cliente@example.com', phone: '', company: '', is_email_placeholder: false }],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('cli');
    await flushPromises();
    expect(wrapper.find('[role="listbox"]').exists()).toBe(true);

    clickOutside();
    await nextTick();

    expect(wrapper.find('[role="listbox"]').exists()).toBe(false);
  });

  describe('external label sync', () => {
    it('adopts a label that arrives after mount', async () => {
      const wrapper = mountAutocomplete({ modelValue: null, initialLabel: '' });

      await wrapper.setProps({ modelValue: 7, initialLabel: 'Kore SAS' });

      expect(wrapper.find('input').element.value).toBe('Kore SAS');
    });

    it('clears the box when the parent retracts both the value and the label', async () => {
      // Retirar una sugerencia (o resetear el form) dejaba el nombre anterior
      // escrito mientras el valor ya era null: el input decía tener cliente y
      // no lo tenía.
      const wrapper = mountAutocomplete({ modelValue: 7, initialLabel: 'Kore SAS' });

      await wrapper.setProps({ modelValue: null, initialLabel: '' });

      expect(wrapper.find('input').element.value).toBe('');
    });

    it('leaves what the user typed alone', async () => {
      mockStore.searchClients.mockResolvedValue({ cancelled: false, data: [] });
      const wrapper = mountAutocomplete({ modelValue: null, initialLabel: '' });
      await wrapper.find('input').setValue('Ana escribiendo');

      await wrapper.setProps({ initialLabel: 'Kore SAS' });

      expect(wrapper.find('input').element.value).toBe('Ana escribiendo');
    });
  });
});

import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import ClientAutocomplete from '../../components/ui/ClientAutocomplete.vue';

const mockStore = {
  searchClients: jest.fn(),
};

let clickOutsideHandler = null;

jest.mock('../../stores/proposalClients', () => ({
  useProposalClientsStore: () => mockStore,
}));

jest.mock('@vueuse/core', () => ({
  useDebounceFn: (fn) => fn,
  onClickOutside: jest.fn((_, handler) => {
    clickOutsideHandler = handler;
  }),
}));

function mountAutocomplete(props = { modelValue: null }) {
  return mount(ClientAutocomplete, {
    props,
    global: {
      mocks: {
        $t: (key) => key,
      },
    },
  });
}

describe('ClientAutocomplete', () => {
  beforeEach(() => {
    mockStore.searchClients.mockReset();
    clickOutsideHandler = null;
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

    expect(mockStore.searchClients).toHaveBeenCalledWith('san');
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

  it('renders the placeholder badge for clients without a real email', async () => {
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

    expect(wrapper.text()).toContain('placeholder');
    expect(wrapper.text()).toContain('Email pendiente');
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

  it('clears the committed selection when typing over an existing client', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [],
    });

    const wrapper = mountAutocomplete({ modelValue: 42, initialLabel: 'Cliente Actual' });

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('nuevo');
    await flushPromises();

    expect(wrapper.emitted('update:modelValue')).toEqual([[null]]);
  });

  it('searches on focus only when there is no committed selection', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: true, data: [] });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();

    expect(mockStore.searchClients).toHaveBeenCalledWith('');
  });

  it('ignores cancelled search results without opening options', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ cancelled: true });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').trigger('focus');
    await flushPromises();

    expect(wrapper.find('[role="option"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('Escribe al menos 1 caracter para buscar');
  });

  it('shows no options when the search response is unsuccessful', async () => {
    mockStore.searchClients.mockResolvedValueOnce({ success: false });
    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('fallo');
    await flushPromises();

    expect(wrapper.find('[role="option"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('No se encontraron clientes con "fallo".');
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
    const wrapper = mountAutocomplete();
    const input = wrapper.get('[data-testid="client-autocomplete-input"]');

    await input.trigger('keydown.down');

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

  it('closes the dropdown when the click-outside handler runs', async () => {
    mockStore.searchClients.mockResolvedValueOnce({
      success: true,
      data: [{ id: 1, name: 'Cliente', email: 'cliente@example.com', phone: '', company: '', is_email_placeholder: false }],
    });

    const wrapper = mountAutocomplete();

    await wrapper.get('[data-testid="client-autocomplete-input"]').setValue('cli');
    await flushPromises();
    expect(wrapper.find('[role="listbox"]').exists()).toBe(true);

    clickOutsideHandler();
    await nextTick();

    expect(wrapper.find('[role="listbox"]').exists()).toBe(false);
  });
});

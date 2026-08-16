/**
 * Tests for FolderChangeClientModal.vue.
 *
 * El camino guiado para cambiarle el cliente a una carpeta CON contenido: se
 * lee a qué afecta antes de confirmar, el modo se elige SIEMPRE (no hay
 * preselección) y un 409 no se traga — el plan se recarga.
 */

const mockFolderStore = {
  previewChangeClient: jest.fn(),
  changeClient: jest.fn(),
  isUpdating: false,
};

const mockNotify = { success: jest.fn(), error: jest.fn() };

global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

jest.mock('../../composables/usePanelNotify', () => ({
  usePanelNotify: () => mockNotify,
}));

import { mount, flushPromises } from '@vue/test-utils';
import FolderChangeClientModal from '../../components/panel/documents/FolderChangeClientModal.vue';
import BaseModal from '../../components/base/BaseModal.vue';
import BaseButton from '../../components/base/BaseButton.vue';
import BaseAlert from '../../components/base/BaseAlert.vue';
import BaseSegmented from '../../components/base/BaseSegmented.vue';

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'initialLabel'],
  emits: ['update:modelValue', 'select'],
  template: '<div class="client-autocomplete-stub" />',
};

const folder = { id: 5, name: 'Kore', client: 7, client_display_name: 'Kore SAS' };

const previewPayload = {
  folder: { id: 5, name: 'Kore' },
  current_client: { profile_id: 7, name: 'Kore SAS' },
  new_client: { profile_id: 9, name: 'Ana Pérez' },
  folders_move: [{ id: 6, name: 'Diseño' }],
  folders_foreign: [],
  documents_move: [{ id: 1, title: 'Contrato' }, { id: 2, title: 'Acta' }],
  documents_blocked: [{ id: 3, title: 'CC-014', reason: 'Ya emitida' }],
  documents_foreign: [{ id: 4, title: 'De Néstor', reason: 'Es de otro cliente' }],
  folder_ids: [6],
  document_ids: [1, 2],
  totals: {
    folders: 1, documents: 2, blocked: 1, foreign: 1, foreign_folders: 0,
  },
};

function mountModal(props = {}) {
  return mount(FolderChangeClientModal, {
    props: { open: true, folder, ...props },
    global: {
      components: { BaseModal, BaseButton, BaseAlert, BaseSegmented },
      stubs: { Teleport: true, Transition: false, ClientAutocomplete: ClientAutocompleteStub },
    },
  });
}

const clientField = (w) => w.findComponent(ClientAutocompleteStub);
const confirmBtn = (w) => w.find('[data-testid="folder-change-client-confirm"]');

async function pickClient(wrapper, id = 9) {
  clientField(wrapper).vm.$emit('update:modelValue', id);
  clientField(wrapper).vm.$emit('select', { id, name: 'Ana Pérez' });
  await flushPromises();
}

async function pickMode(wrapper, value) {
  wrapper.findComponent(BaseSegmented).vm.$emit('update:modelValue', value);
  await flushPromises();
}

describe('FolderChangeClientModal', () => {
  beforeEach(() => {
    mockFolderStore.previewChangeClient.mockReset()
      .mockResolvedValue({ success: true, data: previewPayload });
    mockFolderStore.changeClient.mockReset()
      .mockResolvedValue({
        success: true,
        data: { moved: { folders: 1, documents: 2 }, skipped: { blocked: 1, foreign: 1 } },
      });
    mockNotify.success.mockReset();
  });

  it('asks for the impact as soon as a destination is picked', async () => {
    const wrapper = mountModal();

    await pickClient(wrapper);

    expect(mockFolderStore.previewChangeClient).toHaveBeenCalledWith(5, 9);
  });

  it('names what moves, what is blocked and what belongs to someone else', async () => {
    const wrapper = mountModal();
    await pickClient(wrapper);

    const preview = wrapper.find('[data-testid="folder-change-client-preview"]');
    expect(preview.text()).toContain('Contrato');
    expect(wrapper.find('[data-testid="folder-change-client-blocked"]').text())
      .toContain('CC-014');
    expect(wrapper.find('[data-testid="folder-change-client-foreign"]').text())
      .toContain('De Néstor');
  });

  it('keeps confirm disabled until a mode is chosen — there is no default', async () => {
    const wrapper = mountModal();
    await pickClient(wrapper);

    expect(confirmBtn(wrapper).element.disabled).toBe(true);

    await pickMode(wrapper, 'propagate');

    expect(confirmBtn(wrapper).element.disabled).toBe(false);
  });

  it('sends the plan it showed as the staleness token', async () => {
    const wrapper = mountModal();
    await pickClient(wrapper);
    await pickMode(wrapper, 'propagate');

    await confirmBtn(wrapper).trigger('click');
    await flushPromises();

    expect(mockFolderStore.changeClient).toHaveBeenCalledWith(5, {
      client_profile_id: 9,
      mode: 'propagate',
      document_ids: [1, 2],
      folder_ids: [6],
    });
    expect(wrapper.emitted('changed')).toBeTruthy();
  });

  it('reloads the plan instead of guessing when it went stale', async () => {
    mockFolderStore.changeClient.mockResolvedValue({
      success: false, code: 'records_changed', message: 'cambió',
    });
    const wrapper = mountModal();
    await pickClient(wrapper);
    await pickMode(wrapper, 'propagate');
    mockFolderStore.previewChangeClient.mockClear();

    await confirmBtn(wrapper).trigger('click');
    await flushPromises();

    expect(mockFolderStore.previewChangeClient).toHaveBeenCalledTimes(1);
    // Y el modo vuelve a pedirse: el plan que se aceptó ya no es este.
    expect(confirmBtn(wrapper).element.disabled).toBe(true);
    expect(wrapper.emitted('changed')).toBeFalsy();
  });

  it('starts from the client the form was already proposing', async () => {
    const wrapper = mountModal({ initialClientProfileId: 9 });
    await flushPromises();

    expect(mockFolderStore.previewChangeClient).toHaveBeenCalledWith(5, 9);
  });
});

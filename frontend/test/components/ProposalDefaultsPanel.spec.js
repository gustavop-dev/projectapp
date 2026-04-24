/**
 * Tests for ProposalDefaultsPanel.vue.
 *
 * Covers: rendering, slug preview, handleSaveGeneral success/error,
 * loadDefaults on mount, section loading, toggleSection,
 * switchLanguage, handleReset/confirmReset, email template loading,
 * selectEmailTemplate, JSON tab save/error,
 * handleApplyDefaultsTechnicalJson error.
 */

// ESM/UMD packages in the deep component chain that Jest can't parse directly
jest.mock('marked', () => ({ marked: jest.fn((t) => t) }));
jest.mock('dompurify', () => ({ default: { sanitize: jest.fn((t) => t) } }));
jest.mock('vue3-emoji-picker', () => ({ default: { name: 'EmojiPicker', template: '<div />' } }));

const mockProposalStore = {
  fetchProposalDefaults: jest.fn(),
  saveProposalDefaults: jest.fn(),
  resetProposalDefaults: jest.fn(),
  fetchEmailTemplates: jest.fn(),
  fetchEmailTemplateDetail: jest.fn(),
  saveEmailTemplate: jest.fn(),
  resetEmailTemplate: jest.fn(),
  previewEmailTemplate: jest.fn(),
};

// Nuxt auto-imports — must be set before the component is required
global.useProposalStore = jest.fn(() => mockProposalStore);
global.useRoute = () => ({ query: {} });

let capturedConfirmOpts = null;
const mockConfirmModal = {
  confirmState: { open: false, title: '', message: '', confirmText: '', cancelText: '', variant: '' },
  requestConfirm: jest.fn((opts) => { capturedConfirmOpts = opts; }),
  handleConfirmed: jest.fn(),
  handleCancelled: jest.fn(),
};

jest.mock('../../composables/useConfirmModal', () => ({
  useConfirmModal: () => mockConfirmModal,
}));

jest.mock('../../composables/useSellerPrompt', () => {
  const { ref } = require('vue');
  return {
    useSellerPrompt: () => ({
      promptText: ref(''),
      isEditing: ref(false),
      DEFAULT_PROMPT: '',
      loadSavedPrompt: jest.fn(),
      savePrompt: jest.fn(),
      resetPrompt: jest.fn(),
      copyPrompt: jest.fn().mockResolvedValue(undefined),
      downloadPrompt: jest.fn(),
    }),
  };
});

jest.mock('../../composables/useTechnicalPrompt', () => {
  const { ref } = require('vue');
  return {
    useTechnicalPrompt: () => ({
      promptText: ref(''),
      isEditing: ref(false),
      DEFAULT_PROMPT: '',
      loadSavedPrompt: jest.fn(),
      savePrompt: jest.fn(),
      resetPrompt: jest.fn(),
      copyPrompt: jest.fn().mockResolvedValue(undefined),
      downloadPrompt: jest.fn(),
    }),
  };
});

import { mount } from '@vue/test-utils';
import ProposalDefaultsPanel from '../../components/panel/defaults/ProposalDefaultsPanel.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}

const defaultDataResponse = {
  success: true,
  data: {
    default_currency: 'COP',
    default_total_investment: 0,
    hosting_percent: 30,
    hosting_discount_semiannual: 20,
    hosting_discount_quarterly: 10,
    expiration_days: 21,
    reminder_days: 3,
    urgency_reminder_days: 7,
    default_discount_percent: 0,
    default_slug_pattern: '{client_name}',
    sections_json: [],
    updated_at: null,
  },
};

function mountPanel(tabOverride = 'general') {
  global.useRoute = () => ({ query: { tab: tabOverride } });
  return mount(ProposalDefaultsPanel, {
    global: {
      stubs: {
        ResponsiveTabs: { template: '<div />' },
        ConfirmModal: { template: '<div />' },
        SectionEditor: { template: '<div data-testid="section-editor" />' },
        TechnicalDocumentEditor: { template: '<div data-testid="technical-editor" />' },
        SectionPreviewModal: { template: '<div />' },
        PromptSubTabsPanel: { template: '<div><slot name="commercial" /><slot name="technical" /></div>' },
        TabSplitLayout: { template: '<div><slot name="main" /><slot name="aside" /></div>' },
        UiTooltip: { template: '<div><slot /></div>' },
        NuxtLink: { template: '<a><slot /></a>' },
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ProposalDefaultsPanel', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    capturedConfirmOpts = null;
    mockProposalStore.fetchProposalDefaults.mockReset().mockResolvedValue(defaultDataResponse);
    mockProposalStore.saveProposalDefaults.mockReset().mockResolvedValue({ success: true, data: {} });
    mockProposalStore.resetProposalDefaults.mockReset().mockResolvedValue({ success: true });
    mockProposalStore.fetchEmailTemplates.mockReset().mockResolvedValue({ success: true, data: [] });
    mockProposalStore.fetchEmailTemplateDetail.mockReset().mockResolvedValue({
      success: true,
      data: { editable_fields: [], is_active: true },
    });
    mockProposalStore.saveEmailTemplate.mockReset().mockResolvedValue({ success: true });
    mockProposalStore.resetEmailTemplate.mockReset().mockResolvedValue({ success: true });
    mockProposalStore.previewEmailTemplate.mockReset().mockResolvedValue({ success: false });
    mockConfirmModal.requestConfirm.mockClear();
    global.navigator = { clipboard: { writeText: jest.fn().mockResolvedValue(undefined) } };
    global.URL = { createObjectURL: jest.fn().mockReturnValue('blob://mock'), revokeObjectURL: jest.fn() };
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  describe('rendering', () => {
    it('renders the panel intro text', async () => {
      const wrapper = mountPanel();
      await flushPromises();

      expect(wrapper.text()).toContain('Configura los valores iniciales');
    });

    it('renders the slug pattern input', async () => {
      const wrapper = mountPanel();
      await flushPromises();

      expect(wrapper.find('[data-testid="defaults-slug-pattern"]').exists()).toBe(true);
    });

    it('shows maria-lopez in the slug preview for the default {client_name} pattern', async () => {
      const wrapper = mountPanel();
      await flushPromises();

      expect(wrapper.text()).toContain('maria-lopez');
    });
  });

  // ── handleSaveGeneral ─────────────────────────────────────────────────────

  describe('handleSaveGeneral', () => {
    it('calls saveProposalDefaults when the general form is submitted', async () => {
      const wrapper = mountPanel();
      await flushPromises();

      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(mockProposalStore.saveProposalDefaults).toHaveBeenCalled();
    });

    it('shows success feedback after saving general defaults', async () => {
      const wrapper = mountPanel();
      await flushPromises();

      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(wrapper.text()).toContain('Valores generales guardados correctamente.');
    });

    it('shows error feedback when save fails', async () => {
      mockProposalStore.saveProposalDefaults.mockResolvedValue({ success: false });
      const wrapper = mountPanel();
      await flushPromises();

      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(wrapper.text()).toContain('Error al guardar los valores generales.');
    });
  });

  // ── loadDefaults ──────────────────────────────────────────────────────────

  describe('loadDefaults', () => {
    it('calls fetchProposalDefaults with es on mount', async () => {
      mountPanel();
      await flushPromises();

      expect(mockProposalStore.fetchProposalDefaults).toHaveBeenCalledWith('es');
    });

    it('applies the returned currency to the form selects', async () => {
      mockProposalStore.fetchProposalDefaults.mockResolvedValue({
        ...defaultDataResponse,
        data: { ...defaultDataResponse.data, default_currency: 'USD' },
      });
      const wrapper = mountPanel();
      await flushPromises();
      await wrapper.vm.$nextTick();

      const currencySelect = wrapper.findAll('select').at(1);
      expect(currencySelect.element.value).toBe('USD');
    });

    it('renders section titles after defaults are loaded', async () => {
      mockProposalStore.fetchProposalDefaults.mockResolvedValue({
        success: true,
        data: {
          ...defaultDataResponse.data,
          sections_json: [
            { section_type: 'intro', title: 'Introducción al proyecto', order: 0, content_json: {} },
          ],
        },
      });
      const wrapper = mountPanel('sections');
      await flushPromises();

      expect(wrapper.text()).toContain('Introducción al proyecto');
    });
  });

  // ── switchLanguage ────────────────────────────────────────────────────────

  describe('switchLanguage', () => {
    it('calls loadDefaults with en when the English button is clicked without pending changes', async () => {
      const wrapper = mountPanel('sections');
      await flushPromises();
      mockProposalStore.fetchProposalDefaults.mockClear();

      await wrapper.findAll('button').find((btn) => btn.text() === 'English').trigger('click');
      await flushPromises();

      expect(mockProposalStore.fetchProposalDefaults).toHaveBeenCalledWith('en');
    });
  });

  // ── toggleSection ─────────────────────────────────────────────────────────

  describe('toggleSection', () => {
    it('shows the section editor when a section row header is clicked', async () => {
      mockProposalStore.fetchProposalDefaults.mockResolvedValue({
        success: true,
        data: {
          ...defaultDataResponse.data,
          sections_json: [
            { section_type: 'intro', title: 'Introducción', order: 0, content_json: {} },
          ],
        },
      });
      const wrapper = mountPanel('sections');
      await flushPromises();

      await wrapper.find('div.cursor-pointer').trigger('click');
      await wrapper.vm.$nextTick();

      expect(wrapper.find('[data-testid="section-editor"]').exists()).toBe(true);
    });
  });

  // ── handleReset / confirmReset ────────────────────────────────────────────

  describe('handleReset', () => {
    it('shows the reset confirmation when Restaurar valores originales is clicked', async () => {
      mockProposalStore.fetchProposalDefaults.mockResolvedValue({
        success: true,
        data: {
          ...defaultDataResponse.data,
          sections_json: [{ section_type: 'intro', title: 'Intro', order: 0, content_json: {} }],
        },
      });
      const wrapper = mountPanel('sections');
      await flushPromises();

      await wrapper.findAll('button').find((btn) => btn.text().includes('Restaurar valores originales')).trigger('click');

      expect(wrapper.text()).toContain('¿Restaurar valores originales?');
    });
  });

  describe('confirmReset', () => {
    it('calls resetProposalDefaults when the reset is confirmed', async () => {
      mockProposalStore.fetchProposalDefaults.mockResolvedValue({
        success: true,
        data: {
          ...defaultDataResponse.data,
          sections_json: [{ section_type: 'intro', title: 'Intro', order: 0, content_json: {} }],
        },
      });
      const wrapper = mountPanel('sections');
      await flushPromises();

      await wrapper.findAll('button').find((btn) => btn.text().includes('Restaurar valores originales')).trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text().includes('Sí, restaurar')).trigger('click');
      await flushPromises();

      expect(mockProposalStore.resetProposalDefaults).toHaveBeenCalledWith('es');
    });
  });

  // ── Email templates ───────────────────────────────────────────────────────

  describe('email templates', () => {
    it('calls fetchEmailTemplates on mount', async () => {
      mountPanel();
      await flushPromises();

      expect(mockProposalStore.fetchEmailTemplates).toHaveBeenCalled();
    });

    it('renders email template names from the loaded list', async () => {
      mockProposalStore.fetchEmailTemplates.mockResolvedValue({
        success: true,
        data: [
          { template_key: 'tpl-1', name: 'Correo de seguimiento', category: 'client', description: '', editable_fields_count: 2, is_customized: false, is_active: true },
        ],
      });
      const wrapper = mountPanel('emails');
      await flushPromises();

      expect(wrapper.text()).toContain('Correo de seguimiento');
    });

    it('calls fetchEmailTemplateDetail when a template is selected', async () => {
      mockProposalStore.fetchEmailTemplates.mockResolvedValue({
        success: true,
        data: [
          { template_key: 'tpl-1', name: 'Template 1', category: 'client', description: '', editable_fields_count: 0, is_customized: false, is_active: true },
        ],
      });
      const wrapper = mountPanel('emails');
      await flushPromises();

      await wrapper.findAll('button').find((btn) => btn.text().includes('Template 1')).trigger('click');
      await flushPromises();

      expect(mockProposalStore.fetchEmailTemplateDetail).toHaveBeenCalledWith('tpl-1');
    });
  });

  // ── JSON tab ──────────────────────────────────────────────────────────────

  describe('JSON tab', () => {
    it('shows an error message when saveEditJson receives invalid JSON', async () => {
      const wrapper = mountPanel('json');
      await flushPromises();

      // There are 3 "Editar" buttons (prompt×2, json×1); the JSON tab's is last
      const editarButtons = wrapper.findAll('button').filter((btn) => btn.text() === 'Editar');
      await editarButtons[editarButtons.length - 1].trigger('click');
      await wrapper.vm.$nextTick();

      // JSON edit textarea is conditionally rendered (v-else-if); it's the last font-mono textarea
      const jsonTextarea = wrapper.findAll('textarea.font-mono').at(-1);
      await jsonTextarea.setValue('{ invalid json }');
      await wrapper.findAll('button').find((btn) => btn.text().includes('Guardar cambios')).trigger('click');
      await flushPromises();

      expect(wrapper.text()).toContain('JSON inválido');
    });

    it('calls saveProposalDefaults when valid JSON with sections is saved', async () => {
      const wrapper = mountPanel('json');
      await flushPromises();

      const editarButtons = wrapper.findAll('button').filter((btn) => btn.text() === 'Editar');
      await editarButtons[editarButtons.length - 1].trigger('click');
      await wrapper.vm.$nextTick();

      const validJson = JSON.stringify({
        language: 'es',
        sections: [{ section_type: 'intro', title: 'Intro', order: 0, content_json: {} }],
      });
      const jsonTextarea = wrapper.findAll('textarea.font-mono').at(-1);
      await jsonTextarea.setValue(validJson);
      await wrapper.findAll('button').find((btn) => btn.text().includes('Guardar cambios')).trigger('click');
      await flushPromises();

      expect(mockProposalStore.saveProposalDefaults).toHaveBeenCalled();
    });
  });

  // ── handleApplyDefaultsTechnicalJson ─────────────────────────────────────

  describe('handleApplyDefaultsTechnicalJson', () => {
    it('shows JSON error when the technical JSON textarea contains invalid JSON', async () => {
      mockProposalStore.fetchProposalDefaults.mockResolvedValue({
        success: true,
        data: {
          ...defaultDataResponse.data,
          sections_json: [
            { section_type: 'technical_document', title: 'Det. técnico', order: 0, content_json: { epics: [] } },
          ],
        },
      });
      const wrapper = mountPanel('technical');
      await flushPromises();

      await wrapper.findAll('button').find((btn) => btn.text() === 'JSON').trigger('click');
      await wrapper.vm.$nextTick();

      const technicalJsonTextarea = wrapper.find('textarea[rows="24"]');
      await technicalJsonTextarea.setValue('not valid json {');
      await wrapper.findAll('button').find((btn) => btn.text().includes('Aplicar a plantilla')).trigger('click');

      expect(wrapper.text()).toContain('JSON inválido');
    });
  });

  // ── Language switch ───────────────────────────────────────────────────────

  describe('language switch', () => {
    it('calls fetchProposalDefaults with en when the English button is clicked', async () => {
      const wrapper = mountPanel('general');
      await flushPromises();

      mockProposalStore.fetchProposalDefaults.mockResolvedValueOnce(defaultDataResponse);
      const enBtn = wrapper.findAll('button').find(b => b.text() === 'English');
      await enBtn.trigger('click');
      await flushPromises();

      expect(mockProposalStore.fetchProposalDefaults).toHaveBeenCalledWith('en');
    });

    it('calls requestConfirm when switching language with unsaved section changes', async () => {
      const wrapper = mountPanel('general');
      await flushPromises();

      // Manually mark a section as unsaved via internal state
      wrapper.vm.savedSections.add(0);
      await wrapper.vm.$nextTick();

      const enBtn = wrapper.findAll('button').find(b => b.text() === 'English');
      await enBtn.trigger('click');

      expect(mockConfirmModal.requestConfirm).toHaveBeenCalledWith(
        expect.objectContaining({ title: expect.stringContaining('Cambios') })
      );
    });
  });

  // ── Email template editing ────────────────────────────────────────────────

  describe('email template editing', () => {
    it('renders editable fields when a template with fields is loaded', async () => {
      mockProposalStore.fetchEmailTemplates.mockResolvedValueOnce({
        success: true,
        data: [{ template_key: 'welcome', name: 'Bienvenida', category: 'client', description: '', editable_fields_count: 1, is_customized: false, is_active: true }],
      });
      mockProposalStore.fetchEmailTemplateDetail.mockResolvedValueOnce({
        success: true,
        data: {
          editable_fields: [{ key: 'subject', label: 'Asunto', type: 'text', current_value: 'Hola!', default_value: 'Hola' }],
          is_active: true,
        },
      });

      const wrapper = mountPanel('emails');
      await flushPromises();
      await wrapper.findAll('button').find(b => b.text().includes('Bienvenida')).trigger('click');
      await flushPromises();

      expect(wrapper.text()).toContain('Asunto');
    });

    it('opens the email preview modal when the Vista previa button is clicked', async () => {
      mockProposalStore.fetchEmailTemplates.mockResolvedValueOnce({
        success: true,
        data: [{ template_key: 'welcome', name: 'Bienvenida', category: 'client', description: '', editable_fields_count: 0, is_customized: false, is_active: true }],
      });
      mockProposalStore.fetchEmailTemplateDetail.mockResolvedValueOnce({
        success: true,
        data: { editable_fields: [], is_active: true },
      });
      mockProposalStore.previewEmailTemplate.mockResolvedValueOnce({
        success: true,
        data: { html_preview: '<p>Preview</p>', subject: 'Test' },
      });

      const wrapper = mountPanel('emails');
      await flushPromises();
      await wrapper.findAll('button').find(b => b.text().includes('Bienvenida')).trigger('click');
      await flushPromises();

      const previewBtn = wrapper.findAll('button').find(b => b.text().includes('Vista previa'));
      expect(previewBtn).toBeTruthy();
      await previewBtn.trigger('click');
      await flushPromises();

      expect(mockProposalStore.previewEmailTemplate).toHaveBeenCalledWith('welcome');
    });

    it('sets emailShowResetConfirm when the Restaurar button is clicked', async () => {
      mockProposalStore.fetchEmailTemplates.mockResolvedValueOnce({
        success: true,
        data: [{ template_key: 'welcome', name: 'Bienvenida', category: 'client', description: '', editable_fields_count: 0, is_customized: false, is_active: true }],
      });
      mockProposalStore.fetchEmailTemplateDetail.mockResolvedValueOnce({
        success: true,
        data: { editable_fields: [], is_active: true },
      });

      const wrapper = mountPanel('emails');
      await flushPromises();
      await wrapper.findAll('button').find(b => b.text().includes('Bienvenida')).trigger('click');
      await flushPromises();

      const restaurarBtn = wrapper.findAll('button').find(b => b.text() === 'Restaurar');
      await restaurarBtn.trigger('click');

      expect(wrapper.vm.emailShowResetConfirm).toBe(true);
    });
  });

  // ── Prompt tab ────────────────────────────────────────────────────────────

  describe('prompt tab', () => {
    it('shows the copied confirmation after the Copiar button is clicked', async () => {
      const wrapper = mountPanel('prompt');
      await flushPromises();

      const copyBtn = wrapper.findAll('button').find(b => b.text() === 'Copiar' || b.text() === '¡Copiado!');
      expect(copyBtn).toBeTruthy();
      await copyBtn.trigger('click');
      await flushPromises();

      expect(wrapper.text()).toContain('¡Copiado!');
    });

    it('renders the Descargar .md button in the prompt tab', async () => {
      const wrapper = mountPanel('prompt');
      await flushPromises();

      const dlBtn = wrapper.findAll('button').find(b => b.text().includes('Descargar .md'));
      expect(dlBtn).toBeTruthy();
      await dlBtn.trigger('click');

      expect(wrapper.exists()).toBe(true);
    });
  });
});

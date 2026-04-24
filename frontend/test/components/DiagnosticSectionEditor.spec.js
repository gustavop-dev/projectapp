/**
 * Tests for DiagnosticSectionEditor.vue.
 *
 * Covers: accordion expand/collapse, meta field change emits,
 * form content emit, reset emit, isSaving/lastSavedAt display,
 * dynamic FormComponent selection by section_type.
 */

jest.mock('../../components/WebAppDiagnostic/admin/diagnosticSectionEditorUtils', () => ({
  SECTION_META: {
    purpose: { label: 'Propósito', icon: '🧭' },
    cost: { label: 'Costo y Pago', icon: '💰' },
  },
  VISIBILITY_OPTIONS: [
    { value: 'both', label: 'Ambos envíos' },
    { value: 'initial', label: 'Sólo envío inicial' },
  ],
  buildFormFromJson: jest.fn(() => ({ content: '' })),
  formToJson: jest.fn(() => ({ content: '' })),
}));

jest.mock('../../components/WebAppDiagnostic/admin/sections/PurposeForm.vue', () => ({
  name: 'PurposeForm',
  template: '<div data-testid="purpose-form"><slot /></div>',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/RadiographyForm.vue', () => ({
  name: 'RadiographyForm',
  template: '<div data-testid="radiography-form" />',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/CategoriesForm.vue', () => ({
  name: 'CategoriesForm',
  template: '<div />',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/DeliveryStructureForm.vue', () => ({
  name: 'DeliveryStructureForm',
  template: '<div />',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/ExecutiveSummaryForm.vue', () => ({
  name: 'ExecutiveSummaryForm',
  template: '<div />',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/CostForm.vue', () => ({
  name: 'CostForm',
  template: '<div data-testid="cost-form" />',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/TimelineForm.vue', () => ({
  name: 'TimelineForm',
  template: '<div />',
}));
jest.mock('../../components/WebAppDiagnostic/admin/sections/ScopeForm.vue', () => ({
  name: 'ScopeForm',
  template: '<div />',
}));

import { mount } from '@vue/test-utils';
import DiagnosticSectionEditor from '../../components/WebAppDiagnostic/admin/DiagnosticSectionEditor.vue';

const purposeSection = {
  id: 1,
  section_type: 'purpose',
  title: 'Propósito del diagnóstico',
  visibility: 'both',
  is_enabled: true,
  content_json: {},
  order: 1,
};

const costSection = {
  id: 2,
  section_type: 'cost',
  title: 'Costo y Pago',
  visibility: 'initial',
  is_enabled: false,
  content_json: {},
  order: 2,
};

function mountEditor(props = {}) {
  return mount(DiagnosticSectionEditor, {
    props: { section: purposeSection, ...props },
  });
}

describe('DiagnosticSectionEditor', () => {
  // ── Accordion ─────────────────────────────────────────────────────────────

  describe('accordion', () => {
    it('renders the section title in the accordion header', () => {
      const wrapper = mountEditor();

      expect(wrapper.text()).toContain('Propósito del diagnóstico');
    });

    it('does not render body by default (collapsed)', () => {
      const wrapper = mountEditor();

      expect(wrapper.find('input[type="text"]').exists()).toBe(false);
    });

    it('expands the body when the header is clicked', async () => {
      const wrapper = mountEditor();
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      expect(wrapper.find('input[type="text"]').exists()).toBe(true);
    });

    it('collapses the body when the header is clicked a second time', async () => {
      const wrapper = mountEditor();
      const header = wrapper.find('[class*="cursor-pointer"]');
      await header.trigger('click');
      await header.trigger('click');

      expect(wrapper.find('input[type="text"]').exists()).toBe(false);
    });
  });

  // ── Meta field changes ────────────────────────────────────────────────────

  describe('meta field changes', () => {
    it('emits update:section when the title input changes', async () => {
      const wrapper = mountEditor();
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      const titleInput = wrapper.find('input[type="text"]');
      await titleInput.setValue('Nuevo título');
      await titleInput.trigger('change');

      expect(wrapper.emitted('update:section')).toBeTruthy();
      expect(wrapper.emitted('update:section')[0][0]).toMatchObject({ title: 'Nuevo título' });
    });

    it('emits update:section when the visibility select changes', async () => {
      const wrapper = mountEditor();
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      const select = wrapper.find('select');
      await select.setValue('initial');
      await select.trigger('change');

      expect(wrapper.emitted('update:section')).toBeTruthy();
    });

    it('emits update:section when the is_enabled checkbox changes', async () => {
      const wrapper = mountEditor();
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      const checkbox = wrapper.find('input[type="checkbox"]');
      await checkbox.setChecked(false);
      await checkbox.trigger('change');

      expect(wrapper.emitted('update:section')).toBeTruthy();
    });
  });

  // ── Form content emit ─────────────────────────────────────────────────────

  describe('form content', () => {
    it('emits update:content when the dynamic form emits update:modelValue', async () => {
      const { formToJson } = require('../../components/WebAppDiagnostic/admin/diagnosticSectionEditorUtils');
      formToJson.mockReturnValue({ purpose: 'updated' });

      const wrapper = mountEditor();
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      // Trigger the sub-component's v-model update
      const formComponent = wrapper.findComponent({ name: 'PurposeForm' });
      await formComponent.vm.$emit('update:modelValue', { content: 'new value' });

      expect(wrapper.emitted('update:content')).toBeTruthy();
    });
  });

  // ── Reset emit ────────────────────────────────────────────────────────────

  describe('reset', () => {
    it('emits reset when the restore default button is clicked', async () => {
      const wrapper = mountEditor();
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      const resetBtn = wrapper.findAll('button').find(b => b.text().includes('Restaurar contenido'));
      await resetBtn.trigger('click');

      expect(wrapper.emitted('reset')).toBeTruthy();
    });
  });

  // ── Status display ────────────────────────────────────────────────────────

  describe('status display', () => {
    it('shows Guardando when isSaving is true', async () => {
      const wrapper = mountEditor({ isSaving: true });
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      expect(wrapper.text()).toContain('Guardando');
    });

    it('shows lastSavedAt text when the prop is non-empty', async () => {
      const wrapper = mountEditor({ lastSavedAt: 'hace 2 min' });
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      expect(wrapper.text()).toContain('hace 2 min');
    });
  });

  // ── Dynamic form component ────────────────────────────────────────────────

  describe('dynamic form component', () => {
    it('renders PurposeForm for section_type purpose', async () => {
      const wrapper = mountEditor({ section: purposeSection });
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      expect(wrapper.findComponent({ name: 'PurposeForm' }).exists()).toBe(true);
    });

    it('renders CostForm for section_type cost', async () => {
      const wrapper = mountEditor({ section: costSection });
      await wrapper.find('[class*="cursor-pointer"]').trigger('click');

      expect(wrapper.findComponent({ name: 'CostForm' }).exists()).toBe(true);
    });
  });
});

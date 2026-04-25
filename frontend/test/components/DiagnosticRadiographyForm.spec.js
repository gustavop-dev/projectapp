import { mount } from '@vue/test-utils';
import DiagnosticRadiographyForm from '../../components/WebAppDiagnostic/DiagnosticRadiographyForm.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

function baseValue(overrides = {}) {
  return {
    size_category: '',
    radiography: {
      stack: { backend: { name: '', version: '' }, frontend: { name: '', version: '' } },
      migrations_count: 0,
    },
    ...overrides,
  };
}

function mountForm(props = {}) {
  return mount(DiagnosticRadiographyForm, {
    props: {
      modelValue: baseValue(),
      busy: false,
      ...props,
    },
  });
}

describe('DiagnosticRadiographyForm', () => {
  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders the size_category select with the current value', () => {
    const wrapper = mountForm({ modelValue: baseValue({ size_category: 'medium' }) });
    const select = wrapper.find('select');

    expect(select.element.value).toBe('medium');
  });

  it('renders the NumField label text for Migraciones', () => {
    const wrapper = mountForm();

    expect(wrapper.text()).toContain('Migraciones');
  });

  it('renders the submit button with default label when not busy', () => {
    const wrapper = mountForm({ busy: false });

    expect(wrapper.find('button[type="submit"]').text()).toBe('Guardar radiografía');
  });

  // ── updateRoot ─────────────────────────────────────────────────────────────

  it('emits update:modelValue with updated size_category when select changes', async () => {
    const wrapper = mountForm();
    const select = wrapper.find('select');

    await select.setValue('large');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].size_category).toBe('large');
  });

  // ── updateStack ────────────────────────────────────────────────────────────

  it('emits update:modelValue with updated backend name when backend name input changes', async () => {
    const wrapper = mountForm();
    const input = wrapper.find('input[placeholder="Backend (nombre)"]');

    await input.setValue('Django');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].radiography.stack.backend.name).toBe('Django');
  });

  it('emits update:modelValue with updated frontend name when frontend name input changes', async () => {
    const wrapper = mountForm();
    const input = wrapper.find('input[placeholder="Frontend (nombre)"]');

    await input.setValue('Nuxt');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].radiography.stack.frontend.name).toBe('Nuxt');
  });

  // ── updateRad via NumField ─────────────────────────────────────────────────

  it('emits update:modelValue with updated numeric field when a NumField input changes', async () => {
    const wrapper = mountForm();
    const numInputs = wrapper.findAll('input[type="number"]');

    await numInputs[0].setValue(7);
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].radiography).toBeDefined();
  });

  // ── busy state ─────────────────────────────────────────────────────────────

  it('submit button is enabled when busy is false', () => {
    const wrapper = mountForm({ busy: false });

    expect(wrapper.find('button[type="submit"]').element.disabled).toBe(false);
  });

  it('submit button is disabled when busy is true', () => {
    const wrapper = mountForm({ busy: true });

    expect(wrapper.find('button[type="submit"]').element.disabled).toBe(true);
  });

  it('shows a saving label on the submit button when busy is true', () => {
    const wrapper = mountForm({ busy: true });

    expect(wrapper.find('button[type="submit"]').text()).toBe('Guardando...');
  });

  // ── form submit ────────────────────────────────────────────────────────────

  it('emits submit event when the form is submitted', async () => {
    const wrapper = mountForm();

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')).toBeTruthy();
  });

  // ── computed fallbacks ─────────────────────────────────────────────────────

  it('renders without error when modelValue has no radiography key', () => {
    expect(() => mountForm({ modelValue: { size_category: '' } })).not.toThrow();
  });

  it('renders without error when radiography has no stack key', () => {
    expect(() => mountForm({ modelValue: { size_category: '', radiography: {} } })).not.toThrow();
  });
});

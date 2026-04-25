jest.mock('../../stores/diagnostics_constants', () => ({
  SEVERITY_LEVELS: ['Crítico', 'Alto', 'Medio', 'Bajo'],
}));

import { mount } from '@vue/test-utils';
import CategoriesForm from '../../components/WebAppDiagnostic/admin/sections/CategoriesForm.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

function makeCategory(overrides = {}) {
  return {
    key: '',
    title: 'Categoría A',
    description: '',
    strengthsText: '',
    findings: [],
    recommendations: [],
    ...overrides,
  };
}

function mountForm(categories = []) {
  return mount(CategoriesForm, {
    props: { modelValue: { index: '', title: '', intro: '', categories } },
  });
}

describe('CategoriesForm', () => {
  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders one accordion panel per category provided in modelValue', () => {
    const wrapper = mountForm([makeCategory(), makeCategory({ title: 'B' })]);

    expect(wrapper.findAll('details')).toHaveLength(2);
  });

  it('renders no accordion panels when categories list is empty', () => {
    const wrapper = mountForm([]);

    expect(wrapper.findAll('details')).toHaveLength(0);
  });

  it('displays category count in the section header', () => {
    const wrapper = mountForm([makeCategory(), makeCategory()]);

    expect(wrapper.text()).toContain('2');
  });

  it('shows each category title inside its accordion summary', () => {
    const wrapper = mountForm([
      makeCategory({ title: 'Alpha' }),
      makeCategory({ title: 'Beta' }),
    ]);
    const panels = wrapper.findAll('details');

    expect(panels[0].text()).toContain('Alpha');
    expect(panels[1].text()).toContain('Beta');
  });

  // ── addCategory ────────────────────────────────────────────────────────────

  it('addCategory appends a new accordion panel when the button is clicked', async () => {
    const wrapper = mountForm([]);

    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect(wrapper.findAll('details')).toHaveLength(1);
  });

  it('addCategory emits update:modelValue with categories length increased by one', async () => {
    const wrapper = mountForm([]);

    await wrapper.find('button').trigger('click');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].categories).toHaveLength(1);
  });

  it('addCategory initialises the new category with empty findings and recommendations', async () => {
    const wrapper = mountForm([]);

    await wrapper.find('button').trigger('click');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    const newCat = events[events.length - 1][0].categories[0];
    expect(newCat.findings).toEqual([]);
    expect(newCat.recommendations).toEqual([]);
  });

  // ── removeCategory ─────────────────────────────────────────────────────────

  it('removeCategory reduces the accordion count by one', async () => {
    const wrapper = mountForm([makeCategory(), makeCategory({ title: 'B' })]);
    const removeBtn = wrapper.findAll('button').find((b) => b.text() === 'Quitar');

    await removeBtn.trigger('click');
    await flushPromises();

    expect(wrapper.findAll('details')).toHaveLength(1);
  });

  it('removeCategory emits update:modelValue with the entry removed', async () => {
    const wrapper = mountForm([makeCategory({ title: 'First' }), makeCategory({ title: 'Second' })]);
    const removeBtn = wrapper.findAll('button').find((b) => b.text() === 'Quitar');

    await removeBtn.trigger('click');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].categories).toHaveLength(1);
  });

  // ── addFinding ─────────────────────────────────────────────────────────────

  it('addFinding appends a finding row and emits update:modelValue', async () => {
    const wrapper = mountForm([makeCategory()]);
    const addButtons = wrapper.findAll('button').filter((b) => b.text() === '+ Agregar');

    await addButtons[0].trigger('click');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].categories[0].findings).toHaveLength(1);
  });

  // ── addRec ─────────────────────────────────────────────────────────────────

  it('addRec appends a recommendation row and emits update:modelValue', async () => {
    const wrapper = mountForm([makeCategory()]);
    const addButtons = wrapper.findAll('button').filter((b) => b.text() === '+ Agregar');

    await addButtons[1].trigger('click');
    await flushPromises();

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0].categories[0].recommendations).toHaveLength(1);
  });

  // ── SEVERITY_LEVELS ────────────────────────────────────────────────────────

  it('renders SEVERITY_LEVELS options inside a finding severity select', () => {
    const wrapper = mountForm([makeCategory({ findings: [{ level: '', title: '', detail: '' }] })]);
    const selects = wrapper.findAll('select');
    const optionTexts = selects[0].findAll('option').map((o) => o.text());

    expect(optionTexts).toContain('Crítico');
    expect(optionTexts).toContain('Alto');
    expect(optionTexts).toContain('Medio');
    expect(optionTexts).toContain('Bajo');
  });

  it('renders SEVERITY_LEVELS options inside a recommendation severity select', () => {
    const wrapper = mountForm([
      makeCategory({ recommendations: [{ level: '', title: '', detail: '' }] }),
    ]);
    const selects = wrapper.findAll('select');
    const optionTexts = selects[0].findAll('option').map((o) => o.text());

    expect(optionTexts).toContain('Crítico');
    expect(optionTexts).toContain('Bajo');
  });

  // ── prop watcher ───────────────────────────────────────────────────────────

  it('prop change rerenders with the updated categories list', async () => {
    const wrapper = mountForm([makeCategory({ title: 'Original' })]);

    await wrapper.setProps({
      modelValue: {
        index: '',
        title: '',
        intro: '',
        categories: [makeCategory({ title: 'A' }), makeCategory({ title: 'B' })],
      },
    });
    await flushPromises();

    expect(wrapper.findAll('details')).toHaveLength(2);
  });

  // ── deep clone isolation ───────────────────────────────────────────────────

  it('form mutation via UI does not affect the original prop array', async () => {
    const original = [makeCategory({ title: 'Stable' })];
    const wrapper = mountForm(original);

    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect(original).toHaveLength(1);
  });
});

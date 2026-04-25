import { mount } from '@vue/test-utils';
import CategoriesSection from '../../components/WebAppDiagnostic/public/CategoriesSection.vue';

const SectionHeaderStub = {
  name: 'SectionHeader',
  props: ['index', 'title', 'fallback'],
  template: '<div data-testid="section-header">{{ title }}</div>',
};

function makeCategory(overrides = {}) {
  return {
    key: 'test-cat',
    title: 'Categoría de prueba',
    description: 'Descripción de la categoría',
    strengths: [],
    findings: [],
    recommendations: [],
    ...overrides,
  };
}

function mountSection(contentOverrides = {}) {
  const content = {
    index: 1,
    title: 'Título de sección',
    intro: 'Introducción de la sección',
    categories: [],
    ...contentOverrides,
  };
  return mount(CategoriesSection, {
    props: { content },
    global: { stubs: { SectionHeader: SectionHeaderStub } },
  });
}

describe('CategoriesSection', () => {
  it('renders the section title via SectionHeader', () => {
    const wrapper = mountSection({ title: 'Mi sección' });

    expect(wrapper.find('[data-testid="section-header"]').text()).toBe('Mi sección');
  });

  it('renders intro text when content.intro is provided', () => {
    const wrapper = mountSection({ intro: 'Texto de introducción' });

    expect(wrapper.text()).toContain('Texto de introducción');
  });

  it('renders one details element per category', () => {
    const wrapper = mountSection({
      categories: [makeCategory({ key: 'a' }), makeCategory({ key: 'b' }), makeCategory({ key: 'c' })],
    });

    expect(wrapper.findAll('details')).toHaveLength(3);
  });

  it('renders each category title in its summary', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ title: 'Primera categoría' }),
        makeCategory({ title: 'Segunda categoría' }),
      ],
    });

    const text = wrapper.text();
    expect(text).toContain('Primera categoría');
    expect(text).toContain('Segunda categoría');
  });

  it('levelClass applies bg-rose-100 class for Crítico severity finding', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ findings: [{ level: 'Crítico', title: 'Hallazgo crítico' }] }),
      ],
    });

    const badge = wrapper.find('span.bg-rose-100');
    expect(badge.exists()).toBe(true);
  });

  it('levelClass applies bg-amber-100 class for Alto severity finding', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ findings: [{ level: 'Alto', title: 'Hallazgo alto' }] }),
      ],
    });

    expect(wrapper.find('span.bg-amber-100').exists()).toBe(true);
  });

  it('levelClass applies bg-emerald-100 class for Bajo severity finding', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ findings: [{ level: 'Bajo', title: 'Hallazgo bajo' }] }),
      ],
    });

    expect(wrapper.find('span.bg-emerald-100').exists()).toBe(true);
  });

  it('renders strengths list when category has strengths', () => {
    const wrapper = mountSection({
      categories: [makeCategory({ strengths: ['Fortaleza uno', 'Fortaleza dos'] })],
    });

    const text = wrapper.text();
    expect(text).toContain('Fortaleza uno');
    expect(text).toContain('Fortaleza dos');
  });

  it('renders findings list when category has findings', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ findings: [{ level: 'Alto', title: 'Hallazgo importante', detail: 'Detalle' }] }),
      ],
    });

    expect(wrapper.text()).toContain('Hallazgo importante');
  });

  it('renders recommendations when category has recommendations', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ recommendations: [{ level: 'Bajo', title: 'Recomendación A' }] }),
      ],
    });

    expect(wrapper.text()).toContain('Recomendación A');
  });

  it('shows empty-state message when category has no strengths, findings, or recommendations', () => {
    const wrapper = mountSection({
      categories: [makeCategory({ strengths: [], findings: [], recommendations: [] })],
    });

    expect(wrapper.text()).toContain(
      'Hallazgos y recomendaciones se completarán durante el diagnóstico.',
    );
  });

  it('shows findings count badge when category has findings', () => {
    const wrapper = mountSection({
      categories: [
        makeCategory({ findings: [{ level: 'Alto', title: 'H1' }, { level: 'Bajo', title: 'H2' }] }),
      ],
    });

    expect(wrapper.text()).toContain('2 hallazgo(s)');
  });
});

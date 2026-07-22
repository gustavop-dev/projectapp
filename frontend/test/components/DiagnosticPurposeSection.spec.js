import { mount } from '@vue/test-utils';

import PurposeSection from '../../components/WebAppDiagnostic/public/PurposeSection.vue';

const content = (overrides = {}) => ({
  index: '01',
  title: 'Propósito',
  paragraphs: ['Primer párrafo.', 'Segundo párrafo.'],
  scopeNote: '',
  severityLevels: [],
  ...overrides,
});

describe('WebAppDiagnostic public PurposeSection', () => {
  it('renders every paragraph', () => {
    const wrapper = mount(PurposeSection, { props: { content: content() } });
    expect(wrapper.text()).toContain('Primer párrafo.');
    expect(wrapper.text()).toContain('Segundo párrafo.');
  });

  it('shows the scope note only when provided', () => {
    const withNote = mount(PurposeSection, {
      props: { content: content({ scopeNote: 'Solo frontend.' }) },
    });
    const withoutNote = mount(PurposeSection, { props: { content: content() } });
    expect(withNote.find('blockquote').text()).toContain('Solo frontend.');
    expect(withoutNote.find('blockquote').exists()).toBe(false);
  });

  it('renders one severity row per level with the default heading', () => {
    const wrapper = mount(PurposeSection, {
      props: {
        content: content({
          severityLevels: [
            { level: 'Alta', meaning: 'Bloquea operación' },
            { level: 'Media', meaning: 'Afecta UX' },
          ],
        }),
      },
    });
    expect(wrapper.text()).toContain('Escala de Severidad');
    expect(wrapper.findAll('tbody tr')).toHaveLength(2);
  });

  it('prefers a custom severity heading when provided', () => {
    const wrapper = mount(PurposeSection, {
      props: {
        content: content({
          severityTitle: 'Niveles de riesgo',
          severityLevels: [{ level: 'Alta', meaning: 'X' }],
        }),
      },
    });
    expect(wrapper.text()).toContain('Niveles de riesgo');
  });
});

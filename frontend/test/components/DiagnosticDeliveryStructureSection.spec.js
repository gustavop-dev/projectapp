import { mount } from '@vue/test-utils';

import DeliveryStructureSection from '../../components/WebAppDiagnostic/public/DeliveryStructureSection.vue';

const content = (overrides = {}) => ({
  index: '02',
  title: 'Estructura',
  intro: '',
  blocks: [],
  ...overrides,
});

describe('WebAppDiagnostic public DeliveryStructureSection', () => {
  it('shows the intro only when provided', () => {
    const withIntro = mount(DeliveryStructureSection, {
      props: { content: content({ intro: 'Así entregamos.' }) },
    });
    const withoutIntro = mount(DeliveryStructureSection, { props: { content: content() } });
    expect(withIntro.text()).toContain('Así entregamos.');
    expect(withoutIntro.text()).not.toContain('Así entregamos.');
  });

  it('renders one card per block with its title and paragraphs', () => {
    const wrapper = mount(DeliveryStructureSection, {
      props: {
        content: content({
          blocks: [
            { title: 'Informe', paragraphs: ['PDF con hallazgos.'] },
            { title: 'Sesión', paragraphs: ['Videollamada de cierre.'] },
          ],
        }),
      },
    });
    expect(wrapper.findAll('h3')).toHaveLength(2);
    expect(wrapper.text()).toContain('PDF con hallazgos.');
    expect(wrapper.text()).toContain('Videollamada de cierre.');
  });

  it('renders the example blockquote when the block includes one', () => {
    const wrapper = mount(DeliveryStructureSection, {
      props: {
        content: content({
          blocks: [{ title: 'Informe', paragraphs: [], example: 'Ver anexo 2' }],
        }),
      },
    });
    expect(wrapper.find('blockquote').text()).toContain('Ejemplo: Ver anexo 2');
  });

  it('omits the example blockquote when the block has none', () => {
    const wrapper = mount(DeliveryStructureSection, {
      props: { content: content({ blocks: [{ title: 'Informe', paragraphs: ['X'] }] }) },
    });
    expect(wrapper.find('blockquote').exists()).toBe(false);
  });
});

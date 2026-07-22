import { mount } from '@vue/test-utils';

import ScopeSection from '../../components/WebAppDiagnostic/public/ScopeSection.vue';

describe('WebAppDiagnostic public ScopeSection', () => {
  it('renders one bullet per consideration', () => {
    const wrapper = mount(ScopeSection, {
      props: {
        content: {
          index: '01',
          title: 'Alcance',
          considerations: ['Solo módulo de pagos', 'Sin migración de datos'],
        },
      },
    });
    const items = wrapper.findAll('li');
    expect(items).toHaveLength(2);
    expect(items[1].text()).toContain('Sin migración de datos');
  });

  it('shows the provided section title', () => {
    const wrapper = mount(ScopeSection, {
      props: { content: { index: '01', title: 'Alcance real', considerations: [] } },
    });
    expect(wrapper.text()).toContain('Alcance real');
  });

  it('falls back to the default title when none is provided', () => {
    const wrapper = mount(ScopeSection, {
      props: { content: { index: '01', title: '', considerations: [] } },
    });
    expect(wrapper.text()).toContain('Alcance y Consideraciones');
  });
});

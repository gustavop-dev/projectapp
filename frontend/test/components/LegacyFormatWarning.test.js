import { mount } from '@vue/test-utils';
import LegacyFormatWarning from '../../components/panel/LegacyFormatWarning.vue';

function mountWarning(props = {}) {
  return mount(LegacyFormatWarning, {
    props: {
      issues: ['old_field'],
      fieldLabels: { old_field: 'Campo legado' },
      ...props,
    },
  });
}

describe('LegacyFormatWarning', () => {
  it('does not render anything when there are no issues', () => {
    const wrapper = mountWarning({ issues: [] });

    expect(wrapper.html()).toBe('<!--v-if-->');
  });

  it('renders labeled issues and the default action label', () => {
    const wrapper = mountWarning();

    expect(wrapper.text()).toContain('JSON con formato desactualizado');
    expect(wrapper.text()).toContain('Campo legado');
    expect(wrapper.text()).toContain('Descarga la versión corregida');
  });

  it('falls back to the raw issue key when no label mapping exists', () => {
    const wrapper = mountWarning({ fieldLabels: {} });

    expect(wrapper.text()).toContain('old_field');
  });

  it('renders a custom action label and emits download on click', async () => {
    const wrapper = mountWarning({ actionLabel: 'Acción personalizada' });

    expect(wrapper.text()).toContain('Acción personalizada');
    await wrapper.get('button').trigger('click');

    expect(wrapper.emitted('download')).toEqual([[]]);
  });
});

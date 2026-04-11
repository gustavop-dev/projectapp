import { mount } from '@vue/test-utils';
import PromptSubTabsPanel from '../../components/panel/PromptSubTabsPanel.vue';

function mountPanel(props = {}) {
  return mount(PromptSubTabsPanel, {
    props: {
      modelValue: 'commercial',
      ...props,
    },
    slots: {
      commercial: '<div data-testid="commercial-slot">Comercial</div>',
      technical: '<div data-testid="technical-slot">Técnico</div>',
    },
  });
}

describe('PromptSubTabsPanel', () => {
  it('shows the commercial slot by default', () => {
    const wrapper = mountPanel();

    expect(wrapper.get('[data-testid="commercial-slot"]').isVisible()).toBe(true);
    expect(wrapper.get('[data-testid="technical-slot"]').isVisible()).toBe(false);
  });

  it('shows the technical slot when modelValue is technical', () => {
    const wrapper = mountPanel({ modelValue: 'technical' });

    expect(wrapper.get('[data-testid="commercial-slot"]').isVisible()).toBe(false);
    expect(wrapper.get('[data-testid="technical-slot"]').isVisible()).toBe(true);
  });

  it('emits update:modelValue when a tab is selected', async () => {
    const wrapper = mountPanel();

    await wrapper.findAll('button')[1].trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([['technical']]);
  });

  it('uses dark track styles when darkTrack is true', () => {
    const wrapper = mountPanel({ darkTrack: true, modelValue: 'technical' });
    const track = wrapper.findAll('div')[1];

    expect(wrapper.text()).toContain('Propuesta comercial');
    expect(track.classes().join(' ')).toContain('bg-gray-100');
    expect(wrapper.findAll('button')[1].classes().join(' ')).toContain('dark:bg-gray-800');
  });
});

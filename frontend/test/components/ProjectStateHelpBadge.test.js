import { mount } from '@vue/test-utils';
import ProjectStateHelpBadge from '../../components/panel/projects/ProjectStateHelpBadge.vue';

const STATE = {
  id: 3,
  name: 'En evolución',
  description: 'Está en producción mientras se desarrolla una ampliación.',
  operational_effect_help: 'Mantiene habilitados los cobros y los avisos.',
};

function mountBadge() {
  return mount(ProjectStateHelpBadge, {
    props: { state: STATE, testId: 'evolving-help' },
  });
}

describe('ProjectStateHelpBadge', () => {
  it('opens the complete state help on click', async () => {
    const wrapper = mountBadge();

    await wrapper.get('[data-testid="evolving-help"]').trigger('click');

    const help = wrapper.get('[data-testid="evolving-help-content"]');
    expect(help.text()).toContain(STATE.description);
    expect(help.text()).toContain(`Implica: ${STATE.operational_effect_help}`);
  });

  it('links the trigger to its accessible tooltip', () => {
    const wrapper = mountBadge();
    const trigger = wrapper.get('[data-testid="evolving-help"]');

    expect(trigger.attributes('aria-label')).toBe(
      'Ayuda sobre el estado En evolución',
    );
    expect(trigger.attributes('aria-describedby')).toBeTruthy();
  });
});

/**
 * Tests for ValueAddedModules — per-module condition gating ("condicionado")
 * and the terms & conditions modal (Req 3).
 *
 * Covers:
 * - minimum note shown only when the effective total is below the module min
 * - duration badge shown regardless of the minimum gate
 * - the "Términos y condiciones" button opens ModuleTermsModal WITHOUT
 *   triggering the card's detail modal (@click.stop)
 */
import { mount } from '@vue/test-utils';

jest.mock('~/composables/useSectionAnimations', () => ({
  useSectionAnimations: () => {},
}));
const mockTrack = jest.fn();
jest.mock('~/utils/trackRequirementClick', () => ({
  trackRequirementClick: (...args) => mockTrack(...args),
}));

import ValueAddedModules from '../../components/BusinessProposal/ValueAddedModules.vue';

const AI_GROUP = {
  id: 'ai_automation_module',
  icon: '🤖',
  title: 'Automatización con Asistente de IA',
  description: 'Automatiza un proceso manual con IA.',
  items: [],
};

function makeProps({ effectiveTotal = 0, currency = 'COP' } = {}) {
  return {
    section: {
      section_type: 'value_added_modules',
      content_json: {
        title: 'Incluido',
        module_ids: ['ai_automation_module'],
        justifications: { ai_automation_module: 'Para automatizar tu proceso.' },
        conditions: {
          ai_automation_module: {
            min_price_cop: 10400000,
            min_price_usd: 2900,
            duration_months: 6,
            discretionary_note: 'Se implementa si tiene sentido automatizar.',
            terms: 'Depende de que el asistente de IA siga ofreciendo la integración.',
          },
        },
      },
    },
    proposal: {
      language: 'es',
      currency,
      uuid: 'test-uuid',
      sections: [
        { section_type: 'functional_requirements', content_json: { groups: [AI_GROUP] } },
      ],
    },
    proposalUuid: 'test-uuid',
    itemRequirementsMap: {},
    effectiveTotal,
  };
}

function mountComponent(props) {
  return mount(ValueAddedModules, {
    props,
    global: { stubs: { teleport: true, transition: false } },
  });
}

describe('ValueAddedModules — condition gating', () => {
  beforeEach(() => mockTrack.mockClear());

  it('shows the minimum note when the effective total is below the minimum', () => {
    const wrapper = mountComponent(makeProps({ effectiveTotal: 5000000 }));
    const note = wrapper.find('[data-testid="value-added-minimum-ai_automation_module"]');
    expect(note.exists()).toBe(true);
    expect(note.text()).toContain('Disponible en proyectos desde');
  });

  it('hides the minimum note when the effective total meets the minimum', () => {
    const wrapper = mountComponent(makeProps({ effectiveTotal: 15000000 }));
    expect(
      wrapper.find('[data-testid="value-added-minimum-ai_automation_module"]').exists(),
    ).toBe(false);
    // duration badge is independent of the minimum gate
    expect(wrapper.text()).toContain('Disponible por 6 meses');
  });

  it('compares against the USD minimum when currency is USD', () => {
    // 2000 USD < 2900 USD minimum → note shown
    const wrapper = mountComponent(makeProps({ effectiveTotal: 2000, currency: 'USD' }));
    expect(
      wrapper.find('[data-testid="value-added-minimum-ai_automation_module"]').exists(),
    ).toBe(true);
  });
});

describe('ValueAddedModules — terms modal', () => {
  beforeEach(() => mockTrack.mockClear());

  it('opens the terms modal without triggering the card detail modal', async () => {
    const wrapper = mountComponent(makeProps({ effectiveTotal: 5000000 }));

    await wrapper
      .find('[data-testid="value-added-terms-ai_automation_module"]')
      .trigger('click');

    // Terms modal body is now visible with the module terms
    const body = wrapper.find('[data-testid="module-terms-body"]');
    expect(body.exists()).toBe(true);
    expect(body.text()).toContain('asistente de IA');

    // @click.stop prevented the card's openModal → no engagement tracking fired
    expect(mockTrack).not.toHaveBeenCalled();
  });
});

/**
 * Tests for the categorised legal terms of the value-added modules.
 *
 * The clauses (`conditions[id].terms_clauses`) and the section-level
 * `general_terms` come from the backend and feed BOTH the public modal and the
 * PDF annex. These cover the web side:
 * - each clause renders with its category label and its bold emphasis
 * - proposals predating the clause format still render from the flat `terms`
 * - the general provisions render once at the end of the section
 */
import { mount } from '@vue/test-utils';

jest.mock('~/composables/useSectionAnimations', () => ({
  useSectionAnimations: () => {},
}));
jest.mock('~/utils/trackRequirementClick', () => ({
  trackRequirementClick: () => {},
}));

import ValueAddedModules from '../../components/BusinessProposal/ValueAddedModules.vue';
import ModuleTermsModal from '../../components/BusinessProposal/ModuleTermsModal.vue';

const AI_GROUP = {
  id: 'ai_automation_module',
  icon: '🤖',
  title: 'Automatización con Asistente de IA',
  description: 'Automatiza un proceso manual con IA.',
  items: [],
};

const CLAUSES = [
  { label: 'Elegibilidad', text: 'Aplica a proyectos que superen los **2.900 USD**.' },
  {
    label: 'Vigencia',
    text: 'Disponible por **6 meses** contados desde el despliegue en producción.',
  },
  {
    label: 'Exclusión de responsabilidad',
    text: 'Si el proveedor discontinúa la integración no somos responsables.',
  },
];

const GENERAL_TERMS = {
  title: 'Disposiciones generales aplicables a los módulos incluidos',
  clauses: [
    { label: 'Fuerza mayor y caso fortuito', text: 'No hay responsabilidad por **fuerza mayor**.' },
    { label: 'Intransferibilidad y no canje', text: 'No son canjeables por dinero.' },
  ],
};

function makeProps({ conditions, generalTerms } = {}) {
  const content = {
    title: 'Incluido',
    module_ids: ['ai_automation_module'],
    justifications: { ai_automation_module: 'Para automatizar tu proceso.' },
    conditions: conditions || {
      ai_automation_module: {
        duration_months: 6,
        discretionary_note: 'Se implementa si **tiene sentido** automatizar.',
        terms_clauses: CLAUSES,
        terms: 'irrelevante cuando hay cláusulas',
      },
    },
  };
  if (generalTerms !== null) content.general_terms = generalTerms || GENERAL_TERMS;

  return {
    section: { section_type: 'value_added_modules', content_json: content },
    proposal: {
      language: 'es',
      currency: 'COP',
      uuid: 'test-uuid',
      sections: [
        { section_type: 'functional_requirements', content_json: { groups: [AI_GROUP] } },
      ],
    },
    proposalUuid: 'test-uuid',
    itemRequirementsMap: {},
    effectiveTotal: 15000000,
  };
}

function mountComponent(props) {
  return mount(ValueAddedModules, {
    props,
    global: { stubs: { teleport: true, transition: false } },
  });
}

async function openTermsModal(wrapper) {
  await wrapper.find('[data-testid="value-added-terms-ai_automation_module"]').trigger('click');
  return wrapper.findComponent(ModuleTermsModal);
}

describe('ModuleTermsModal — categorised clauses', () => {
  it('renders one entry per clause with its category label', async () => {
    const wrapper = mountComponent(makeProps());
    const modal = await openTermsModal(wrapper);

    const labels = modal.findAll('[data-testid="module-terms-clause-label"]');
    expect(labels).toHaveLength(CLAUSES.length);
    expect(labels.map((l) => l.text())).toEqual([
      'Elegibilidad',
      'Vigencia',
      'Exclusión de responsabilidad',
    ]);
  });

  it('renders the bold emphasis inside a clause as real markup', async () => {
    const wrapper = mountComponent(makeProps());
    const modal = await openTermsModal(wrapper);

    const html = modal.find('[data-testid="module-terms-clauses"]').html();
    expect(html).toContain('<strong>6 meses</strong>');
    expect(html).toContain('<strong>2.900 USD</strong>');
    expect(html).not.toContain('**');
  });

  it('shows the term is counted from the production deployment', async () => {
    const wrapper = mountComponent(makeProps());
    const modal = await openTermsModal(wrapper);

    expect(modal.find('[data-testid="module-terms-body"]').text())
      .toContain('contados desde el despliegue en producción');
  });

  it('falls back to the flat terms string for proposals without clauses', async () => {
    const wrapper = mountComponent(makeProps({
      conditions: {
        ai_automation_module: {
          duration_months: 6,
          terms: '**Alcance.** Cubre un proceso.\n**Vigencia.** Dura 6 meses.',
        },
      },
    }));
    const modal = await openTermsModal(wrapper);

    const labels = modal.findAll('[data-testid="module-terms-clause-label"]');
    expect(labels.map((l) => l.text())).toEqual(['Alcance', 'Vigencia']);
    expect(modal.find('[data-testid="module-terms-clauses"]').text())
      .toContain('Cubre un proceso.');
  });

  it('escapes HTML coming from the clause text', async () => {
    const wrapper = mountComponent(makeProps({
      conditions: {
        ai_automation_module: {
          terms_clauses: [{ label: 'Alcance', text: '<img src=x onerror=alert(1)>' }],
        },
      },
    }));
    const modal = await openTermsModal(wrapper);

    const html = modal.find('[data-testid="module-terms-clauses"]').html();
    expect(html).not.toContain('<img');
    expect(html).toContain('&lt;img');
  });
});

describe('ValueAddedModules — general provisions', () => {
  it('renders the general provisions once at the end of the section', () => {
    const wrapper = mountComponent(makeProps());
    const block = wrapper.find('[data-testid="value-added-general-terms"]');

    expect(block.exists()).toBe(true);
    expect(block.text()).toContain(GENERAL_TERMS.title);
    expect(wrapper.findAll('[data-testid="value-added-general-label"]').map((l) => l.text()))
      .toEqual(['Fuerza mayor y caso fortuito', 'Intransferibilidad y no canje']);
  });

  it('renders bold emphasis inside the general provisions', () => {
    const wrapper = mountComponent(makeProps());
    expect(wrapper.find('[data-testid="value-added-general-terms"]').html())
      .toContain('<strong>fuerza mayor</strong>');
  });

  it('omits the block when the section carries no general provisions', () => {
    const wrapper = mountComponent(makeProps({ generalTerms: null }));
    expect(wrapper.find('[data-testid="value-added-general-terms"]').exists()).toBe(false);
  });

  it('renders bold emphasis in the discretionary note on the card', () => {
    const wrapper = mountComponent(makeProps());
    expect(wrapper.html()).toContain('<strong>tiene sentido</strong>');
  });
});

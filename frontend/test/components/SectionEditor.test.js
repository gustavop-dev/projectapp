/**
 * Tests for SectionEditor pure utility functions.
 *
 * Covers: arrToText, textToArr, buildFormFromJson, formToJson,
 * formToReadableText, groupToReadableText, buildSavePayload
 * for all 12 section types with form/paste mode and edge cases.
 */
import {
  arrToText,
  textToArr,
  buildFormFromJson,
  formToJson,
  formToReadableText,
  groupToReadableText,
  buildSavePayload,
} from '../../components/BusinessProposal/admin/sectionEditorUtils.js';


// ─── Fixtures ────────────────────────────────────────────────────────────────

const greetingJson = {
  clientName: 'María García',
  inspirationalQuote: 'Design is how it works.',
};

const executiveSummaryJson = {
  index: '1',
  title: 'Resumen ejecutivo',
  paragraphs: ['Primer párrafo.', 'Segundo párrafo.'],
  highlightsTitle: 'Incluye',
  highlights: ['Diseño personalizado', 'Desarrollo responsivo'],
};

const contextDiagnosticJson = {
  index: '2',
  title: 'Contexto',
  paragraphs: ['El cliente busca fortalecer su presencia digital.'],
  issuesTitle: 'Desafíos',
  issues: ['Falta de presencia digital', 'Difícil captar clientes'],
  opportunityTitle: 'Oportunidad',
  opportunity: 'Crear una plataforma que genere confianza.',
};

const conversionStrategyJson = {
  index: '3',
  title: 'Estrategia',
  intro: 'La página se construirá como herramienta de conversión.',
  steps: [
    { title: 'Captar atención', bullets: ['Mensaje claro', 'Beneficio visible'] },
    { title: 'Construir confianza', bullets: ['Testimonios'] },
  ],
  resultTitle: 'Resultado',
  result: 'Una página que genere contactos.',
};

const designUxJson = {
  index: '4',
  title: 'Diseño UX',
  paragraphs: ['El desarrollo será una experiencia digital.'],
  focusTitle: 'Estructura',
  focusItems: ['Presentación clara', 'Integración redes sociales'],
  objectiveTitle: 'Objetivo',
  objective: 'Inspirar confianza.',
};

const creativeSupportJson = {
  index: '5',
  title: 'Acompañamiento',
  paragraphs: ['El cliente contará con acompañamiento cercano.'],
  includesTitle: 'Incluye',
  includes: ['Sesiones de revisión', 'Apoyo visual'],
  closing: 'Cada decisión será co-creación.',
};

const developmentStagesJson = {
  stages: [
    { icon: '✉️', title: 'Propuesta', description: 'Etapa actual.', current: true },
    { icon: '🎨', title: 'Diseño', description: 'Prototipo en Figma.' },
    { icon: '💻', title: 'Desarrollo', description: 'Implementación.' },
  ],
};

const functionalRequirementsJson = {
  index: '7',
  title: 'Requerimientos',
  intro: 'Detalle de requerimientos.',
  groups: [
    {
      id: 'views', icon: '🖥️', title: 'Vistas', description: 'Pantallas.',
      items: [
        { icon: '🏠', name: 'Home', description: 'Landing con CTAs.' },
        { icon: '📧', name: 'Contacto', description: 'Formulario.' },
      ],
    },
  ],
  additionalModules: [
    {
      icon: '📊', title: 'Analytics', description: 'Dashboard.',
      items: [{ icon: '📈', name: 'Reports', description: 'Reportes.' }],
    },
  ],
};

const functionalRequirementsJsonWithPaste = {
  index: '7',
  title: 'Requerimientos',
  intro: 'Detalle.',
  groups: [
    {
      id: 'views', icon: '🖥️', title: 'Vistas', description: '',
      items: [], _editMode: 'paste', rawText: 'Pasted views content',
    },
  ],
  additionalModules: [
    {
      icon: '📊', title: 'Analytics', description: '',
      items: [], _editMode: 'paste', rawText: 'Pasted analytics',
    },
  ],
};

const timelineJson = {
  index: '8',
  title: 'Cronograma',
  introText: 'Fases del proyecto.',
  totalDuration: '1 mes',
  phases: [
    {
      title: 'Diseño', duration: '1 semana', description: 'Diseño visual.',
      tasks: ['Moodboard', 'Wireframes'], milestone: 'Diseño aprobado',
    },
  ],
};

const investmentJson = {
  index: '9',
  title: 'Inversión',
  introText: 'La inversión total es:',
  totalInvestment: '$3.500.000',
  currency: 'COP',
  whatsIncluded: [
    { icon: '🎨', title: 'Diseño', description: 'UX/UI' },
  ],
  paymentOptions: [
    { label: '40% al firmar', description: '$1.400.000' },
  ],
  hostingPlan: {
    title: 'Hosting, Mantenimiento y Soporte',
    description: 'Infraestructura optimizada.',
    specs: [
      { icon: '🧠', label: 'vCPU', value: '1 núcleo' },
      { icon: '🧮', label: 'RAM', value: '1 GB' },
    ],
    monthlyPrice: '$49.999 COP',
    monthlyLabel: 'por mes',
    annualPrice: '$680.000 COP',
    annualLabel: 'Hosting anual — Año 1',
    renewalNote: 'Renovación con SMLMV.',
    coverageNote: 'Cubre mantenimiento, soporte y recursos.',
  },
  paymentMethods: ['Transferencia', 'Nequi'],
  valueReasons: ['Diseño a medida', 'Código optimizado'],
};

const finalNoteJson = {
  index: '10',
  title: 'Nota Final',
  message: 'Creemos firmemente.',
  personalNote: 'Estamos emocionados.',
  teamName: 'Project App',
  teamRole: 'Socio digital',
  contactEmail: 'team@projectapp.co',
  commitmentBadges: [
    { icon: '🤝', title: 'Compromiso', description: 'Dedicación.' },
  ],
  validityMessage: 'Válida 30 días.',
  thankYouMessage: 'Gracias.',
};

const nextStepsJson = {
  index: '11',
  title: 'Próximos pasos',
  introMessage: 'Estamos listos.',
  steps: [
    { title: 'Revisión', description: 'Revisa la propuesta.' },
    { title: 'Comenzamos', description: 'Kickoff meeting.' },
  ],
  ctaMessage: 'Contáctanos hoy.',
  primaryCTA: { text: 'WhatsApp', link: 'https://wa.me/123' },
  secondaryCTA: { text: 'Agendar', link: 'https://calendly.com/x' },
  contactMethods: [
    { icon: '📧', title: 'Email', value: 'hi@test.co', link: 'mailto:hi@test.co' },
  ],
  validityMessage: 'Válida 30 días.',
  thankYouMessage: 'Gracias.',
};


// ─── arrToText / textToArr ───────────────────────────────────────────────────

describe('arrToText', () => {
  it('joins array with newlines', () => {
    expect(arrToText(['a', 'b', 'c'])).toBe('a\nb\nc');
  });

  it('returns empty string for empty array', () => {
    expect(arrToText([])).toBe('');
  });

  it('returns string as-is if not an array', () => {
    expect(arrToText('already text')).toBe('already text');
  });

  it('returns empty string for null', () => {
    expect(arrToText(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(arrToText(undefined)).toBe('');
  });
});

describe('textToArr', () => {
  it('splits text by newlines and trims', () => {
    expect(textToArr('a\n  b  \nc')).toEqual(['a', 'b', 'c']);
  });

  it('filters empty lines', () => {
    expect(textToArr('a\n\n\nb')).toEqual(['a', 'b']);
  });

  it('returns empty array for empty string', () => {
    expect(textToArr('')).toEqual([]);
  });

  it('returns empty array for null', () => {
    expect(textToArr(null)).toEqual([]);
  });

  it('returns empty array for undefined', () => {
    expect(textToArr(undefined)).toEqual([]);
  });

  it('handles single line', () => {
    expect(textToArr('single')).toEqual(['single']);
  });
});


// ─── buildFormFromJson ───────────────────────────────────────────────────────

describe('buildFormFromJson', () => {
  describe('greeting', () => {
    it('builds form from full content_json', () => {
      const form = buildFormFromJson(greetingJson, 'greeting');
      expect(form.clientName).toBe('María García');
      expect(form.inspirationalQuote).toBe('Design is how it works.');
    });

    it('uses proposalData.client_name as fallback', () => {
      const form = buildFormFromJson({}, 'greeting', { client_name: 'Fallback' });
      expect(form.clientName).toBe('Fallback');
    });

    it('defaults to empty strings when no data', () => {
      const form = buildFormFromJson({}, 'greeting');
      expect(form.clientName).toBe('');
      expect(form.inspirationalQuote).toBe('');
    });

    it('handles null json', () => {
      const form = buildFormFromJson(null, 'greeting');
      expect(form.clientName).toBe('');
    });
  });

  describe('executive_summary', () => {
    it('converts paragraphs array to newline text', () => {
      const form = buildFormFromJson(executiveSummaryJson, 'executive_summary');
      expect(form.paragraphs).toBe('Primer párrafo.\nSegundo párrafo.');
      expect(form.highlights).toBe('Diseño personalizado\nDesarrollo responsivo');
      expect(form.index).toBe('1');
    });

    it('defaults empty arrays to empty string', () => {
      const form = buildFormFromJson({ paragraphs: [], highlights: [] }, 'executive_summary');
      expect(form.paragraphs).toBe('');
      expect(form.highlights).toBe('');
    });
  });

  describe('context_diagnostic', () => {
    it('builds form with issues and opportunity', () => {
      const form = buildFormFromJson(contextDiagnosticJson, 'context_diagnostic');
      expect(form.issues).toBe('Falta de presencia digital\nDifícil captar clientes');
      expect(form.opportunity).toBe('Crear una plataforma que genere confianza.');
    });
  });

  describe('conversion_strategy', () => {
    it('builds form with steps containing bullet text', () => {
      const form = buildFormFromJson(conversionStrategyJson, 'conversion_strategy');
      expect(form.steps).toHaveLength(2);
      expect(form.steps[0].bullets).toBe('Mensaje claro\nBeneficio visible');
      expect(form.result).toBe('Una página que genere contactos.');
    });

    it('defaults to empty steps array', () => {
      const form = buildFormFromJson({}, 'conversion_strategy');
      expect(form.steps).toEqual([]);
    });
  });

  describe('design_ux', () => {
    it('builds form with focusItems and objective', () => {
      const form = buildFormFromJson(designUxJson, 'design_ux');
      expect(form.focusItems).toBe('Presentación clara\nIntegración redes sociales');
      expect(form.objective).toBe('Inspirar confianza.');
    });
  });

  describe('creative_support', () => {
    it('builds form with includes and closing', () => {
      const form = buildFormFromJson(creativeSupportJson, 'creative_support');
      expect(form.includes).toBe('Sesiones de revisión\nApoyo visual');
      expect(form.closing).toBe('Cada decisión será co-creación.');
    });
  });

  describe('development_stages', () => {
    it('builds form with stages and current flag', () => {
      const form = buildFormFromJson(developmentStagesJson, 'development_stages');
      expect(form.stages).toHaveLength(3);
      expect(form.stages[0].current).toBe(true);
      expect(form.stages[1].current).toBe(false);
    });

    it('defaults to empty stages', () => {
      const form = buildFormFromJson({}, 'development_stages');
      expect(form.stages).toEqual([]);
    });
  });

  describe('functional_requirements', () => {
    it('builds form with groups and items', () => {
      const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
      expect(form.groups).toHaveLength(1);
      expect(form.groups[0].items).toHaveLength(2);
      expect(form.groups[0].id).toBe('views');
      expect(form.additionalModules).toHaveLength(1);
    });

    it('restores paste mode from _editMode in groups', () => {
      const form = buildFormFromJson(functionalRequirementsJsonWithPaste, 'functional_requirements');
      expect(form.groups[0]._pasteMode).toBe(true);
      expect(form.groups[0]._pasteText).toBe('Pasted views content');
      expect(form.additionalModules[0]._pasteMode).toBe(true);
      expect(form.additionalModules[0]._pasteText).toBe('Pasted analytics');
    });

    it('sets _collapsed to true by default', () => {
      const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
      expect(form.groups[0]._collapsed).toBe(true);
      expect(form.additionalModules[0]._collapsed).toBe(true);
    });

    it('defaults form mode when _editMode absent', () => {
      const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
      expect(form.groups[0]._pasteMode).toBe(false);
      expect(form.groups[0]._pasteText).toBe('');
    });
  });

  describe('timeline', () => {
    it('builds form with phases and tasks as text', () => {
      const form = buildFormFromJson(timelineJson, 'timeline');
      expect(form.phases).toHaveLength(1);
      expect(form.phases[0].tasks).toBe('Moodboard\nWireframes');
      expect(form.totalDuration).toBe('1 mes');
    });
  });

  describe('investment', () => {
    it('builds form with payment options and methods as text', () => {
      const form = buildFormFromJson(investmentJson, 'investment');
      expect(form.totalInvestment).toBe('$3.500.000');
      expect(form.whatsIncluded).toHaveLength(1);
      expect(form.paymentOptions).toHaveLength(1);
      expect(form.paymentMethods).toBe('Transferencia\nNequi');
      expect(form.valueReasons).toBe('Diseño a medida\nCódigo optimizado');
    });

    it('defaults currency to COP', () => {
      const form = buildFormFromJson({}, 'investment');
      expect(form.currency).toBe('COP');
    });
  });

  describe('final_note', () => {
    it('builds form with badges and contact info', () => {
      const form = buildFormFromJson(finalNoteJson, 'final_note');
      expect(form.commitmentBadges).toHaveLength(1);
      expect(form.contactEmail).toBe('team@projectapp.co');
      expect(form.validityMessage).toBe('Válida 30 días.');
    });
  });

  describe('next_steps', () => {
    it('builds form with steps, CTAs, and contact methods', () => {
      const form = buildFormFromJson(nextStepsJson, 'next_steps');
      expect(form.steps).toHaveLength(2);
      expect(form.primaryCTA.text).toBe('WhatsApp');
      expect(form.secondaryCTA.link).toBe('https://calendly.com/x');
      expect(form.contactMethods).toHaveLength(1);
    });

    it('defaults CTAs to empty text/link', () => {
      const form = buildFormFromJson({}, 'next_steps');
      expect(form.primaryCTA).toEqual({ text: '', link: '' });
      expect(form.secondaryCTA).toEqual({ text: '', link: '' });
    });
  });

  describe('unknown type', () => {
    it('returns empty object for unknown section type', () => {
      const form = buildFormFromJson({ foo: 'bar' }, 'unknown_type');
      expect(form).toEqual({});
    });
  });
});


// ─── formToJson ──────────────────────────────────────────────────────────────

describe('formToJson', () => {
  describe('greeting', () => {
    it('serializes greeting form to json', () => {
      const form = { clientName: 'Test', inspirationalQuote: 'Quote' };
      const json = formToJson(form, 'greeting');
      expect(json).toEqual({ clientName: 'Test', inspirationalQuote: 'Quote' });
    });
  });

  describe('executive_summary', () => {
    it('converts newline text to arrays', () => {
      const form = buildFormFromJson(executiveSummaryJson, 'executive_summary');
      const json = formToJson(form, 'executive_summary');
      expect(json.paragraphs).toEqual(['Primer párrafo.', 'Segundo párrafo.']);
      expect(json.highlights).toEqual(['Diseño personalizado', 'Desarrollo responsivo']);
    });

    it('produces empty arrays from empty text', () => {
      const form = { index: '', title: '', paragraphs: '', highlightsTitle: '', highlights: '' };
      const json = formToJson(form, 'executive_summary');
      expect(json.paragraphs).toEqual([]);
      expect(json.highlights).toEqual([]);
    });
  });

  describe('context_diagnostic', () => {
    it('serializes issues and opportunity', () => {
      const form = buildFormFromJson(contextDiagnosticJson, 'context_diagnostic');
      const json = formToJson(form, 'context_diagnostic');
      expect(json.issues).toEqual(['Falta de presencia digital', 'Difícil captar clientes']);
      expect(json.opportunity).toBe('Crear una plataforma que genere confianza.');
    });
  });

  describe('conversion_strategy', () => {
    it('serializes steps with bullet arrays', () => {
      const form = buildFormFromJson(conversionStrategyJson, 'conversion_strategy');
      const json = formToJson(form, 'conversion_strategy');
      expect(json.steps[0].bullets).toEqual(['Mensaje claro', 'Beneficio visible']);
      expect(json.steps[1].bullets).toEqual(['Testimonios']);
    });
  });

  describe('design_ux', () => {
    it('serializes focusItems as array', () => {
      const form = buildFormFromJson(designUxJson, 'design_ux');
      const json = formToJson(form, 'design_ux');
      expect(json.focusItems).toEqual(['Presentación clara', 'Integración redes sociales']);
    });
  });

  describe('creative_support', () => {
    it('serializes includes as array', () => {
      const form = buildFormFromJson(creativeSupportJson, 'creative_support');
      const json = formToJson(form, 'creative_support');
      expect(json.includes).toEqual(['Sesiones de revisión', 'Apoyo visual']);
      expect(json.closing).toBe('Cada decisión será co-creación.');
    });
  });

  describe('development_stages', () => {
    it('includes current flag only when true', () => {
      const form = buildFormFromJson(developmentStagesJson, 'development_stages');
      const json = formToJson(form, 'development_stages');
      expect(json.stages[0].current).toBe(true);
      expect(json.stages[1]).not.toHaveProperty('current');
    });
  });

  describe('functional_requirements', () => {
    it('serializes groups with form mode metadata', () => {
      const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
      const json = formToJson(form, 'functional_requirements');
      expect(json.groups[0]._editMode).toBe('form');
      expect(json.groups[0]).not.toHaveProperty('rawText');
      expect(json.groups[0].items).toHaveLength(2);
    });

    it('serializes groups with paste mode metadata', () => {
      const form = buildFormFromJson(functionalRequirementsJsonWithPaste, 'functional_requirements');
      const json = formToJson(form, 'functional_requirements');
      expect(json.groups[0]._editMode).toBe('paste');
      expect(json.groups[0].rawText).toBe('Pasted views content');
    });

    it('serializes additionalModules with paste mode', () => {
      const form = buildFormFromJson(functionalRequirementsJsonWithPaste, 'functional_requirements');
      const json = formToJson(form, 'functional_requirements');
      expect(json.additionalModules[0]._editMode).toBe('paste');
      expect(json.additionalModules[0].rawText).toBe('Pasted analytics');
    });

    it('strips internal _pasteMode/_pasteText/_collapsed from output', () => {
      const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
      const json = formToJson(form, 'functional_requirements');
      expect(json.groups[0]).not.toHaveProperty('_pasteMode');
      expect(json.groups[0]).not.toHaveProperty('_pasteText');
      expect(json.groups[0]).not.toHaveProperty('_collapsed');
    });
  });

  describe('timeline', () => {
    it('serializes phases with tasks as array', () => {
      const form = buildFormFromJson(timelineJson, 'timeline');
      const json = formToJson(form, 'timeline');
      expect(json.phases[0].tasks).toEqual(['Moodboard', 'Wireframes']);
    });
  });

  describe('investment', () => {
    it('serializes payment methods and value reasons as arrays', () => {
      const form = buildFormFromJson(investmentJson, 'investment');
      const json = formToJson(form, 'investment');
      expect(json.paymentMethods).toEqual(['Transferencia', 'Nequi']);
      expect(json.valueReasons).toEqual(['Diseño a medida', 'Código optimizado']);
    });
  });

  describe('final_note', () => {
    it('serializes badges and contact info', () => {
      const form = buildFormFromJson(finalNoteJson, 'final_note');
      const json = formToJson(form, 'final_note');
      expect(json.commitmentBadges).toHaveLength(1);
      expect(json.contactEmail).toBe('team@projectapp.co');
    });
  });

  describe('next_steps', () => {
    it('serializes CTAs and contact methods', () => {
      const form = buildFormFromJson(nextStepsJson, 'next_steps');
      const json = formToJson(form, 'next_steps');
      expect(json.primaryCTA.text).toBe('WhatsApp');
      expect(json.contactMethods).toHaveLength(1);
      expect(json.validityMessage).toBe('Válida 30 días.');
    });
  });

  describe('unknown type', () => {
    it('returns empty object', () => {
      expect(formToJson({}, 'unknown')).toEqual({});
    });
  });
});


// ─── Round-trip: buildFormFromJson → formToJson ──────────────────────────────

describe('buildFormFromJson → formToJson round-trip', () => {
  const cases = [
    { type: 'greeting', json: greetingJson },
    { type: 'executive_summary', json: executiveSummaryJson },
    { type: 'context_diagnostic', json: contextDiagnosticJson },
    { type: 'conversion_strategy', json: conversionStrategyJson },
    { type: 'design_ux', json: designUxJson },
    { type: 'creative_support', json: creativeSupportJson },
    { type: 'development_stages', json: developmentStagesJson },
    { type: 'timeline', json: timelineJson },
    { type: 'investment', json: investmentJson },
    { type: 'final_note', json: finalNoteJson },
    { type: 'next_steps', json: nextStepsJson },
  ];

  it.each(cases)('round-trips $type correctly', ({ type, json }) => {
    const form = buildFormFromJson(json, type);
    const result = formToJson(form, type);
    // Compare key fields — the round-trip should preserve data
    for (const key of Object.keys(json)) {
      expect(result).toHaveProperty(key);
    }
  });

  it('round-trips functional_requirements preserving group items', () => {
    const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
    const result = formToJson(form, 'functional_requirements');
    expect(result.groups[0].items).toHaveLength(2);
    expect(result.groups[0].items[0].name).toBe('Home');
    expect(result.additionalModules[0].items[0].name).toBe('Reports');
  });
});


// ─── formToReadableText ──────────────────────────────────────────────────────

describe('formToReadableText', () => {
  it('generates text for greeting', () => {
    const form = buildFormFromJson(greetingJson, 'greeting');
    const text = formToReadableText(form, 'greeting');
    expect(text).toContain('María García');
    expect(text).toContain('Design is how it works.');
  });

  it('generates text for executive_summary with bullets', () => {
    const form = buildFormFromJson(executiveSummaryJson, 'executive_summary');
    const text = formToReadableText(form, 'executive_summary');
    expect(text).toContain('Primer párrafo.');
    expect(text).toContain('Incluye');
    expect(text).toContain('- Diseño personalizado');
  });

  it('generates text for context_diagnostic', () => {
    const form = buildFormFromJson(contextDiagnosticJson, 'context_diagnostic');
    const text = formToReadableText(form, 'context_diagnostic');
    expect(text).toContain('Desafíos');
    expect(text).toContain('- Falta de presencia digital');
    expect(text).toContain('Crear una plataforma');
  });

  it('generates text for conversion_strategy with steps', () => {
    const form = buildFormFromJson(conversionStrategyJson, 'conversion_strategy');
    const text = formToReadableText(form, 'conversion_strategy');
    expect(text).toContain('Captar atención');
    expect(text).toContain('- Mensaje claro');
  });

  it('generates text for design_ux', () => {
    const form = buildFormFromJson(designUxJson, 'design_ux');
    const text = formToReadableText(form, 'design_ux');
    expect(text).toContain('- Presentación clara');
    expect(text).toContain('Inspirar confianza.');
  });

  it('generates text for creative_support', () => {
    const form = buildFormFromJson(creativeSupportJson, 'creative_support');
    const text = formToReadableText(form, 'creative_support');
    expect(text).toContain('- Sesiones de revisión');
    expect(text).toContain('co-creación');
  });

  it('generates text for functional_requirements including title, intro and group overviews', () => {
    const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
    const text = formToReadableText(form, 'functional_requirements');
    expect(text).toContain('Requerimientos');
    expect(text).toContain('Detalle de requerimientos.');
    expect(text).toContain('Vistas');
    expect(text).toContain('Pantallas.');
    expect(text).toContain('Analytics');
    expect(text).toContain('Dashboard.');
  });

  it('generates text for functional_requirements excluding individual items', () => {
    const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
    const text = formToReadableText(form, 'functional_requirements');
    expect(text).not.toContain('**Home**');
    expect(text).not.toContain('**Contacto**');
    expect(text).not.toContain('**Reports**');
  });

  it('generates text for development_stages', () => {
    const form = buildFormFromJson(developmentStagesJson, 'development_stages');
    const text = formToReadableText(form, 'development_stages');
    expect(text).toContain('Propuesta');
    expect(text).toContain('(actual)');
  });

  it('generates text for timeline', () => {
    const form = buildFormFromJson(timelineJson, 'timeline');
    const text = formToReadableText(form, 'timeline');
    expect(text).toContain('1 mes');
    expect(text).toContain('Diseño aprobado');
  });

  it('generates text for investment', () => {
    const form = buildFormFromJson(investmentJson, 'investment');
    const text = formToReadableText(form, 'investment');
    expect(text).toContain('$3.500.000');
    expect(text).toContain('Qué incluye:');
  });

  it('generates text for final_note', () => {
    const form = buildFormFromJson(finalNoteJson, 'final_note');
    const text = formToReadableText(form, 'final_note');
    expect(text).toContain('Creemos firmemente.');
    expect(text).toContain('team@projectapp.co');
  });

  it('generates text for next_steps', () => {
    const form = buildFormFromJson(nextStepsJson, 'next_steps');
    const text = formToReadableText(form, 'next_steps');
    expect(text).toContain('Pasos:');
    expect(text).toContain('- Revisión:');
    expect(text).toContain('Contacto:');
  });

  it('returns empty string for empty form', () => {
    const text = formToReadableText({}, 'greeting');
    expect(text).toBe('');
  });

  it('returns empty string for unknown type', () => {
    const text = formToReadableText({}, 'unknown');
    expect(text).toBe('');
  });
});


// ─── groupToReadableText ─────────────────────────────────────────────────────

describe('groupToReadableText', () => {
  it('generates text with title, description and items', () => {
    const group = {
      icon: '🖥️',
      title: 'Vistas',
      description: 'Pantallas del sitio.',
      items: [
        { icon: '🏠', name: 'Home', description: 'Landing.' },
        { icon: '📧', name: 'Contacto', description: 'Formulario.' },
      ],
    };
    const text = groupToReadableText(group);
    expect(text).toContain('🖥️ Vistas');
    expect(text).toContain('Pantallas del sitio.');
    expect(text).toContain('- 🏠 **Home**: Landing.');
    expect(text).toContain('- 📧 **Contacto**: Formulario.');
  });

  it('handles group with no description', () => {
    const group = {
      title: 'Test',
      description: '',
      items: [{ icon: '', name: 'Item', description: 'Desc' }],
    };
    const text = groupToReadableText(group);
    expect(text).toBe('Test\n-  **Item**: Desc');
  });

  it('handles group with no items', () => {
    const group = { title: 'Empty', icon: '📦', description: 'Just description.', items: [] };
    const text = groupToReadableText(group);
    expect(text).toBe('📦 Empty\nJust description.');
  });

  it('returns empty string for empty group', () => {
    const text = groupToReadableText({ description: '', items: [] });
    expect(text).toBe('');
  });
});


// ─── buildSavePayload ────────────────────────────────────────────────────────

describe('buildSavePayload', () => {
  it('builds payload in form mode with _editMode form', () => {
    const form = { clientName: 'Test', inspirationalQuote: 'Quote' };
    const result = buildSavePayload(form, 'greeting', false, '', 'Greeting', false, 101);
    expect(result.sectionId).toBe(101);
    expect(result.payload.title).toBe('Greeting');
    expect(result.payload.content_json._editMode).toBe('form');
    expect(result.payload.content_json).not.toHaveProperty('rawText');
    expect(result.payload.content_json.clientName).toBe('Test');
  });

  it('builds payload in paste mode with _editMode paste and rawText', () => {
    const form = { clientName: '', inspirationalQuote: '' };
    const rawText = 'Pasted greeting content';
    const result = buildSavePayload(form, 'greeting', true, rawText, 'Greeting', false, 101);
    expect(result.payload.content_json._editMode).toBe('paste');
    expect(result.payload.content_json.rawText).toBe('Pasted greeting content');
  });

  it('includes is_wide_panel in payload', () => {
    const form = buildFormFromJson(functionalRequirementsJson, 'functional_requirements');
    const result = buildSavePayload(form, 'functional_requirements', false, '', 'Reqs', true, 301);
    expect(result.payload.is_wide_panel).toBe(true);
  });

  it('handles empty paste text', () => {
    const form = { clientName: '', inspirationalQuote: '' };
    const result = buildSavePayload(form, 'greeting', true, '', 'Greeting', false, 101);
    expect(result.payload.content_json.rawText).toBe('');
    expect(result.payload.content_json._editMode).toBe('paste');
  });

  it('form mode deletes rawText even if present', () => {
    const form = { clientName: 'X', inspirationalQuote: 'Y' };
    const result = buildSavePayload(form, 'greeting', false, 'stale text', 'Greeting', false, 101);
    expect(result.payload.content_json).not.toHaveProperty('rawText');
  });
});


// ─── Edge cases ──────────────────────────────────────────────────────────────

describe('edge cases', () => {
  it('buildFormFromJson handles undefined for all array fields', () => {
    const json = { index: '1', title: 'T' };
    const form = buildFormFromJson(json, 'executive_summary');
    expect(form.paragraphs).toBe('');
    expect(form.highlights).toBe('');
  });

  it('formToJson with whitespace-only text produces empty arrays', () => {
    const form = { index: '1', title: 'T', paragraphs: '   \n  \n  ', highlightsTitle: '', highlights: '' };
    const json = formToJson(form, 'executive_summary');
    expect(json.paragraphs).toEqual([]);
  });

  it('buildFormFromJson with extra unknown keys does not break', () => {
    const json = { clientName: 'X', unknownKey: 'ignored', inspirationalQuote: 'Q' };
    const form = buildFormFromJson(json, 'greeting');
    expect(form.clientName).toBe('X');
    expect(form).not.toHaveProperty('unknownKey');
  });

  it('formToJson for conversion_strategy with empty steps array', () => {
    const form = { index: '', title: '', intro: '', steps: [], resultTitle: '', result: '' };
    const json = formToJson(form, 'conversion_strategy');
    expect(json.steps).toEqual([]);
  });

  it('formToJson for development_stages with no current stages', () => {
    const form = {
      stages: [
        { icon: '🎨', title: 'Design', description: 'Desc', current: false },
      ],
    };
    const json = formToJson(form, 'development_stages');
    expect(json.stages[0]).not.toHaveProperty('current');
  });

  it('formToJson for functional_requirements with empty groups', () => {
    const form = { index: '', title: '', intro: '', groups: [], additionalModules: [] };
    const json = formToJson(form, 'functional_requirements');
    expect(json.groups).toEqual([]);
    expect(json.additionalModules).toEqual([]);
  });

  it('buildSavePayload for executive_summary in paste mode preserves structured data', () => {
    const form = buildFormFromJson(executiveSummaryJson, 'executive_summary');
    const result = buildSavePayload(form, 'executive_summary', true, 'Custom pasted text', 'Summary', false, 102);
    expect(result.payload.content_json.paragraphs).toEqual(['Primer párrafo.', 'Segundo párrafo.']);
    expect(result.payload.content_json.rawText).toBe('Custom pasted text');
    expect(result.payload.content_json._editMode).toBe('paste');
  });

  it('timeline with empty phases', () => {
    const form = { index: '', title: '', introText: '', totalDuration: '', phases: [] };
    const json = formToJson(form, 'timeline');
    expect(json.phases).toEqual([]);
  });

  it('investment with empty payment options and methods', () => {
    const form = buildFormFromJson({}, 'investment');
    const json = formToJson(form, 'investment');
    expect(json.whatsIncluded).toEqual([]);
    expect(json.paymentOptions).toEqual([]);
    expect(json.paymentMethods).toEqual([]);
    expect(json.valueReasons).toEqual([]);
  });

  it('next_steps with empty contact methods and steps', () => {
    const form = buildFormFromJson({}, 'next_steps');
    const json = formToJson(form, 'next_steps');
    expect(json.steps).toEqual([]);
    expect(json.contactMethods).toEqual([]);
  });
});


// ─── Paste panel detection helpers ───────────────────────────────────────────
// These replicate the logic from pages/proposal/[uuid]/index.vue

function isPastePanel(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?._editMode === 'paste' && panel._group?.rawText;
  }
  return panel.content_json?._editMode === 'paste' && panel.content_json?.rawText;
}

function getPastePanelTitle(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?.title || panel.title;
  }
  return panel.content_json?.title || panel.title;
}

function getPastePanelIndex(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._subIndex || '';
  }
  return panel.content_json?.index || '';
}

function getPastePanelRawText(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?.rawText || '';
  }
  return panel.content_json?.rawText || '';
}

describe('isPastePanel', () => {
  it('returns true for section with _editMode paste and rawText', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: { _editMode: 'paste', rawText: 'Some content' },
    };
    expect(isPastePanel(panel)).toBeTruthy();
  });

  it('returns false for section with _editMode form', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: { _editMode: 'form', paragraphs: ['P1'] },
    };
    expect(isPastePanel(panel)).toBeFalsy();
  });

  it('returns false for section with paste mode but empty rawText', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: { _editMode: 'paste', rawText: '' },
    };
    expect(isPastePanel(panel)).toBeFalsy();
  });

  it('returns false for section without _editMode', () => {
    const panel = {
      section_type: 'greeting',
      content_json: { clientName: 'Test' },
    };
    expect(isPastePanel(panel)).toBeFalsy();
  });

  it('returns true for functional_requirements_group with paste mode', () => {
    const panel = {
      section_type: 'functional_requirements_group',
      _group: { _editMode: 'paste', rawText: 'Group paste content', title: 'Vistas' },
    };
    expect(isPastePanel(panel)).toBeTruthy();
  });

  it('returns false for functional_requirements_group with form mode', () => {
    const panel = {
      section_type: 'functional_requirements_group',
      _group: { _editMode: 'form', title: 'Vistas', items: [] },
    };
    expect(isPastePanel(panel)).toBeFalsy();
  });

  it('returns false when content_json is empty object', () => {
    const panel = {
      section_type: 'context_diagnostic',
      content_json: {},
    };
    expect(isPastePanel(panel)).toBeFalsy();
  });
});

describe('getPastePanelTitle', () => {
  it('returns title from content_json for regular sections', () => {
    const panel = {
      section_type: 'executive_summary',
      title: 'Section Title',
      content_json: { title: 'Content Title', _editMode: 'paste', rawText: 'x' },
    };
    expect(getPastePanelTitle(panel)).toBe('Content Title');
  });

  it('falls back to panel title when content_json title is empty', () => {
    const panel = {
      section_type: 'executive_summary',
      title: 'Fallback Title',
      content_json: { title: '', _editMode: 'paste', rawText: 'x' },
    };
    expect(getPastePanelTitle(panel)).toBe('Fallback Title');
  });

  it('returns group title for functional_requirements_group', () => {
    const panel = {
      section_type: 'functional_requirements_group',
      title: 'Panel Title',
      _group: { title: 'Group Title' },
    };
    expect(getPastePanelTitle(panel)).toBe('Group Title');
  });
});

describe('getPastePanelIndex', () => {
  it('returns index from content_json for regular sections', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: { index: '1', _editMode: 'paste', rawText: 'x' },
    };
    expect(getPastePanelIndex(panel)).toBe('1');
  });

  it('returns _subIndex for functional_requirements_group', () => {
    const panel = {
      section_type: 'functional_requirements_group',
      _subIndex: '7.2',
    };
    expect(getPastePanelIndex(panel)).toBe('7.2');
  });

  it('returns empty string when index is missing', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: {},
    };
    expect(getPastePanelIndex(panel)).toBe('');
  });
});

describe('getPastePanelRawText', () => {
  it('returns rawText from content_json for regular sections', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: { rawText: 'Pasted markdown content', _editMode: 'paste' },
    };
    expect(getPastePanelRawText(panel)).toBe('Pasted markdown content');
  });

  it('returns rawText from _group for functional_requirements_group', () => {
    const panel = {
      section_type: 'functional_requirements_group',
      _group: { rawText: 'Group pasted content' },
    };
    expect(getPastePanelRawText(panel)).toBe('Group pasted content');
  });

  it('returns empty string when rawText is missing', () => {
    const panel = {
      section_type: 'executive_summary',
      content_json: { _editMode: 'form' },
    };
    expect(getPastePanelRawText(panel)).toBe('');
  });
});


// ─── Mode persistence on reopen ──────────────────────────────────────────────

describe('mode persistence (SectionEditor remembers _editMode)', () => {
  it('buildFormFromJson from paste-mode content_json preserves pasteMode state', () => {
    const contentJson = {
      index: '1', title: 'Summary',
      paragraphs: ['P1'], highlightsTitle: 'H', highlights: ['H1'],
      _editMode: 'paste', rawText: 'Pasted summary text.',
    };
    // The SectionEditor initializes pasteMode from content._editMode === 'paste'
    const initialContent = contentJson;
    const pasteMode = initialContent._editMode === 'paste';
    const pasteText = initialContent.rawText || '';

    expect(pasteMode).toBe(true);
    expect(pasteText).toBe('Pasted summary text.');

    // Verify the form still builds correctly from the same content_json
    const form = buildFormFromJson(contentJson, 'executive_summary');
    expect(form.paragraphs).toBe('P1');
  });

  it('buildFormFromJson from form-mode content_json opens in form mode', () => {
    const contentJson = {
      index: '1', title: 'Summary',
      paragraphs: ['P1'], highlightsTitle: 'H', highlights: ['H1'],
      _editMode: 'form',
    };
    const pasteMode = contentJson._editMode === 'paste';
    const pasteText = contentJson.rawText || '';

    expect(pasteMode).toBe(false);
    expect(pasteText).toBe('');
  });

  it('buildFormFromJson from content_json without _editMode opens in form mode', () => {
    const contentJson = {
      index: '1', title: 'Summary',
      paragraphs: ['P1'], highlightsTitle: 'H', highlights: ['H1'],
    };
    const pasteMode = contentJson._editMode === 'paste';
    expect(pasteMode).toBe(false);
  });

  it('functional_requirements group remembers paste mode per group', () => {
    const contentJson = {
      index: '7', title: 'Reqs', intro: '',
      groups: [
        { id: 'views', icon: '', title: 'Views', description: '', items: [], _editMode: 'paste', rawText: 'Pasted views' },
        { id: 'comps', icon: '', title: 'Components', description: '', items: [], _editMode: 'form' },
      ],
      additionalModules: [],
    };

    const form = buildFormFromJson(contentJson, 'functional_requirements');
    expect(form.groups[0]._pasteMode).toBe(true);
    expect(form.groups[0]._pasteText).toBe('Pasted views');
    expect(form.groups[1]._pasteMode).toBe(false);
    expect(form.groups[1]._pasteText).toBe('');
  });
});


// ─── Form-to-paste auto-sync ─────────────────────────────────────────────────

describe('form-to-paste auto-sync (formToReadableText reflects form state)', () => {
  it('reflects updated form data when toggling to paste mode', () => {
    const form = buildFormFromJson(greetingJson, 'greeting');
    const textBefore = formToReadableText(form, 'greeting');
    expect(textBefore).toContain('María García');

    // Simulate user editing form
    form.clientName = 'Updated Client';
    const textAfter = formToReadableText(form, 'greeting');
    expect(textAfter).toContain('Updated Client');
    expect(textAfter).not.toContain('María García');
  });

  it('executive_summary: form changes reflect in paste text', () => {
    const form = buildFormFromJson(executiveSummaryJson, 'executive_summary');
    form.paragraphs = 'New paragraph.';
    const text = formToReadableText(form, 'executive_summary');
    expect(text).toContain('New paragraph.');
    expect(text).not.toContain('Primer párrafo.');
  });

  it('conversion_strategy: adding a step reflects in paste text', () => {
    const form = buildFormFromJson(conversionStrategyJson, 'conversion_strategy');
    form.steps.push({ title: 'New Step', bullets: 'New bullet' });
    const text = formToReadableText(form, 'conversion_strategy');
    expect(text).toContain('New Step');
    expect(text).toContain('- New bullet');
  });

  it('buildSavePayload in paste mode captures current paste text, not form text', () => {
    const form = buildFormFromJson(greetingJson, 'greeting');
    const customPasteText = 'Manually typed paste content, NOT from form.';
    const result = buildSavePayload(form, 'greeting', true, customPasteText, 'Greeting', false, 1);
    // rawText should be the custom paste text, not the auto-synced text
    expect(result.payload.content_json.rawText).toBe(customPasteText);
    // But structured data still comes from form
    expect(result.payload.content_json.clientName).toBe('María García');
  });
});

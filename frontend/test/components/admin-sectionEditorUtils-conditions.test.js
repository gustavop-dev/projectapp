/**
 * Tests for sectionEditorUtils — value_added conditions + commercial_conditions
 * roundtrip (Req 3 + Req 1/2 panel editing).
 */
import {
  buildFormFromJson,
  formToJson,
} from '../../components/BusinessProposal/admin/sectionEditorUtils.js';

describe('value_added_modules conditions roundtrip', () => {
  const json = {
    index: '11',
    title: 'Incluido',
    intro: 'intro',
    module_ids: ['ai_automation_module'],
    justifications: { ai_automation_module: 'j' },
    conditions: {
      ai_automation_module: {
        min_price_usd: 2900,
        min_price_cop: 10400000,
        duration_months: 6,
        discretionary_note: 'si aplica',
        terms: 'Depende del asistente.',
      },
    },
    footer_note: 'nota',
  };

  it('buildFormFromJson keeps conditions for referenced ids', () => {
    const form = buildFormFromJson(json, 'value_added_modules', {});
    expect(form.conditions.ai_automation_module.duration_months).toBe(6);
    expect(form.conditions.ai_automation_module.terms).toBe('Depende del asistente.');
  });

  it('formToJson serializes non-empty conditions and prunes empty ones', () => {
    const form = buildFormFromJson(json, 'value_added_modules', {});
    // Add an empty condition for a second id → should be pruned.
    form.module_ids.push('admin_module');
    form.conditions.admin_module = {
      min_price_usd: null, min_price_cop: null, duration_months: null,
      discretionary_note: '', terms: '',
    };
    const out = formToJson(form, 'value_added_modules');
    expect(out.conditions.ai_automation_module.min_price_cop).toBe(10400000);
    expect(out.conditions.admin_module).toBeUndefined();
  });
});

describe('commercial_conditions roundtrip', () => {
  const json = {
    index: '17',
    title: 'Condiciones comerciales',
    packagesTitle: 'Paquetes',
    packagesIntro: 'intro',
    hourlyRate: 90000,
    currency: 'COP',
    packages: [
      { name: 'Ágil', hours: 20, discountPercent: 0, note: 'x' },
      { name: 'Pro', hours: 60, discountPercent: 10, note: 'y' },
    ],
    effortBadge: 'Esfuerzo medio aparte',
    scopeTitle: 'Alcance',
    scopeParagraphs: ['p1', 'p2'],
  };

  it('builds a form with textarea-joined scope paragraphs', () => {
    const form = buildFormFromJson(json, 'commercial_conditions', { currency: 'COP' });
    expect(form.packages).toHaveLength(2);
    expect(form.hourlyRate).toBe(90000);
    expect(form.scopeParagraphs).toContain('p1');
    expect(form.scopeParagraphs).toContain('p2');
  });

  it('formToJson coerces numerics and splits scope paragraphs back to an array', () => {
    const form = buildFormFromJson(json, 'commercial_conditions', { currency: 'COP' });
    // Simulate admin text edits (strings from inputs).
    form.hourlyRate = '80000';
    form.packages[0].hours = '25';
    const out = formToJson(form, 'commercial_conditions');
    expect(out.hourlyRate).toBe(80000);
    expect(out.packages[0].hours).toBe(25);
    expect(Array.isArray(out.scopeParagraphs)).toBe(true);
    expect(out.scopeParagraphs).toEqual(['p1', 'p2']);
  });
});

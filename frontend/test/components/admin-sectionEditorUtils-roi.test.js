/**
 * Tests for the ``roi_projection`` cases in sectionEditorUtils.js.
 *
 * Covers: form ↔ JSON round-trip, empty-row filtering on save, the
 * methodology / per-scenario assumptions / per-metric basis fields, and the
 * paste-mode readable text generation.
 */
import {
  buildFormFromJson,
  formToJson,
  formToReadableText,
} from '../../components/BusinessProposal/admin/sectionEditorUtils';

const SAMPLE_JSON = {
  index: '4',
  title: '📈 Proyección de retorno',
  subtitle: 'Lo que esta inversión genera.',
  methodology: 'Partimos del tráfico esperado del mercado local; de cada 100 visitas 3 agendan; proyectamos a 12 meses.',
  kpis: [
    { icon: '👁️', value: '90K', label: 'Visualizaciones', sublabel: 'mes 6', source: 'Benchmark' },
    { icon: '🏪', value: '$34M', label: 'MRR mes 6', sublabel: '', source: '' },
  ],
  scenariosTitle: 'Escenarios proyectados al primer año',
  scenarios: [
    {
      name: 'realistic', label: 'Realista', icon: '🎯',
      assumptions: ['Tráfico orgánico del mercado local', '3 de cada 100 visitas agendan'],
      metrics: [
        { label: 'MAU', value: '80K' },
        { label: 'Total año 1', value: '$280M', basis: '≈ 6.500 clientes × $43.000 ticket promedio', emphasis: true },
      ],
    },
  ],
  ctaNote: 'Cubre la inversión.',
};


describe('sectionEditorUtils — roi_projection', () => {
  it('buildFormFromJson exposes all fields with safe defaults', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    expect(form.index).toBe('4');
    expect(form.title).toBe('📈 Proyección de retorno');
    expect(form.subtitle).toBe('Lo que esta inversión genera.');
    expect(form.methodology).toContain('Partimos del tráfico');
    expect(form.kpis).toHaveLength(2);
    expect(form.kpis[0]).toEqual({
      icon: '👁️', value: '90K', label: 'Visualizaciones',
      sublabel: 'mes 6', source: 'Benchmark',
    });
    expect(form.scenarios).toHaveLength(1);
    expect(form.scenarios[0].assumptions).toEqual([
      'Tráfico orgánico del mercado local', '3 de cada 100 visitas agendan',
    ]);
    expect(form.scenarios[0].metrics[1].basis).toBe('≈ 6.500 clientes × $43.000 ticket promedio');
    expect(form.scenarios[0].metrics[1].emphasis).toBe(true);
    expect(form.scenarios[0].metrics[0].basis).toBe('');
    expect(form.scenariosTitle).toBe('Escenarios proyectados al primer año');
    expect(form.ctaNote).toBe('Cubre la inversión.');
  });

  it('buildFormFromJson on empty JSON returns empty arrays (no crashes downstream)', () => {
    const form = buildFormFromJson({}, 'roi_projection');
    expect(form.methodology).toBe('');
    expect(form.kpis).toEqual([]);
    expect(form.scenarios).toEqual([]);
    expect(form.ctaNote).toBe('');
  });

  it('round-trip: formToJson(buildFormFromJson(json)) preserves shape', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    const back = formToJson(form, 'roi_projection');
    expect(back).toEqual(SAMPLE_JSON);
  });

  it('formToJson filters KPIs that have no value or label', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    form.kpis.push({ icon: '', value: '', label: '', sublabel: '', source: '' });
    const back = formToJson(form, 'roi_projection');
    expect(back.kpis).toHaveLength(2); // empty row dropped
  });

  it('formToJson filters scenarios that have no label/name and no metrics', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    form.scenarios.push({ name: '', label: '', icon: '', assumptions: [], metrics: [] });
    const back = formToJson(form, 'roi_projection');
    expect(back.scenarios).toHaveLength(1);
  });

  it('formToJson omits emphasis flag when false (keeps payload tidy)', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    form.scenarios[0].metrics[0].emphasis = false;
    const back = formToJson(form, 'roi_projection');
    // First metric had no emphasis originally; serialized object must not contain the key.
    expect('emphasis' in back.scenarios[0].metrics[0]).toBe(false);
    // Second metric had emphasis: true; serialized object must keep it.
    expect(back.scenarios[0].metrics[1].emphasis).toBe(true);
  });

  it('formToJson drops empty metric rows inside a scenario', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    form.scenarios[0].metrics.push({ label: '', value: '', basis: '', emphasis: false });
    const back = formToJson(form, 'roi_projection');
    expect(back.scenarios[0].metrics).toHaveLength(2);
  });

  it('formToJson filters blank assumptions and omits empty basis', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    form.scenarios[0].assumptions.push('   ');
    form.scenarios[0].assumptions.push('Inversión sostenida en canales');
    form.scenarios[0].metrics[0].basis = '   ';
    const back = formToJson(form, 'roi_projection');
    expect(back.scenarios[0].assumptions).toEqual([
      'Tráfico orgánico del mercado local',
      '3 de cada 100 visitas agendan',
      'Inversión sostenida en canales',
    ]);
    expect('basis' in back.scenarios[0].metrics[0]).toBe(false);
    expect(back.scenarios[0].metrics[1].basis).toBe('≈ 6.500 clientes × $43.000 ticket promedio');
  });

  it('formToReadableText produces a structured paste-mode summary', () => {
    const form = buildFormFromJson(SAMPLE_JSON, 'roi_projection');
    const text = formToReadableText(form, 'roi_projection');
    expect(text).toContain('Lo que esta inversión genera.');
    expect(text).toContain('Cómo calculamos esto:');
    expect(text).toContain('KPIs:');
    expect(text).toContain('90K — Visualizaciones');
    expect(text).toContain('Realista');
    expect(text).toContain('- 3 de cada 100 visitas agendan');
    expect(text).toContain('Total año 1: $280M (≈ 6.500 clientes × $43.000 ticket promedio)');
    expect(text).toContain('Cubre la inversión.');
  });
});

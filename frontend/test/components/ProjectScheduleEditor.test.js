/**
 * Tests for ProjectScheduleEditor logic.
 *
 * Following project convention (see ProposalEmailsTab.test.js): the component
 * itself is mostly bindings + a single decision tree (form validation +
 * derived stage list). We extract those pure functions here so they can be
 * tested without mounting Vue. The composable `useStageStatus` covers the
 * status-computation logic separately in test/composables/useStageStatus.test.js.
 */

// ── editableStages: derive the list of two stages, falling back to placeholders ─

const STAGE_DEFAULTS = [
  { stage_key: 'design', stage_label: 'Diseño', order: 0 },
  { stage_key: 'development', stage_label: 'Desarrollo', order: 1 },
];

function deriveEditableStages(proposal) {
  const existing = proposal?.project_stages || [];
  return STAGE_DEFAULTS.map((def) => {
    const found = existing.find((s) => s.stage_key === def.stage_key);
    return found
      ? { ...found, stage_label: found.stage_label || def.stage_label }
      : { ...def, completed_at: null, start_date: null, end_date: null };
  });
}

describe('ProjectScheduleEditor.deriveEditableStages', () => {
  it('returns two placeholder stages when proposal has none', () => {
    const stages = deriveEditableStages({});
    expect(stages).toHaveLength(2);
    expect(stages[0].stage_key).toBe('design');
    expect(stages[1].stage_key).toBe('development');
    expect(stages[0].start_date).toBeNull();
  });

  it('returns the existing stages when both are present', () => {
    const proposal = {
      project_stages: [
        { id: 1, stage_key: 'design', start_date: '2026-04-01', end_date: '2026-04-15', completed_at: null },
        { id: 2, stage_key: 'development', start_date: '2026-04-16', end_date: '2026-04-30', completed_at: null },
      ],
    };
    const stages = deriveEditableStages(proposal);
    expect(stages[0].id).toBe(1);
    expect(stages[1].id).toBe(2);
    expect(stages[0].start_date).toBe('2026-04-01');
  });

  it('fills in placeholder for the missing stage when only one exists', () => {
    const proposal = {
      project_stages: [
        { id: 1, stage_key: 'design', start_date: '2026-04-01', end_date: '2026-04-15' },
      ],
    };
    const stages = deriveEditableStages(proposal);
    expect(stages[0].id).toBe(1);
    expect(stages[1].stage_key).toBe('development');
    expect(stages[1].id).toBeUndefined();
    expect(stages[1].start_date).toBeNull();
  });

  it('preserves the existing stage_label when present', () => {
    const proposal = {
      project_stages: [
        { id: 1, stage_key: 'design', stage_label: 'Etapa de Diseño UI' },
      ],
    };
    const stages = deriveEditableStages(proposal);
    expect(stages[0].stage_label).toBe('Etapa de Diseño UI');
  });

  it('falls back to default label when stage_label is empty', () => {
    const proposal = {
      project_stages: [
        { id: 1, stage_key: 'development', stage_label: '' },
      ],
    };
    const stages = deriveEditableStages(proposal);
    expect(stages[1].stage_label).toBe('Desarrollo');
  });
});


// ── validateStageDates: pure validator used by handleSave ────────────────────

function validateStageDates(dates) {
  if (!dates.start_date || !dates.end_date) {
    return 'Debes especificar fecha de inicio y fecha fin.';
  }
  if (dates.start_date > dates.end_date) {
    return 'La fecha fin debe ser igual o posterior a la fecha de inicio.';
  }
  return '';
}

describe('ProjectScheduleEditor.validateStageDates', () => {
  it('returns error when start_date is empty', () => {
    expect(validateStageDates({ start_date: '', end_date: '2026-04-15' })).toContain('especificar');
  });

  it('returns error when end_date is empty', () => {
    expect(validateStageDates({ start_date: '2026-04-01', end_date: '' })).toContain('especificar');
  });

  it('returns error when start_date is after end_date', () => {
    expect(
      validateStageDates({ start_date: '2026-04-20', end_date: '2026-04-10' }),
    ).toContain('posterior');
  });

  it('returns empty string when start_date equals end_date', () => {
    expect(
      validateStageDates({ start_date: '2026-04-10', end_date: '2026-04-10' }),
    ).toBe('');
  });

  it('returns empty string when start_date is before end_date', () => {
    expect(
      validateStageDates({ start_date: '2026-04-01', end_date: '2026-04-15' }),
    ).toBe('');
  });
});

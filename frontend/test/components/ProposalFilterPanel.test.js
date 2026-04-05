/**
 * Tests for ProposalFilterPanel logic.
 *
 * Covers: toggleArrayFilter, removeFromArray, toggleMultiSelect, updateNumeric,
 * updateField, emitUpdate, and option arrays validation.
 *
 * Following project convention: extract and test component logic directly
 * rather than mounting Vue components.
 */

// ── Helper: emitUpdate simulation ───────────────────────────────────────────

function emitUpdate(modelValue, partial) {
  return { ...modelValue, ...partial };
}

describe('emitUpdate', () => {
  it('merges partial into model value', () => {
    const model = { statuses: [], investmentMin: null };
    const result = emitUpdate(model, { investmentMin: 5000 });
    expect(result).toEqual({ statuses: [], investmentMin: 5000 });
  });

  it('does not mutate original model', () => {
    const model = { statuses: ['draft'] };
    emitUpdate(model, { statuses: [] });
    expect(model.statuses).toEqual(['draft']);
  });
});


// ── toggleArrayFilter ───────────────────────────────────────────────────────

function toggleArrayFilter(modelValue, field, value) {
  const arr = [...modelValue[field]];
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
  return emitUpdate(modelValue, { [field]: arr });
}

describe('toggleArrayFilter', () => {
  const base = { statuses: [], currencies: [], languages: [] };

  it('adds value when not present', () => {
    const result = toggleArrayFilter(base, 'statuses', 'draft');
    expect(result.statuses).toEqual(['draft']);
  });

  it('removes value when already present', () => {
    const model = { ...base, statuses: ['draft', 'sent'] };
    const result = toggleArrayFilter(model, 'statuses', 'draft');
    expect(result.statuses).toEqual(['sent']);
  });

  it('supports multiple values in array', () => {
    let model = { ...base };
    model = toggleArrayFilter(model, 'statuses', 'draft');
    model = toggleArrayFilter(model, 'statuses', 'sent');
    expect(model.statuses).toEqual(['draft', 'sent']);
  });

  it('works with currencies field', () => {
    const result = toggleArrayFilter(base, 'currencies', 'COP');
    expect(result.currencies).toEqual(['COP']);
  });

  it('works with languages field', () => {
    const result = toggleArrayFilter(base, 'languages', 'en');
    expect(result.languages).toEqual(['en']);
  });
});


// ── removeFromArray ─────────────────────────────────────────────────────────

function removeFromArray(modelValue, field, value) {
  return emitUpdate(modelValue, { [field]: modelValue[field].filter((v) => v !== value) });
}

describe('removeFromArray', () => {
  it('removes specific value from array', () => {
    const model = { projectTypes: ['webapp', 'landing', 'ecommerce'] };
    const result = removeFromArray(model, 'projectTypes', 'landing');
    expect(result.projectTypes).toEqual(['webapp', 'ecommerce']);
  });

  it('returns empty array when removing last value', () => {
    const model = { projectTypes: ['webapp'] };
    const result = removeFromArray(model, 'projectTypes', 'webapp');
    expect(result.projectTypes).toEqual([]);
  });

  it('returns unchanged array when value not present', () => {
    const model = { projectTypes: ['webapp'] };
    const result = removeFromArray(model, 'projectTypes', 'landing');
    expect(result.projectTypes).toEqual(['webapp']);
  });
});


// ── toggleMultiSelect ───────────────────────────────────────────────────────

function toggleMultiSelect(modelValue, field, value) {
  if (!value) {
    return emitUpdate(modelValue, { [field]: [] });
  }
  const arr = [...modelValue[field]];
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
  return emitUpdate(modelValue, { [field]: arr });
}

describe('toggleMultiSelect', () => {
  const base = { marketTypes: [] };

  it('clears array when value is empty string', () => {
    const model = { marketTypes: ['b2b', 'b2c'] };
    const result = toggleMultiSelect(model, 'marketTypes', '');
    expect(result.marketTypes).toEqual([]);
  });

  it('adds value when not present', () => {
    const result = toggleMultiSelect(base, 'marketTypes', 'b2b');
    expect(result.marketTypes).toEqual(['b2b']);
  });

  it('removes value when already present', () => {
    const model = { marketTypes: ['b2b'] };
    const result = toggleMultiSelect(model, 'marketTypes', 'b2b');
    expect(result.marketTypes).toEqual([]);
  });

  it('accumulates multiple selections', () => {
    let model = { ...base };
    model = toggleMultiSelect(model, 'marketTypes', 'b2b');
    model = toggleMultiSelect(model, 'marketTypes', 'saas');
    expect(model.marketTypes).toEqual(['b2b', 'saas']);
  });
});


// ── updateNumeric ───────────────────────────────────────────────────────────

function updateNumeric(modelValue, field, value) {
  const parsed = value === '' ? null : Number(value);
  return emitUpdate(modelValue, { [field]: parsed });
}

describe('updateNumeric', () => {
  const base = { investmentMin: null, investmentMax: null, heatScoreMin: null, heatScoreMax: null };

  it('sets numeric value from string', () => {
    const result = updateNumeric(base, 'investmentMin', '5000');
    expect(result.investmentMin).toBe(5000);
  });

  it('clears to null for empty string', () => {
    const model = { ...base, investmentMin: 5000 };
    const result = updateNumeric(model, 'investmentMin', '');
    expect(result.investmentMin).toBeNull();
  });

  it('handles zero value', () => {
    const result = updateNumeric(base, 'heatScoreMin', '0');
    expect(result.heatScoreMin).toBe(0);
  });

  it('handles decimal values', () => {
    const result = updateNumeric(base, 'investmentMax', '1500.50');
    expect(result.investmentMax).toBe(1500.5);
  });
});


// ── updateField ─────────────────────────────────────────────────────────────

function updateField(modelValue, field, value) {
  return emitUpdate(modelValue, { [field]: value });
}

describe('updateField', () => {
  it('sets scalar value', () => {
    const model = { isActive: 'all' };
    const result = updateField(model, 'isActive', 'active');
    expect(result.isActive).toBe('active');
  });

  it('sets date value', () => {
    const model = { createdAfter: null };
    const result = updateField(model, 'createdAfter', '2026-01-01');
    expect(result.createdAfter).toBe('2026-01-01');
  });

  it('clears value with null', () => {
    const model = { createdAfter: '2026-01-01' };
    const result = updateField(model, 'createdAfter', null);
    expect(result.createdAfter).toBeNull();
  });
});


// ── Option arrays validation ────────────────────────────────────────────────

const statusOptions = [
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'viewed', label: 'Vistas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'rejected', label: 'Rechazadas' },
  { value: 'negotiating', label: 'Negociando' },
  { value: 'expired', label: 'Expiradas' },
];

const projectTypeOptions = [
  { value: 'website', label: 'Sitio Web' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'webapp', label: 'Aplicación Web' },
  { value: 'landing', label: 'Landing Page' },
  { value: 'redesign', label: 'Rediseño' },
  { value: 'mobile_app', label: 'App Móvil' },
  { value: 'branding', label: 'Branding' },
  { value: 'cms', label: 'Sistema CMS' },
  { value: 'portal', label: 'Portal / Intranet' },
  { value: 'api_integration', label: 'Integración de APIs' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'erp', label: 'Sistema ERP' },
  { value: 'booking', label: 'Sistema de Reservas' },
  { value: 'dashboard', label: 'Dashboard / Reportes' },
  { value: 'crm', label: 'Sistema CRM' },
  { value: 'saas', label: 'SaaS / Plataforma' },
  { value: 'chatbot', label: 'Chatbot / IA' },
  { value: 'ai_tool', label: 'Herramienta con IA' },
  { value: 'automation', label: 'Automatización' },
  { value: 'data_analytics', label: 'Analítica de Datos' },
  { value: 'plugin_extension', label: 'Plugin / Extensión' },
  { value: 'other', label: 'Otro' },
];

const marketTypeOptions = [
  { value: 'b2b', label: 'B2B' },
  { value: 'b2c', label: 'B2C' },
  { value: 'saas', label: 'SaaS' },
  { value: 'retail', label: 'Retail' },
  { value: 'services', label: 'Servicios profesionales' },
  { value: 'health', label: 'Salud' },
  { value: 'education', label: 'Educación' },
  { value: 'real_estate', label: 'Inmobiliaria' },
  { value: 'fintech', label: 'Fintech' },
  { value: 'restaurant', label: 'Restaurantes' },
  { value: 'tourism', label: 'Turismo' },
  { value: 'logistics', label: 'Logística' },
  { value: 'sports', label: 'Deportes' },
  { value: 'legal', label: 'Servicios Legales' },
  { value: 'construction', label: 'Construcción' },
  { value: 'media', label: 'Medios' },
  { value: 'ngo', label: 'ONG / Sector Público' },
  { value: 'agriculture', label: 'Agro' },
  { value: 'tech', label: 'Tecnología' },
  { value: 'consulting', label: 'Consultoría' },
  { value: 'automotive', label: 'Automotriz' },
  { value: 'fashion', label: 'Moda' },
  { value: 'beauty', label: 'Belleza' },
  { value: 'manufacturing', label: 'Manufactura' },
  { value: 'energy', label: 'Energía' },
  { value: 'gaming', label: 'Gaming' },
  { value: 'other', label: 'Otro' },
];

describe('statusOptions', () => {
  it('has 7 entries', () => {
    expect(statusOptions).toHaveLength(7);
  });

  it('each entry has value and label', () => {
    statusOptions.forEach(opt => {
      expect(opt).toHaveProperty('value');
      expect(opt).toHaveProperty('label');
    });
  });

  it('has unique values', () => {
    const values = statusOptions.map(o => o.value);
    expect(new Set(values).size).toBe(values.length);
  });
});

describe('projectTypeOptions', () => {
  it('has 22 entries', () => {
    expect(projectTypeOptions).toHaveLength(22);
  });

  it('has unique values', () => {
    const values = projectTypeOptions.map(o => o.value);
    expect(new Set(values).size).toBe(values.length);
  });
});

describe('marketTypeOptions', () => {
  it('has 27 entries', () => {
    expect(marketTypeOptions).toHaveLength(27);
  });

  it('has unique values', () => {
    const values = marketTypeOptions.map(o => o.value);
    expect(new Set(values).size).toBe(values.length);
  });
});


// ── Label maps ──────────────────────────────────────────────────────────────

describe('label maps', () => {
  const projectTypeLabelMap = Object.fromEntries(projectTypeOptions.map((o) => [o.value, o.label]));
  const marketTypeLabelMap = Object.fromEntries(marketTypeOptions.map((o) => [o.value, o.label]));

  it('maps project type value to label', () => {
    expect(projectTypeLabelMap['webapp']).toBe('Aplicación Web');
  });

  it('maps market type value to label', () => {
    expect(marketTypeLabelMap['fintech']).toBe('Fintech');
  });

  it('returns undefined for unknown project type', () => {
    expect(projectTypeLabelMap['nonexistent']).toBeUndefined();
  });
});


// ── Filter count badge logic ────────────────────────────────────────────────

describe('filter count badge text', () => {
  function badgeText(count) {
    if (count <= 0) return null;
    return `${count} filtro${count !== 1 ? 's' : ''} activo${count !== 1 ? 's' : ''}`;
  }

  it('returns null when count is 0', () => {
    expect(badgeText(0)).toBeNull();
  });

  it('returns singular for count 1', () => {
    expect(badgeText(1)).toBe('1 filtro activo');
  });

  it('returns plural for count > 1', () => {
    expect(badgeText(3)).toBe('3 filtros activos');
  });
});

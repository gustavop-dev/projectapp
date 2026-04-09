/**
 * Tests for proposalJsonMigration utility.
 *
 * Covers: LEGACY_FIELD_LABELS, detectLegacyTechnicalFormat (all 14 patterns),
 * migrateLegacyProposalJson (all transformations), downloadMigratedProposalJson (DOM mocking).
 */
import {
  LEGACY_FIELD_LABELS,
  detectLegacyTechnicalFormat,
  migrateLegacyProposalJson,
  downloadMigratedProposalJson,
} from '../../utils/proposalJsonMigration';

// ── Helpers ──────────────────────────────────────────────────────────────────

function buildModernProposal(tdOverrides = {}) {
  return {
    general: { clientName: 'Test Client' },
    technicalDocument: {
      stack: [{ layer: 'Frontend', technology: 'Vue', rationale: 'reactive' }],
      security: [{ aspect: 'Auth', implementation: 'JWT' }],
      performanceQuality: {
        metrics: [{ metric: 'LCP', target: '<2.5s', howMeasured: 'Lighthouse' }],
        practices: [{ strategy: 'CDN', description: 'Edge caching' }],
      },
      epics: [{ name: 'Auth', requirements: [{ title: 'Login', description: 'User login' }] }],
      decisions: [{ decision: 'Vue', reason: 'DX', alternative: 'React' }],
      apiDomains: [{ name: 'Users', summary: 'User management' }],
      integrations: {
        included: [{ service: 'Stripe', provider: 'Stripe Inc', connection: 'API', dataExchange: 'JSON', accountOwner: 'Admin' }],
        excluded: [{ service: 'PayPal', reason: 'Not needed', availability: 'N/A' }],
      },
      growthReadiness: { strategies: [{ dimension: 'Scale', preparation: 'K8s', evolution: 'Auto-scale' }] },
      architecture: { patterns: [{ component: 'API', pattern: 'REST', description: 'RESTful' }] },
      quality: {
        dimensions: [{ dimension: 'Reliability', evaluates: 'Uptime', standard: '99.9%' }],
        testTypes: [{ type: 'Unit', validates: 'Logic', tool: 'Jest', whenRun: 'CI' }],
      },
      environments: [{ name: 'Production', purpose: 'Live' }],
      ...tdOverrides,
    },
  };
}

// ── LEGACY_FIELD_LABELS ──────────────────────────────────────────────────────

describe('LEGACY_FIELD_LABELS', () => {
  it('exports an object with 14 entries', () => {
    expect(Object.keys(LEGACY_FIELD_LABELS)).toHaveLength(14);
  });

  it('has string descriptions for every key', () => {
    Object.values(LEGACY_FIELD_LABELS).forEach((label) => {
      expect(typeof label).toBe('string');
      expect(label.length).toBeGreaterThan(0);
    });
  });
});

// ── detectLegacyTechnicalFormat ──────────────────────────────────────────────

describe('detectLegacyTechnicalFormat', () => {
  it('returns not legacy when proposalJson is null', () => {
    expect(detectLegacyTechnicalFormat(null)).toEqual({ isLegacy: false, issues: [] });
  });

  it('returns not legacy when technicalDocument is missing', () => {
    expect(detectLegacyTechnicalFormat({ general: {} })).toEqual({ isLegacy: false, issues: [] });
  });

  it('returns not legacy when technicalDocument is not an object', () => {
    expect(detectLegacyTechnicalFormat({ technicalDocument: 'string' })).toEqual({ isLegacy: false, issues: [] });
  });

  it('returns not legacy for a fully modern format document', () => {
    const result = detectLegacyTechnicalFormat(buildModernProposal());
    expect(result.isLegacy).toBe(false);
    expect(result.issues).toEqual([]);
  });

  it('detects legacy stack with {category, technologies} format', () => {
    const proposal = { technicalDocument: { stack: [{ category: 'Frontend', technologies: 'Vue, React' }] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.stack');
  });

  it('detects legacy stack with flat string format', () => {
    const proposal = { technicalDocument: { stack: ['Vue', 'React'] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.stack');
  });

  it('detects legacy security as flat strings', () => {
    const proposal = { technicalDocument: { security: ['HTTPS', 'JWT'] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.security');
  });

  it('detects legacy performanceQuality.metrics as flat strings', () => {
    const proposal = { technicalDocument: { performanceQuality: { metrics: ['LCP < 2.5s'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.performanceQuality.metrics');
  });

  it('detects legacy performanceQuality.practices as flat strings', () => {
    const proposal = { technicalDocument: { performanceQuality: { practices: ['CDN caching'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.performanceQuality.practices');
  });

  it('detects legacy epics[].requirements as flat strings', () => {
    const proposal = { technicalDocument: { epics: [{ name: 'Auth', requirements: ['Login page'] }] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.epics[].requirements');
  });

  it('detects legacy decisions with {rationale} instead of {reason}', () => {
    const proposal = { technicalDocument: { decisions: [{ decision: 'Vue', rationale: 'DX' }] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.decisions');
  });

  it('detects legacy apiDomains with {description} instead of {summary}', () => {
    const proposal = { technicalDocument: { apiDomains: [{ name: 'Users', description: 'User mgmt' }] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.apiDomains');
  });

  it('detects legacy integrations.included as flat strings', () => {
    const proposal = { technicalDocument: { integrations: { included: ['Stripe', 'Twilio'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.integrations.included');
  });

  it('detects legacy integrations.excluded as flat strings', () => {
    const proposal = { technicalDocument: { integrations: { excluded: ['PayPal'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.integrations.excluded');
  });

  it('detects legacy growthReadiness.strategies as flat strings', () => {
    const proposal = { technicalDocument: { growthReadiness: { strategies: ['Horizontal scaling'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.growthReadiness.strategies');
  });

  it('detects legacy architecture.patterns as flat strings', () => {
    const proposal = { technicalDocument: { architecture: { patterns: ['MVC'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.architecture.patterns');
  });

  it('detects legacy quality.dimensions as flat strings', () => {
    const proposal = { technicalDocument: { quality: { dimensions: ['Reliability'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.quality.dimensions');
  });

  it('detects legacy quality.testTypes as flat strings', () => {
    const proposal = { technicalDocument: { quality: { testTypes: ['Unit tests'] } } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.quality.testTypes');
  });

  it('detects legacy environments with {description} instead of {purpose}', () => {
    const proposal = { technicalDocument: { environments: [{ name: 'Prod', description: 'Live' }] } };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toContain('technicalDocument.environments');
  });

  it('reports multiple legacy issues simultaneously', () => {
    const proposal = {
      technicalDocument: {
        security: ['HTTPS'],
        decisions: [{ decision: 'Vue', rationale: 'DX' }],
        environments: [{ name: 'Prod', description: 'Live' }],
      },
    };
    const result = detectLegacyTechnicalFormat(proposal);
    expect(result.isLegacy).toBe(true);
    expect(result.issues).toHaveLength(3);
  });
});

// ── migrateLegacyProposalJson ────────────────────────────────────────────────

describe('migrateLegacyProposalJson', () => {
  it('returns input unchanged when technicalDocument is missing', () => {
    const input = { general: { clientName: 'Test' } };
    expect(migrateLegacyProposalJson(input)).toBe(input);
  });

  it('returns input unchanged when proposalJson is null', () => {
    expect(migrateLegacyProposalJson(null)).toBeNull();
  });

  it('does not mutate the original object', () => {
    const original = {
      technicalDocument: { security: ['HTTPS'] },
    };
    const originalJson = JSON.stringify(original);

    migrateLegacyProposalJson(original);

    expect(JSON.stringify(original)).toBe(originalJson);
  });

  it('migrates stack from {category, technologies} to {layer, technology, rationale}', () => {
    const input = { technicalDocument: { stack: [{ category: 'Frontend', technologies: 'Vue' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.stack[0]).toEqual({ layer: 'Frontend', technology: 'Vue', rationale: '' });
  });

  it('migrates stack with only technologies (no category)', () => {
    const input = { technicalDocument: { stack: [{ technologies: 'React' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.stack[0]).toEqual({ layer: '', technology: 'React', rationale: '' });
  });

  it('migrates stack with only category (no technologies)', () => {
    const input = { technicalDocument: { stack: [{ category: 'Backend', rationale: 'stable' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.stack[0]).toEqual({ layer: 'Backend', technology: '', rationale: 'stable' });
  });

  it('migrates stack from flat string to structured object', () => {
    const input = { technicalDocument: { stack: ['Vue.js'] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.stack[0]).toEqual({ layer: 'Vue.js', technology: '', rationale: '' });
  });

  it('migrates security from flat strings to {aspect, implementation}', () => {
    const input = { technicalDocument: { security: ['HTTPS', 'JWT'] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.security).toEqual([
      { aspect: 'HTTPS', implementation: '' },
      { aspect: 'JWT', implementation: '' },
    ]);
  });

  it('migrates performanceQuality metrics and practices', () => {
    const input = {
      technicalDocument: {
        performanceQuality: {
          metrics: ['LCP < 2.5s'],
          practices: ['CDN caching'],
        },
      },
    };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.performanceQuality.metrics[0]).toEqual({
      metric: 'LCP < 2.5s', target: '', howMeasured: '',
    });
    expect(result.technicalDocument.performanceQuality.practices[0]).toEqual({
      strategy: 'CDN caching', description: '',
    });
  });

  it('migrates epics requirements from strings to {title, description}', () => {
    const input = { technicalDocument: { epics: [{ name: 'Auth', requirements: ['Login page'] }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.epics[0].requirements[0]).toEqual({
      title: 'Login page', description: '',
    });
  });

  it('migrates decisions: rationale to reason, adds alternative', () => {
    const input = { technicalDocument: { decisions: [{ decision: 'Vue', rationale: 'Great DX' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.decisions[0].reason).toBe('Great DX');
    expect(result.technicalDocument.decisions[0].alternative).toBe('');
  });

  it('migrates apiDomains: description to summary', () => {
    const input = { technicalDocument: { apiDomains: [{ name: 'Users', description: 'User mgmt' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.apiDomains[0].summary).toBe('User mgmt');
  });

  it('migrates integrations included from strings to objects', () => {
    const input = { technicalDocument: { integrations: { included: ['Stripe'] } } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.integrations.included[0]).toEqual({
      service: 'Stripe', provider: '', connection: '', dataExchange: '', accountOwner: '',
    });
  });

  it('migrates integrations excluded from strings to objects', () => {
    const input = { technicalDocument: { integrations: { excluded: ['PayPal'] } } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.integrations.excluded[0]).toEqual({
      service: 'PayPal', reason: '', availability: '',
    });
  });

  it('migrates growthReadiness strategies from strings to structured objects', () => {
    const input = { technicalDocument: { growthReadiness: { strategies: ['Horizontal scaling'] } } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.growthReadiness.strategies[0]).toEqual({
      dimension: '', preparation: 'Horizontal scaling', evolution: '',
    });
  });

  it('migrates architecture patterns from strings to structured objects', () => {
    const input = { technicalDocument: { architecture: { patterns: ['MVC'] } } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.architecture.patterns[0]).toEqual({
      component: '', pattern: '', description: 'MVC',
    });
  });

  it('migrates quality dimensions from strings to structured objects', () => {
    const input = { technicalDocument: { quality: { dimensions: ['Reliability'] } } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.quality.dimensions[0]).toEqual({
      dimension: 'Reliability', evaluates: '', standard: '',
    });
  });

  it('migrates quality testTypes from strings to structured objects', () => {
    const input = { technicalDocument: { quality: { testTypes: ['Unit tests'] } } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.quality.testTypes[0]).toEqual({
      type: 'Unit tests', validates: '', tool: '', whenRun: '',
    });
  });

  it('migrates environments: description to purpose', () => {
    const input = { technicalDocument: { environments: [{ name: 'Prod', description: 'Live server' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.environments[0].purpose).toBe('Live server');
  });

  it('preserves already-modern format fields without modification', () => {
    const modern = buildModernProposal();
    const result = migrateLegacyProposalJson(modern);
    expect(result.technicalDocument.stack[0]).toEqual(modern.technicalDocument.stack[0]);
    expect(result.technicalDocument.security[0]).toEqual(modern.technicalDocument.security[0]);
    expect(result.technicalDocument.decisions[0]).toEqual(modern.technicalDocument.decisions[0]);
  });

  it('preserves stack items that already have layer and technology', () => {
    const input = {
      technicalDocument: {
        stack: [
          { layer: 'Frontend', technology: 'Vue', rationale: 'reactive' },
          { category: 'Backend', technologies: 'Django' },
        ],
      },
    };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.stack[0]).toEqual({ layer: 'Frontend', technology: 'Vue', rationale: 'reactive' });
    expect(result.technicalDocument.stack[1]).toEqual({ layer: 'Backend', technology: 'Django', rationale: '' });
  });

  it('returns epic unchanged when it has no requirements array', () => {
    const input = { technicalDocument: { epics: [{ name: 'Auth' }, { name: 'Dashboard', requirements: ['Page'] }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.epics[0]).toEqual({ name: 'Auth' });
    expect(result.technicalDocument.epics[1].requirements[0]).toEqual({ title: 'Page', description: '' });
  });

  it('returns null epic unchanged', () => {
    const input = { technicalDocument: { epics: [null, { name: 'Auth', requirements: ['Login'] }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.epics[0]).toBeNull();
  });

  it('returns non-object decision unchanged', () => {
    const input = { technicalDocument: { decisions: [null, 'string-decision', { decision: 'Vue', rationale: 'DX' }] } };
    const result = migrateLegacyProposalJson(input);
    expect(result.technicalDocument.decisions[0]).toBeNull();
    expect(result.technicalDocument.decisions[1]).toBe('string-decision');
    expect(result.technicalDocument.decisions[2].reason).toBe('DX');
  });
});

// ── downloadMigratedProposalJson ─────────────────────────────────────────────

describe('downloadMigratedProposalJson', () => {
  let mockAnchor;
  let createElementSpy;

  beforeEach(() => {
    jest.useFakeTimers();
    mockAnchor = { href: '', download: '', click: jest.fn() };
    createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);
    jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});
    URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('does nothing when proposalJson is null', () => {
    downloadMigratedProposalJson(null);

    expect(createElementSpy).not.toHaveBeenCalled();
  });

  it('creates a downloadable blob with migrated JSON', () => {
    const input = { general: { clientName: 'Acme' }, technicalDocument: { security: ['HTTPS'] } };

    downloadMigratedProposalJson(input);

    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(mockAnchor.click).toHaveBeenCalled();
    expect(document.body.appendChild).toHaveBeenCalledWith(mockAnchor);
    expect(document.body.removeChild).toHaveBeenCalledWith(mockAnchor);
  });

  it('generates filename slug from clientName', () => {
    downloadMigratedProposalJson({ general: { clientName: 'Acme Corp' }, technicalDocument: {} });

    expect(mockAnchor.download).toBe('proposal-acme-corp-v2.json');
  });

  it('uses fallback filename when clientName is missing', () => {
    downloadMigratedProposalJson({ technicalDocument: {} });

    expect(mockAnchor.download).toBe('proposal-propuesta-v2.json');
  });

  it('revokes object URL after timeout', () => {
    downloadMigratedProposalJson({ general: { clientName: 'Test' }, technicalDocument: {} });

    expect(URL.revokeObjectURL).not.toHaveBeenCalled();
    jest.advanceTimersByTime(100);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });
});

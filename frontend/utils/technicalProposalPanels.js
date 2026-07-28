/**
 * Synthetic panels for public proposal "technical" view mode.
 * IDs are stable for tracking and localStorage progress.
 */

const FRAGMENT_ORDER = [
  'intro',
  'stack',
  'architecture',
  'dataModel',
  'growthReadiness',
  'epics',
  'api',
  'integrations',
  'environments',
  'security',
  'performance',
  'backups',
  'quality',
  'decisions',
];

const FRAGMENT_IDS = {
  intro: 'tech_intro',
  stack: 'tech_stack',
  architecture: 'tech_architecture',
  dataModel: 'tech_data',
  growthReadiness: 'tech_growth',
  epics: 'tech_epics',
  api: 'tech_api',
  integrations: 'tech_integrations',
  environments: 'tech_environments',
  security: 'tech_security',
  performance: 'tech_performance',
  backups: 'tech_backups',
  quality: 'tech_quality',
  decisions: 'tech_decisions',
};

export const TECH_PANEL_TITLES = {
  es: {
    intro: 'Detalle técnico',
    stack: 'Stack tecnológico',
    architecture: 'Arquitectura',
    dataModel: 'Modelo de datos',
    growthReadiness: 'Preparación para el crecimiento',
    epics: 'Módulos del producto',
    api: 'API y endpoints',
    integrations: 'Integraciones',
    environments: 'Ambientes',
    security: 'Seguridad',
    performance: 'Rendimiento y prácticas',
    backups: 'Backups',
    quality: 'Calidad y pruebas',
    decisions: 'Decisiones técnicas',
  },
  en: {
    intro: 'Technical detail',
    stack: 'Technology stack',
    architecture: 'Architecture',
    dataModel: 'Data model',
    growthReadiness: 'Growth readiness',
    epics: 'Product modules',
    api: 'API and endpoints',
    integrations: 'Integrations',
    environments: 'Environments',
    security: 'Security',
    performance: 'Performance and practices',
    backups: 'Backups',
    quality: 'Quality and testing',
    decisions: 'Technical decisions',
  },
};

/**
 * Single source for the "how long is this document" promise. Rendered both on
 * the mode gateway card and on the technical cover, which must never disagree.
 */
export const TECH_READING_TIME = {
  es: '~30 min de lectura',
  en: '~30 min read',
};

// [singular, plural] per counted noun, used to build the per-section weight
// shown on the technical cover index ("7 capas", "6 módulos · 38 requerimientos").
const FRAGMENT_COUNT_NOUNS = {
  es: {
    layers: ['capa', 'capas'],
    patterns: ['patrón', 'patrones'],
    entities: ['entidad', 'entidades'],
    dimensions: ['dimensión', 'dimensiones'],
    modules: ['módulo', 'módulos'],
    requirements: ['requerimiento', 'requerimientos'],
    domains: ['dominio', 'dominios'],
    included: ['incluida', 'incluidas'],
    excluded: ['no incluida', 'no incluidas'],
    environments: ['ambiente', 'ambientes'],
    aspects: ['aspecto', 'aspectos'],
    metrics: ['métrica', 'métricas'],
    practices: ['práctica', 'prácticas'],
    testTypes: ['tipo de prueba', 'tipos de prueba'],
    decisions: ['decisión', 'decisiones'],
  },
  en: {
    layers: ['layer', 'layers'],
    patterns: ['pattern', 'patterns'],
    entities: ['entity', 'entities'],
    dimensions: ['dimension', 'dimensions'],
    modules: ['module', 'modules'],
    requirements: ['requirement', 'requirements'],
    domains: ['domain', 'domains'],
    included: ['included', 'included'],
    excluded: ['not included', 'not included'],
    environments: ['environment', 'environments'],
    aspects: ['aspect', 'aspects'],
    metrics: ['metric', 'metrics'],
    practices: ['practice', 'practices'],
    testTypes: ['test type', 'test types'],
    decisions: ['decision', 'decisions'],
  },
};

function _nonEmptyStr(v) {
  return typeof v === 'string' && v.trim().length > 0;
}

function _rowHasValues(row, keys) {
  if (!row || typeof row !== 'object') return false;
  return keys.some((k) => _nonEmptyStr(row[k]));
}

/**
 * @param {string} fragment
 * @param {object} doc — merged technical document content_json
 */
export function technicalFragmentHasContent(fragment, doc) {
  const d = doc && typeof doc === 'object' ? doc : {};
  switch (fragment) {
    case 'intro':
      return true;
    case 'stack':
      return Array.isArray(d.stack) && d.stack.some((r) => _rowHasValues(r, ['layer', 'technology', 'rationale']));
    case 'architecture': {
      const arch = d.architecture || {};
      if (_nonEmptyStr(arch.summary) || _nonEmptyStr(arch.diagramNote)) return true;
      const pats = arch.patterns || [];
      return pats.some((r) => _rowHasValues(r, ['component', 'pattern', 'description']));
    }
    case 'dataModel': {
      const dm = d.dataModel || {};
      if (_nonEmptyStr(dm.summary) || _nonEmptyStr(dm.relationships)) return true;
      const ents = dm.entities || [];
      return ents.some((r) => _rowHasValues(r, ['name', 'description', 'keyFields']));
    }
    case 'growthReadiness': {
      const gr = d.growthReadiness || {};
      if (_nonEmptyStr(gr.summary)) return true;
      const st = gr.strategies || [];
      return st.some((r) => _rowHasValues(r, ['dimension', 'preparation', 'evolution']));
    }
    case 'epics':
      return Array.isArray(d.epics) && d.epics.some((ep) => {
        if (_nonEmptyStr(ep.title) || _nonEmptyStr(ep.description) || _nonEmptyStr(ep.epicKey)) return true;
        const reqs = ep.requirements || [];
        return reqs.some((rq) => _rowHasValues(rq, ['title', 'description', 'configuration', 'usageFlow', 'flowKey']));
      });
    case 'api':
      if (_nonEmptyStr(d.apiSummary)) return true;
      return Array.isArray(d.apiDomains) && d.apiDomains.some((r) => _rowHasValues(r, ['domain', 'summary']));
    case 'integrations': {
      const integ = d.integrations || {};
      if (_nonEmptyStr(integ.notes)) return true;
      const inc = integ.included || [];
      const exc = integ.excluded || [];
      return inc.some((r) => _rowHasValues(r, ['service', 'provider', 'connection', 'dataExchange', 'accountOwner']))
        || exc.some((r) => _rowHasValues(r, ['service', 'reason', 'availability']));
    }
    case 'environments':
      if (_nonEmptyStr(d.environmentsNote)) return true;
      return Array.isArray(d.environments) && d.environments.some((r) => _rowHasValues(r, ['name', 'purpose', 'url', 'database', 'whoAccesses']));
    case 'security':
      return Array.isArray(d.security) && d.security.some((r) => _rowHasValues(r, ['aspect', 'implementation']));
    case 'performance': {
      const pq = d.performanceQuality || {};
      const m = pq.metrics || [];
      const p = pq.practices || [];
      return m.some((r) => _rowHasValues(r, ['metric', 'target', 'howMeasured']))
        || p.some((r) => _rowHasValues(r, ['strategy', 'description']));
    }
    case 'backups':
      return _nonEmptyStr(d.backupsNote);
    case 'quality': {
      const q = d.quality || {};
      if (_nonEmptyStr(q.criticalFlowsNote)) return true;
      const dims = q.dimensions || [];
      const tt = q.testTypes || [];
      return dims.some((r) => _rowHasValues(r, ['dimension', 'evaluates', 'standard']))
        || tt.some((r) => _rowHasValues(r, ['type', 'validates', 'tool', 'whenRun']));
    }
    case 'decisions':
      return Array.isArray(d.decisions) && d.decisions.some((r) => _rowHasValues(r, ['decision', 'alternative', 'reason']));
    default:
      return false;
  }
}

function _countRows(rows, keys) {
  if (!Array.isArray(rows)) return 0;
  return rows.filter((r) => _rowHasValues(r, keys)).length;
}

const _EPIC_REQ_KEYS = ['title', 'description', 'configuration', 'usageFlow', 'flowKey'];

// Mirrors the `epicsList` computed in TechnicalDocumentPublicPanel: a module
// counts when it is named or carries at least one requirement that survives
// the same row filter the table applies.
function _countEpics(epics) {
  let modules = 0;
  let requirements = 0;
  if (!Array.isArray(epics)) return { modules, requirements };
  for (const ep of epics) {
    if (!ep || typeof ep !== 'object') continue;
    const reqs = Array.isArray(ep.requirements)
      ? ep.requirements.filter((rq) => _rowHasValues(rq, _EPIC_REQ_KEYS))
      : [];
    const named = _nonEmptyStr(ep.title) || _nonEmptyStr(ep.epicKey) || _nonEmptyStr(ep.description);
    if (!named && !reqs.length) continue;
    modules += 1;
    requirements += reqs.length;
  }
  return { modules, requirements };
}

/**
 * How much substance a technical section holds, for the cover index.
 *
 * Counts only rows the section would actually render, so the promise on the
 * cover matches what the reader finds after the jump. Returns '' when there is
 * nothing countable (free-text sections, or a section present only because of a
 * loose summary) — callers omit the line rather than print "0 patrones".
 *
 * @param {string} fragment
 * @param {object} doc — merged technical document content_json
 * @param {string} lang — 'es' | 'en'
 * @returns {string}
 */
export function technicalFragmentSummary(fragment, doc, lang) {
  const d = doc && typeof doc === 'object' ? doc : {};
  const nouns = FRAGMENT_COUNT_NOUNS[lang] || FRAGMENT_COUNT_NOUNS.es;
  const part = (n, key) => (n > 0 ? `${n} ${nouns[key][n === 1 ? 0 : 1]}` : '');
  const join = (...parts) => parts.filter(Boolean).join(' · ');

  switch (fragment) {
    case 'stack':
      return part(_countRows(d.stack, ['layer', 'technology', 'rationale']), 'layers');
    case 'architecture':
      return part(_countRows(d.architecture?.patterns, ['component', 'pattern', 'description']), 'patterns');
    case 'dataModel':
      return part(_countRows(d.dataModel?.entities, ['name', 'description', 'keyFields']), 'entities');
    case 'growthReadiness':
      return part(_countRows(d.growthReadiness?.strategies, ['dimension', 'preparation', 'evolution']), 'dimensions');
    case 'epics': {
      const { modules, requirements } = _countEpics(d.epics);
      return join(part(modules, 'modules'), part(requirements, 'requirements'));
    }
    case 'api':
      return part(_countRows(d.apiDomains, ['domain', 'summary']), 'domains');
    case 'integrations': {
      const integ = d.integrations || {};
      return join(
        part(_countRows(integ.included, ['service', 'provider', 'connection', 'dataExchange', 'accountOwner']), 'included'),
        part(_countRows(integ.excluded, ['service', 'reason', 'availability']), 'excluded'),
      );
    }
    case 'environments':
      return part(_countRows(d.environments, ['name', 'purpose', 'url', 'database', 'whoAccesses']), 'environments');
    case 'security':
      return part(_countRows(d.security, ['aspect', 'implementation']), 'aspects');
    case 'performance': {
      const pq = d.performanceQuality || {};
      return join(
        part(_countRows(pq.metrics, ['metric', 'target', 'howMeasured']), 'metrics'),
        part(_countRows(pq.practices, ['strategy', 'description']), 'practices'),
      );
    }
    case 'quality': {
      const q = d.quality || {};
      return join(
        part(_countRows(q.dimensions, ['dimension', 'evaluates', 'standard']), 'dimensions'),
        part(_countRows(q.testTypes, ['type', 'validates', 'tool', 'whenRun']), 'testTypes'),
      );
    }
    case 'decisions':
      return part(_countRows(d.decisions, ['decision', 'alternative', 'reason']), 'decisions');
    default:
      // intro (never listed) and backups (a single free-text note) carry no count.
      return '';
  }
}

/**
 * @param {object} technicalSection — ProposalSection-like { id, content_json, title }
 * @param {string} lang — 'es' | 'en'
 * @returns {object[]} panel descriptors for carousel (before proposal_closing)
 */
export function buildSyntheticTechnicalPanels(technicalSection, lang) {
  const doc = technicalSection?.content_json && typeof technicalSection.content_json === 'object'
    ? technicalSection.content_json
    : {};
  const loc = TECH_PANEL_TITLES[lang] || TECH_PANEL_TITLES.es;
  const panels = [];

  for (const fragment of FRAGMENT_ORDER) {
    if (!technicalFragmentHasContent(fragment, doc)) continue;
    panels.push({
      id: FRAGMENT_IDS[fragment],
      section_type: 'technical_document_public',
      /* c8 ignore next */
      title: loc[fragment] || fragment,
      content_json: doc,
      _technicalFragment: fragment,
      _sourceTechnicalSectionId: technicalSection?.id,
    });
  }

  return panels;
}

export { FRAGMENT_ORDER, FRAGMENT_IDS };

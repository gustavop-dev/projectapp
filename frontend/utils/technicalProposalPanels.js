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
    intro: 'Documento técnico',
    stack: 'Stack tecnológico',
    architecture: 'Arquitectura',
    dataModel: 'Modelo de datos',
    growthReadiness: 'Preparación para el crecimiento',
    epics: 'Épicas y requerimientos',
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
    intro: 'Technical document',
    stack: 'Technology stack',
    architecture: 'Architecture',
    dataModel: 'Data model',
    growthReadiness: 'Growth readiness',
    epics: 'Epics and requirements',
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
      title: loc[fragment] || fragment,
      content_json: doc,
      _technicalFragment: fragment,
      _sourceTechnicalSectionId: technicalSection?.id,
    });
  }

  return panels;
}

export { FRAGMENT_ORDER, FRAGMENT_IDS };

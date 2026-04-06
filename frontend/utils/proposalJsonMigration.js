/**
 * Utilities for detecting and migrating legacy proposal JSON formats.
 *
 * The technicalDocument section historically used a simplified format
 * (flat string arrays, {category/technologies} for stack, {rationale} for decisions, etc.)
 * that no longer matches the structured format expected by the renderer.
 */

/** Human-readable labels for each detectable legacy field */
export const LEGACY_FIELD_LABELS = {
  'technicalDocument.stack': 'stack — usa {category, technologies} en lugar de {layer, technology, rationale}',
  'technicalDocument.security': 'security — array de strings en lugar de {aspect, implementation}[]',
  'technicalDocument.performanceQuality.metrics': 'performanceQuality.metrics — array de strings en lugar de {metric, target, howMeasured}[]',
  'technicalDocument.performanceQuality.practices': 'performanceQuality.practices — array de strings en lugar de {strategy, description}[]',
  'technicalDocument.epics[].requirements': 'epics[].requirements — array de strings en lugar de {title, description}[]',
  'technicalDocument.decisions': 'decisions — usa {rationale} en lugar de {reason}',
  'technicalDocument.apiDomains': 'apiDomains — usa {description} en lugar de {summary}',
  'technicalDocument.integrations.included': 'integrations.included — array de strings en lugar de objetos estructurados',
  'technicalDocument.integrations.excluded': 'integrations.excluded — array de strings en lugar de objetos estructurados',
  'technicalDocument.growthReadiness.strategies': 'growthReadiness.strategies — array de strings en lugar de {dimension, preparation, evolution}[]',
  'technicalDocument.architecture.patterns': 'architecture.patterns — array de strings en lugar de {component, pattern, description}[]',
  'technicalDocument.quality.dimensions': 'quality.dimensions — array de strings en lugar de {dimension, evaluates, standard}[]',
  'technicalDocument.quality.testTypes': 'quality.testTypes — array de strings en lugar de {type, validates, tool, whenRun}[]',
  'technicalDocument.environments': 'environments — usa {description} en lugar de {purpose}',
};

/**
 * Detects whether a proposal JSON uses the legacy technical document format.
 *
 * @param {object} proposalJson — full proposal JSON (camelCase keys, pre-import format)
 * @returns {{ isLegacy: boolean, issues: string[] }} — issues is a list of field keys from LEGACY_FIELD_LABELS
 */
export function detectLegacyTechnicalFormat(proposalJson) {
  const td = proposalJson?.technicalDocument;
  if (!td || typeof td !== 'object') return { isLegacy: false, issues: [] };

  const issues = [];

  // stack: {category, technologies} instead of {layer, technology, rationale}
  if (Array.isArray(td.stack) && td.stack.length > 0) {
    const first = td.stack[0];
    if (typeof first === 'string' || (first && (first.category || first.technologies) && !first.layer && !first.technology)) {
      issues.push('technicalDocument.stack');
    }
  }

  // security: flat strings instead of {aspect, implementation}
  if (Array.isArray(td.security) && td.security.length > 0 && typeof td.security[0] === 'string') {
    issues.push('technicalDocument.security');
  }

  // performanceQuality.metrics / practices: flat strings
  if (td.performanceQuality && typeof td.performanceQuality === 'object') {
    if (Array.isArray(td.performanceQuality.metrics) && td.performanceQuality.metrics.length > 0
      && typeof td.performanceQuality.metrics[0] === 'string') {
      issues.push('technicalDocument.performanceQuality.metrics');
    }
    if (Array.isArray(td.performanceQuality.practices) && td.performanceQuality.practices.length > 0
      && typeof td.performanceQuality.practices[0] === 'string') {
      issues.push('technicalDocument.performanceQuality.practices');
    }
  }

  // epics[].requirements: flat strings
  if (Array.isArray(td.epics) && td.epics.length > 0) {
    const firstEpic = td.epics[0];
    if (Array.isArray(firstEpic?.requirements) && firstEpic.requirements.length > 0
      && typeof firstEpic.requirements[0] === 'string') {
      issues.push('technicalDocument.epics[].requirements');
    }
  }

  // decisions: {rationale} instead of {reason}
  if (Array.isArray(td.decisions) && td.decisions.length > 0) {
    const first = td.decisions[0];
    if (first && typeof first === 'object' && first.rationale && !first.reason) {
      issues.push('technicalDocument.decisions');
    }
  }

  // apiDomains: {description} instead of {summary}
  if (Array.isArray(td.apiDomains) && td.apiDomains.length > 0) {
    const first = td.apiDomains[0];
    if (first && typeof first === 'object' && first.description && !first.summary) {
      issues.push('technicalDocument.apiDomains');
    }
  }

  // integrations.included / excluded: flat strings
  if (td.integrations && typeof td.integrations === 'object') {
    if (Array.isArray(td.integrations.included) && td.integrations.included.length > 0
      && typeof td.integrations.included[0] === 'string') {
      issues.push('technicalDocument.integrations.included');
    }
    if (Array.isArray(td.integrations.excluded) && td.integrations.excluded.length > 0
      && typeof td.integrations.excluded[0] === 'string') {
      issues.push('technicalDocument.integrations.excluded');
    }
  }

  // growthReadiness.strategies: flat strings
  if (Array.isArray(td.growthReadiness?.strategies) && td.growthReadiness.strategies.length > 0
    && typeof td.growthReadiness.strategies[0] === 'string') {
    issues.push('technicalDocument.growthReadiness.strategies');
  }

  // architecture.patterns: flat strings
  if (Array.isArray(td.architecture?.patterns) && td.architecture.patterns.length > 0
    && typeof td.architecture.patterns[0] === 'string') {
    issues.push('technicalDocument.architecture.patterns');
  }

  // quality.dimensions / testTypes: flat strings
  if (td.quality && typeof td.quality === 'object') {
    if (Array.isArray(td.quality.dimensions) && td.quality.dimensions.length > 0
      && typeof td.quality.dimensions[0] === 'string') {
      issues.push('technicalDocument.quality.dimensions');
    }
    if (Array.isArray(td.quality.testTypes) && td.quality.testTypes.length > 0
      && typeof td.quality.testTypes[0] === 'string') {
      issues.push('technicalDocument.quality.testTypes');
    }
  }

  // environments: {description} instead of {purpose}
  if (Array.isArray(td.environments) && td.environments.length > 0) {
    const first = td.environments[0];
    if (first && typeof first === 'object' && first.description && !first.purpose) {
      issues.push('technicalDocument.environments');
    }
  }

  return { isLegacy: issues.length > 0, issues };
}

/**
 * Migrates a proposal JSON from the legacy format to the current structured format.
 * Returns a new object; the original is not mutated.
 *
 * @param {object} proposalJson — full proposal JSON (camelCase, pre-import format)
 * @returns {object} — migrated JSON ready for import
 */
export function migrateLegacyProposalJson(proposalJson) {
  if (!proposalJson?.technicalDocument) return proposalJson;

  const td = { ...proposalJson.technicalDocument };

  // stack: {category, technologies} or string → {layer, technology, rationale}
  if (Array.isArray(td.stack)) {
    td.stack = td.stack.map((r) => {
      if (typeof r === 'string') return { layer: r, technology: '', rationale: '' };
      if (r && !r.layer && !r.technology && (r.category || r.technologies)) {
        return { layer: r.category || '', technology: r.technologies || '', rationale: r.rationale || '' };
      }
      return r;
    });
  }

  // security: string → {aspect, implementation}
  if (Array.isArray(td.security)) {
    td.security = td.security.map((r) =>
      typeof r === 'string' ? { aspect: r, implementation: '' } : r,
    );
  }

  // performanceQuality
  if (td.performanceQuality && typeof td.performanceQuality === 'object') {
    const pq = { ...td.performanceQuality };
    if (Array.isArray(pq.metrics)) {
      pq.metrics = pq.metrics.map((r) =>
        typeof r === 'string' ? { metric: r, target: '', howMeasured: '' } : r,
      );
    }
    if (Array.isArray(pq.practices)) {
      pq.practices = pq.practices.map((r) =>
        typeof r === 'string' ? { strategy: r, description: '' } : r,
      );
    }
    td.performanceQuality = pq;
  }

  // epics[].requirements: string → {title, description}
  if (Array.isArray(td.epics)) {
    td.epics = td.epics.map((ep) => {
      if (!ep || !Array.isArray(ep.requirements)) return ep;
      return {
        ...ep,
        requirements: ep.requirements.map((r) =>
          typeof r === 'string' ? { title: r, description: '' } : r,
        ),
      };
    });
  }

  // apiDomains: description → summary
  if (Array.isArray(td.apiDomains)) {
    td.apiDomains = td.apiDomains.map((r) =>
      r && typeof r === 'object' && !r.summary && r.description
        ? { ...r, summary: r.description }
        : r,
    );
  }

  // decisions: rationale → reason, add alternative
  if (Array.isArray(td.decisions)) {
    td.decisions = td.decisions.map((r) => {
      if (!r || typeof r !== 'object') return r;
      const out = { ...r };
      if (!out.reason && out.rationale) out.reason = out.rationale;
      if (out.alternative === undefined) out.alternative = '';
      return out;
    });
  }

  // integrations.included / excluded: string → structured objects
  if (td.integrations && typeof td.integrations === 'object') {
    const integ = { ...td.integrations };
    if (Array.isArray(integ.included)) {
      integ.included = integ.included.map((r) =>
        typeof r === 'string'
          ? { service: r, provider: '', connection: '', dataExchange: '', accountOwner: '' }
          : r,
      );
    }
    if (Array.isArray(integ.excluded)) {
      integ.excluded = integ.excluded.map((r) =>
        typeof r === 'string' ? { service: r, reason: '', availability: '' } : r,
      );
    }
    td.integrations = integ;
  }

  // growthReadiness.strategies: string → {dimension, preparation, evolution}
  if (td.growthReadiness && typeof td.growthReadiness === 'object') {
    const gr = { ...td.growthReadiness };
    if (Array.isArray(gr.strategies)) {
      gr.strategies = gr.strategies.map((r) =>
        typeof r === 'string' ? { dimension: '', preparation: r, evolution: '' } : r,
      );
    }
    td.growthReadiness = gr;
  }

  // architecture.patterns: string → {component, pattern, description}
  if (td.architecture && typeof td.architecture === 'object') {
    const arch = { ...td.architecture };
    if (Array.isArray(arch.patterns)) {
      arch.patterns = arch.patterns.map((r) =>
        typeof r === 'string' ? { component: '', pattern: '', description: r } : r,
      );
    }
    td.architecture = arch;
  }

  // quality.dimensions / testTypes: string → structured objects
  if (td.quality && typeof td.quality === 'object') {
    const q = { ...td.quality };
    if (Array.isArray(q.dimensions)) {
      q.dimensions = q.dimensions.map((r) =>
        typeof r === 'string' ? { dimension: r, evaluates: '', standard: '' } : r,
      );
    }
    if (Array.isArray(q.testTypes)) {
      q.testTypes = q.testTypes.map((r) =>
        typeof r === 'string' ? { type: r, validates: '', tool: '', whenRun: '' } : r,
      );
    }
    td.quality = q;
  }

  // environments: description → purpose
  if (Array.isArray(td.environments)) {
    td.environments = td.environments.map((r) =>
      r && typeof r === 'object' && !r.purpose && r.description
        ? { ...r, purpose: r.description }
        : r,
    );
  }

  return { ...proposalJson, technicalDocument: td };
}

/**
 * Migrates a legacy proposal JSON and triggers a browser download of the corrected file.
 * Generates the filename from the client name in the JSON.
 *
 * @param {object|null} proposalJson — parsed proposal JSON (camelCase, pre-import format)
 */
export function downloadMigratedProposalJson(proposalJson) {
  if (!proposalJson) return;
  const migrated = migrateLegacyProposalJson(proposalJson);
  const clientName = migrated.general?.clientName || 'propuesta';
  const slug = clientName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  const blob = new Blob([JSON.stringify(migrated, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proposal-${slug}-v2.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 100);
}

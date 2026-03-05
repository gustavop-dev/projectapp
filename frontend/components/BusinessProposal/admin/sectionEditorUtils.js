/**
 * Pure utility functions for SectionEditor.vue.
 *
 * Extracted to enable unit testing of JSON serialization/deserialization
 * logic without mounting Vue components.
 */

/**
 * Join an array into newline-separated text.
 * @param {Array|string} arr
 * @returns {string}
 */
export function arrToText(arr) {
  return Array.isArray(arr) ? arr.join('\n') : (arr || '');
}

/**
 * Split newline-separated text into a trimmed, non-empty array.
 * @param {string} text
 * @returns {string[]}
 */
export function textToArr(text) {
  if (!text) return [];
  return text.split('\n').map(l => l.trim()).filter(Boolean);
}

/**
 * Build a reactive form object from a section's content_json.
 * @param {object} json - The content_json from the backend.
 * @param {string} type - The section_type.
 * @param {object} [proposalData] - Optional parent proposal data for defaults.
 * @returns {object}
 */
export function buildFormFromJson(json, type, proposalData) {
  const j = json || {};
  switch (type) {
    case 'greeting':
      return { clientName: j.clientName || proposalData?.client_name || '', inspirationalQuote: j.inspirationalQuote || '' };
    case 'executive_summary':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), highlightsTitle: j.highlightsTitle || '', highlights: arrToText(j.highlights) };
    case 'context_diagnostic':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), issuesTitle: j.issuesTitle || '', issues: arrToText(j.issues), opportunityTitle: j.opportunityTitle || '', opportunity: j.opportunity || '' };
    case 'conversion_strategy':
      return { index: j.index || '', title: j.title || '', intro: j.intro || '', steps: (j.steps || []).map(s => ({ title: s.title || '', bullets: arrToText(s.bullets) })), resultTitle: j.resultTitle || '', result: j.result || '' };
    case 'design_ux':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), focusTitle: j.focusTitle || '', focusItems: arrToText(j.focusItems), objectiveTitle: j.objectiveTitle || '', objective: j.objective || '' };
    case 'creative_support':
      return { index: j.index || '', title: j.title || '', paragraphs: arrToText(j.paragraphs), includesTitle: j.includesTitle || '', includes: arrToText(j.includes), closing: j.closing || '' };
    case 'development_stages':
      return { stages: (j.stages || []).map(s => ({ icon: s.icon || '', title: s.title || '', description: s.description || '', current: !!s.current })) };
    case 'functional_requirements':
      return {
        index: j.index || '', title: j.title || '', intro: j.intro || '',
        groups: (j.groups || []).map(g => ({
          id: g.id || '', icon: g.icon || '', title: g.title || '',
          description: g.description || '',
          items: (g.items || []).map(i => ({ icon: i.icon || '', name: i.name || '', description: i.description || '' })),
          _pasteMode: g._editMode === 'paste', _pasteText: g.rawText || '', _collapsed: true,
        })),
        additionalModules: (j.additionalModules || []).map(m => ({
          icon: m.icon || '', title: m.title || '', description: m.description || '',
          items: (m.items || []).map(i => ({ icon: i.icon || '', name: i.name || '', description: i.description || '' })),
          _pasteMode: m._editMode === 'paste', _pasteText: m.rawText || '', _collapsed: true,
        })),
      };
    case 'timeline':
      return { index: j.index || '', title: j.title || '', introText: j.introText || '', totalDuration: j.totalDuration || '', phases: (j.phases || []).map(p => ({ title: p.title || '', duration: p.duration || '', description: p.description || '', tasks: arrToText(p.tasks), milestone: p.milestone || '' })) };
    case 'investment':
      return { index: j.index || '', title: j.title || '', introText: j.introText || '', totalInvestment: j.totalInvestment || '', currency: j.currency || 'COP', whatsIncluded: (j.whatsIncluded || []).map(i => ({ ...i })), paymentOptions: (j.paymentOptions || []).map(o => ({ ...o })), hostingPlan: j.hostingPlan || {}, paymentMethods: arrToText(j.paymentMethods), valueReasons: arrToText(j.valueReasons) };
    case 'final_note':
      return { index: j.index || '', title: j.title || '', message: j.message || '', personalNote: j.personalNote || '', teamName: j.teamName || '', teamRole: j.teamRole || '', contactEmail: j.contactEmail || '', commitmentBadges: (j.commitmentBadges || []).map(b => ({ ...b })), validityMessage: j.validityMessage || '', thankYouMessage: j.thankYouMessage || '' };
    case 'next_steps':
      return { index: j.index || '', title: j.title || '', introMessage: j.introMessage || '', steps: (j.steps || []).map(s => ({ ...s })), ctaMessage: j.ctaMessage || '', primaryCTA: { text: j.primaryCTA?.text || '', link: j.primaryCTA?.link || '' }, secondaryCTA: { text: j.secondaryCTA?.text || '', link: j.secondaryCTA?.link || '' }, contactMethods: (j.contactMethods || []).map(m => ({ ...m })), validityMessage: j.validityMessage || '', thankYouMessage: j.thankYouMessage || '' };
    default:
      return {};
  }
}

/**
 * Convert form state back to content_json for saving.
 * @param {object} formData - The reactive form object.
 * @param {string} type - The section_type.
 * @returns {object}
 */
export function formToJson(formData, type) {
  const f = formData;
  switch (type) {
    case 'greeting':
      return { clientName: f.clientName, inspirationalQuote: f.inspirationalQuote };
    case 'executive_summary':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), highlightsTitle: f.highlightsTitle, highlights: textToArr(f.highlights) };
    case 'context_diagnostic':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), issuesTitle: f.issuesTitle, issues: textToArr(f.issues), opportunityTitle: f.opportunityTitle, opportunity: f.opportunity };
    case 'conversion_strategy':
      return { index: f.index, title: f.title, intro: f.intro, steps: f.steps.map(s => ({ title: s.title, bullets: textToArr(s.bullets) })), resultTitle: f.resultTitle, result: f.result };
    case 'design_ux':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), focusTitle: f.focusTitle, focusItems: textToArr(f.focusItems), objectiveTitle: f.objectiveTitle, objective: f.objective };
    case 'creative_support':
      return { index: f.index, title: f.title, paragraphs: textToArr(f.paragraphs), includesTitle: f.includesTitle, includes: textToArr(f.includes), closing: f.closing };
    case 'development_stages':
      return { stages: f.stages.map(s => ({ icon: s.icon, title: s.title, description: s.description, ...(s.current ? { current: true } : {}) })) };
    case 'functional_requirements': {
      const cleanGroup = (g) => {
        const out = {
          id: g.id, icon: g.icon, title: g.title, description: g.description,
          items: (g.items || []).map(i => ({ icon: i.icon, name: i.name, description: i.description })),
        };
        if (g._pasteMode) {
          out._editMode = 'paste';
          out.rawText = g._pasteText || '';
        } else {
          out._editMode = 'form';
        }
        return out;
      };
      return {
        index: f.index, title: f.title, intro: f.intro,
        groups: (f.groups || []).map(cleanGroup),
        additionalModules: (f.additionalModules || []).map(cleanGroup),
      };
    }
    case 'timeline':
      return { index: f.index, title: f.title, introText: f.introText, totalDuration: f.totalDuration, phases: f.phases.map(p => ({ title: p.title, duration: p.duration, description: p.description, tasks: textToArr(p.tasks), milestone: p.milestone })) };
    case 'investment':
      return { index: f.index, title: f.title, introText: f.introText, totalInvestment: f.totalInvestment, currency: f.currency, whatsIncluded: f.whatsIncluded, paymentOptions: f.paymentOptions, hostingPlan: f.hostingPlan || {}, paymentMethods: textToArr(f.paymentMethods), valueReasons: textToArr(f.valueReasons) };
    case 'final_note':
      return { index: f.index, title: f.title, message: f.message, personalNote: f.personalNote, teamName: f.teamName, teamRole: f.teamRole, contactEmail: f.contactEmail, commitmentBadges: f.commitmentBadges, validityMessage: f.validityMessage, thankYouMessage: f.thankYouMessage };
    case 'next_steps':
      return { index: f.index, title: f.title, introMessage: f.introMessage, steps: f.steps, ctaMessage: f.ctaMessage, primaryCTA: f.primaryCTA, secondaryCTA: f.secondaryCTA, contactMethods: f.contactMethods, validityMessage: f.validityMessage, thankYouMessage: f.thankYouMessage };
    default:
      return {};
  }
}

/**
 * Convert form state to human-readable text for paste mode pre-fill.
 * @param {object} form - The reactive form object.
 * @param {string} type - The section_type.
 * @returns {string}
 */
export function formToReadableText(form, type) {
  const parts = [];
  const bullet = (items) => items.split('\n').filter(Boolean).map(l => `- ${l}`).join('\n');
  if (type === 'greeting') {
    if (form.clientName) parts.push(`Nombre del cliente: ${form.clientName}`);
    if (form.inspirationalQuote) parts.push(`\n"${form.inspirationalQuote}"`);
  } else if (type === 'executive_summary') {
    if (form.paragraphs) parts.push(form.paragraphs);
    if (form.highlightsTitle) parts.push(`\n${form.highlightsTitle}`);
    if (form.highlights) parts.push(bullet(form.highlights));
  } else if (type === 'context_diagnostic') {
    if (form.paragraphs) parts.push(form.paragraphs);
    if (form.issuesTitle) parts.push(`\n${form.issuesTitle}`);
    if (form.issues) parts.push(bullet(form.issues));
    if (form.opportunityTitle) parts.push(`\n${form.opportunityTitle}`);
    if (form.opportunity) parts.push(form.opportunity);
  } else if (type === 'conversion_strategy') {
    if (form.intro) parts.push(form.intro);
    for (const step of (form.steps || [])) {
      if (step.title) parts.push(`\n${step.title}`);
      if (step.bullets) parts.push(bullet(step.bullets));
    }
    if (form.resultTitle) parts.push(`\n${form.resultTitle}`);
    if (form.result) parts.push(form.result);
  } else if (type === 'design_ux') {
    if (form.paragraphs) parts.push(form.paragraphs);
    if (form.focusTitle) parts.push(`\n${form.focusTitle}`);
    if (form.focusItems) parts.push(bullet(form.focusItems));
    if (form.objectiveTitle) parts.push(`\n${form.objectiveTitle}`);
    if (form.objective) parts.push(form.objective);
  } else if (type === 'creative_support') {
    if (form.paragraphs) parts.push(form.paragraphs);
    if (form.includesTitle) parts.push(`\n${form.includesTitle}`);
    if (form.includes) parts.push(bullet(form.includes));
    if (form.closing) parts.push(`\n${form.closing}`);
  } else if (type === 'functional_requirements') {
    if (form.intro) parts.push(form.intro);
  } else if (type === 'development_stages') {
    for (const s of (form.stages || [])) {
      parts.push(`${s.icon || ''} ${s.title}${s.current ? ' (actual)' : ''}`);
      if (s.description) parts.push(`  ${s.description}`);
    }
  } else if (type === 'timeline') {
    if (form.introText) parts.push(form.introText);
    if (form.totalDuration) parts.push(`Duración total: ${form.totalDuration}`);
    for (const p of (form.phases || [])) {
      parts.push(`\n${p.title} — ${p.duration || ''}`);
      if (p.description) parts.push(p.description);
      if (p.tasks) parts.push(bullet(p.tasks));
      if (p.milestone) parts.push(`Hito: ${p.milestone}`);
    }
  } else if (type === 'investment') {
    if (form.introText) parts.push(form.introText);
    if (form.totalInvestment) parts.push(`Inversión total: ${form.totalInvestment} ${form.currency || 'COP'}`);
    if (form.whatsIncluded?.length) {
      parts.push('\nQué incluye:');
      for (const i of form.whatsIncluded) parts.push(`${i.icon || ''} ${i.title}: ${i.description || ''}`);
    }
    if (form.paymentOptions?.length) {
      parts.push('\nOpciones de pago:');
      for (const o of form.paymentOptions) parts.push(`- ${o.label}: ${o.description || ''}`);
    }
    if (form.valueReasons) parts.push(`\nRazones de valor:\n${bullet(form.valueReasons)}`);
  } else if (type === 'final_note') {
    if (form.message) parts.push(form.message);
    if (form.personalNote) parts.push(`\n${form.personalNote}`);
    if (form.teamName) parts.push(`\n${form.teamName} — ${form.teamRole || ''}`);
    if (form.contactEmail) parts.push(form.contactEmail);
    if (form.validityMessage) parts.push(`\nValidez: ${form.validityMessage}`);
    if (form.thankYouMessage) parts.push(`\n${form.thankYouMessage}`);
    if (form.commitmentBadges?.length) {
      parts.push('\nBadges:');
      for (const b of form.commitmentBadges) parts.push(`${b.icon || ''} ${b.title}: ${b.description || ''}`);
    }
  } else if (type === 'next_steps') {
    if (form.introMessage) parts.push(form.introMessage);
    if (form.steps?.length) {
      parts.push('\nPasos:');
      for (const s of form.steps) parts.push(`- ${s.title}: ${s.description || ''}`);
    }
    if (form.ctaMessage) parts.push(`\n${form.ctaMessage}`);
    if (form.contactMethods?.length) {
      parts.push('\nContacto:');
      for (const m of form.contactMethods) parts.push(`${m.icon || ''} ${m.title}: ${m.value || ''}`);
    }
    if (form.validityMessage) parts.push(`\nValidez: ${form.validityMessage}`);
    if (form.thankYouMessage) parts.push(`\n${form.thankYouMessage}`);
  }
  return parts.join('\n').trim();
}

/**
 * Convert a group's form data to human-readable text.
 * @param {object} group - A functional_requirements group object.
 * @returns {string}
 */
export function groupToReadableText(group) {
  const parts = [];
  if (group.description) parts.push(group.description);
  for (const item of (group.items || [])) {
    parts.push(`- ${item.icon || ''} **${item.name}**: ${item.description || ''}`);
  }
  return parts.join('\n').trim();
}

/**
 * Build the save payload from form state, applying paste mode metadata.
 * @param {object} form - The reactive form object.
 * @param {string} sectionType - The section_type.
 * @param {boolean} pasteMode - Whether paste mode is active.
 * @param {string} pasteText - The raw paste text.
 * @param {string} sectionTitle - The section title.
 * @param {boolean} isWidePanel - The is_wide_panel flag.
 * @param {number} sectionId - The section ID.
 * @returns {{ sectionId: number, payload: object }}
 */
export function buildSavePayload(form, sectionType, pasteMode, pasteText, sectionTitle, isWidePanel, sectionId) {
  const contentJson = formToJson(form, sectionType);
  if (pasteMode) {
    contentJson._editMode = 'paste';
    contentJson.rawText = pasteText;
  } else {
    contentJson._editMode = 'form';
    delete contentJson.rawText;
  }
  return {
    sectionId,
    payload: {
      title: sectionTitle,
      is_wide_panel: isWidePanel,
      content_json: contentJson,
    },
  };
}

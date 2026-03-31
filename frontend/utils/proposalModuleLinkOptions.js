/**
 * Build { id, label } options for linking technical requirements to commercial modules.
 * Ids match proposal public calculator: module-*, group-*, or investment module id string.
 *
 * @param {Array<{ section_type?: string, content_json?: object }>} sections
 * @returns {{ id: string, label: string }[]}
 */
export function buildProposalModuleLinkOptions(sections) {
  const out = [];
  if (!Array.isArray(sections)) return out;

  const fr = sections.find((s) => s.section_type === 'functional_requirements');
  const inv = sections.find((s) => s.section_type === 'investment');
  const cj = fr?.content_json || {};
  const groups = [...(cj.groups || []), ...(cj.additionalModules || [])];

  for (const g of groups) {
    if (!g || g.is_visible === false) continue;
    if (!g.title && !(g.items || []).length) continue;
    const isCalc = g.is_calculator_module === true;
    const pp = g.price_percent ?? 0;
    if (!isCalc && pp <= 0) continue;
    const id = isCalc ? `module-${g.id}` : `group-${g.id}`;
    const label = `${g.icon || ''} ${g.title || g.id}`.trim();
    out.push({ id, label });
  }

  for (const m of inv?.content_json?.modules || []) {
    if (m == null || m.id == null || String(m.id).length === 0) continue;
    const id = String(m.id);
    const label = `${m.icon || ''} ${m.title || id}`.trim();
    out.push({ id, label });
  }

  return out;
}

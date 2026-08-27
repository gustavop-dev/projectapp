const REQUIRED_VIEW_FIELDS = Object.freeze([
  'label',
  'url',
  'group',
  'file',
  'reference',
  'audience',
  'viewType',
])

function duplicateValues(entries, field) {
  const occurrences = new Map()
  for (const entry of entries) {
    const value = entry[field]
    if (!value) continue
    const matches = occurrences.get(value) || []
    matches.push(entry)
    occurrences.set(value, matches)
  }
  return [...occurrences.entries()]
    .filter(([, matches]) => matches.length > 1)
    .map(([value, matches]) => ({
      value,
      entries: matches.map((entry) => `${entry.sectionId}:${entry.label}`),
    }))
}

export function routeFromPageFile(file) {
  const withoutPrefix = file
    .replace(/^frontend\/pages/, '')
    .replace(/\.vue$/, '')
    .replace(/\/index$/, '')

  const route = withoutPrefix
    .replace(/\[\.\.\.([^\]]+)\]/g, ':$1*')
    .replace(/\[([^\]]+)\]/g, ':$1')

  return route || '/'
}

export function auditViewCatalog({
  pageFiles,
  sections,
  validAudiences,
  validViewTypes,
}) {
  const pages = [...new Set(pageFiles)].sort()
  const entries = sections.flatMap((section) => section.views.map((view) => ({
    ...view,
    sectionId: section.id,
  })))
  const pageSet = new Set(pages)
  const catalogFileSet = new Set(entries.map((entry) => entry.file))
  const audienceSet = new Set(validAudiences)
  const viewTypeSet = new Set(validViewTypes)
  const usedAudiences = new Set(entries.map((entry) => entry.audience))
  const usedViewTypes = new Set(entries.map((entry) => entry.viewType))

  return {
    pageCount: pages.length,
    entryCount: entries.length,
    orphanPages: pages.filter((file) => !catalogFileSet.has(file)),
    staleEntries: entries
      .filter((entry) => !pageSet.has(entry.file))
      .map((entry) => ({ sectionId: entry.sectionId, label: entry.label, file: entry.file })),
    duplicateUrls: duplicateValues(entries, 'url'),
    duplicateFiles: duplicateValues(entries, 'file'),
    routeMismatches: entries
      .filter((entry) => routeFromPageFile(entry.file) !== entry.url)
      .map((entry) => ({
        sectionId: entry.sectionId,
        label: entry.label,
        expected: routeFromPageFile(entry.file),
        actual: entry.url,
      })),
    invalidMetadata: entries
      .filter((entry) => (
        !audienceSet.has(entry.audience)
        || !viewTypeSet.has(entry.viewType)
      ))
      .map((entry) => ({
        sectionId: entry.sectionId,
        label: entry.label,
        audience: entry.audience,
        viewType: entry.viewType,
      })),
    unusedAudiences: validAudiences.filter((value) => !usedAudiences.has(value)),
    unusedViewTypes: validViewTypes.filter((value) => !usedViewTypes.has(value)),
    missingFields: entries
      .map((entry) => ({
        sectionId: entry.sectionId,
        label: entry.label || '(sin etiqueta)',
        fields: REQUIRED_VIEW_FIELDS.filter((field) => (
          typeof entry[field] !== 'string' || entry[field].trim().length === 0
        )),
      }))
      .filter((entry) => entry.fields.length > 0),
  }
}

export function catalogAuditFindings(report) {
  return [
    ...report.orphanPages.map((file) => `Página sin catalogar: ${file}`),
    ...report.staleEntries.map((entry) => `Entrada obsoleta: ${entry.file}`),
    ...report.duplicateUrls.map((entry) => `URL duplicada: ${entry.value}`),
    ...report.duplicateFiles.map((entry) => `Archivo duplicado: ${entry.value}`),
    ...report.routeMismatches.map((entry) => (
      `Ruta desalineada: ${entry.actual} debería ser ${entry.expected}`
    )),
    ...report.invalidMetadata.map((entry) => (
      `Metadata inválida: ${entry.sectionId}:${entry.label}`
    )),
    ...report.unusedAudiences.map((value) => `Filtro de audiencia sin vistas: ${value}`),
    ...report.unusedViewTypes.map((value) => `Filtro de tipo sin vistas: ${value}`),
    ...report.missingFields.map((entry) => (
      `Campos faltantes: ${entry.sectionId}:${entry.label} (${entry.fields.join(', ')})`
    )),
  ]
}

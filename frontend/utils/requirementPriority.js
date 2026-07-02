/**
 * Shared i18n labels for technical requirement priorities.
 * Used by the technical public panel and the commercial
 * linked-requirements modal so both render the same wording.
 */
export const PRIORITY_I18N = {
  es: { critical: 'Crítico', high: 'Alta', medium: 'Media', low: 'Baja' },
  en: { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' },
};

export function priorityLabel(priority, language = 'es') {
  const map = PRIORITY_I18N[language] || PRIORITY_I18N.es;
  return map[priority] || priority || '';
}

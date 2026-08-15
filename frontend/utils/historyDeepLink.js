/**
 * Link to the send log already narrowed to one record.
 *
 * "What has gone out about this?" is the question the Historial tab gets
 * asked most, and answering it used to mean rebuilding the filter by hand.
 * The route carries plain filter keys — the same ones the page writes when
 * you filter by hand — so the link is readable and reproducible.
 */
export function historySendsLink(entityType, objectId) {
  return {
    path: '/panel/accounting/history',
    query: {
      tab: 'sends',
      entity_type: entityType,
      object_id: String(objectId),
    },
  };
}

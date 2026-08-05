/**
 * Suggest which registered client a free-text name refers to.
 *
 * Hosting records predate the client relation and stored the client as a
 * hand-written label following the house convention `Persona - Marca`
 * ("German - Kore", "Jimmy & Daniel - Mimittos"). Neither half maps to a
 * single profile field: the left side is the person, the right side the
 * company. So both are tried, against both fields, accent- and case-blind.
 *
 * This only ever SUGGESTS: the operator confirms, and a wrong guess costs
 * one click to discard.
 */

/** Lowercase, without accents, single-spaced — what comparisons run on. */
export function normalizeName(value) {
  return String(value ?? '')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9& ]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** The `Persona - Marca` halves, plus the whole string, all normalized. */
export function nameParts(value) {
  const whole = normalizeName(value);
  if (!whole) return [];
  const halves = String(value).split(' - ').map(normalizeName).filter(Boolean);
  return [...new Set([whole, ...halves])];
}

function candidateNames(client) {
  return [client?.company, client?.name].map(normalizeName).filter(Boolean);
}

/**
 * Best match for `clientName` among `clients`, or null.
 *
 * Exact equality on a whole side wins over a containment match, so
 * "Mimittos" pairs with the MIMITTOS company before any looser hit. Ties
 * and near-misses resolve to null on purpose: a doubtful suggestion is
 * worse than none, because it invites a confirming click on a wrong pair.
 */
export function suggestClient(clientName, clients = []) {
  const parts = nameParts(clientName);
  if (!parts.length || !clients.length) return null;

  let contained = null;
  for (const client of clients) {
    for (const candidate of candidateNames(client)) {
      if (parts.includes(candidate)) return client;
      const hit = parts.some(
        (part) => part.length >= 4
          && (part.includes(candidate) || candidate.includes(part)),
      );
      if (hit && !contained) contained = client;
    }
  }
  return contained;
}

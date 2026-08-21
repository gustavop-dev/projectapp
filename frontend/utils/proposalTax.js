const TAX_TOKEN_RE = /\b(?:iva|tax)\b/i;
const MONETARY_VALUE_RE = /\d/;

export function proposalTaxLabel(currency = 'COP') {
  return String(currency || 'COP').trim().toUpperCase() === 'USD'
    ? '+ Tax'
    : '+ IVA';
}

export function ensureProposalTaxLabel(value, currency = 'COP') {
  const text = String(value ?? '').trim();
  if (!text || !MONETARY_VALUE_RE.test(text) || TAX_TOKEN_RE.test(text)) return text;
  return `${text} ${proposalTaxLabel(currency)}`;
}

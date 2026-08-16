/**
 * Listas en español para la UI del panel.
 *
 * Existe por el aviso de cambios sin guardar: nombrar los campos exige unirlos
 * como los uniría una persona ("cliente y proyecto"), no con un join crudo.
 */

/**
 * La conjunción "y" pasa a "e" ante palabra que empieza por i-/hi- (RAE),
 * salvo diptongo (hie-, hia-): "cliente e idioma", pero "agua y hielo".
 */
export function conjunction(word) {
  const w = String(word || '').trim().toLowerCase();
  // "hielo"/"hiato": el diptongo suena distinto y conserva la "y".
  if (/^hi[ae]/.test(w)) return 'y';
  // i- o hi-, con o sin tilde. La clase acepta la í precompuesta y, si el texto
  // viniera descompuesto, igual entra por la "i" que precede a la tilde.
  if (/^h?[ií]/.test(w)) return 'e';
  return 'y';
}

/** ["cliente"] -> "cliente"; ["cliente","proyecto"] -> "cliente y proyecto". */
export function joinEs(items) {
  const list = (items || []).filter(Boolean);
  if (list.length === 0) return '';
  if (list.length === 1) return list[0];
  const last = list[list.length - 1];
  return `${list.slice(0, -1).join(', ')} ${conjunction(last)} ${last}`;
}

export function capitalizeFirst(text) {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : '';
}

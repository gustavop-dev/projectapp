/**
 * Qué páginas va a traer el PDF de un documento, dicho en la propia pantalla.
 *
 * Las casillas de exportación sólo se podían verificar bajando el archivo: el
 * PDF lo arma el servidor y la vista previa de markdown no muestra portadas.
 * Esta línea traduce el estado VIVO del formulario —guardado o no— a la lista
 * de páginas, para que el efecto de desmarcar una casilla se vea al instante.
 */

/** El contenido siempre está: sin bloques no hay PDF que descargar. */
export const CONTENT_PAGE = 'contenido';

/**
 * @param {object} form - { include_portada, include_subportada, include_contraportada }.
 * @returns {string[]} Páginas en el orden en que salen en el PDF.
 */
export function includedPages(form = {}) {
  return [
    form.include_portada ? 'portada' : null,
    form.include_subportada ? 'subportada' : null,
    CONTENT_PAGE,
    form.include_contraportada ? 'contraportada' : null,
  ].filter(Boolean);
}

/** "portada · contenido · contraportada" */
export function describeIncludedPages(form = {}) {
  return includedPages(form).join(' · ');
}

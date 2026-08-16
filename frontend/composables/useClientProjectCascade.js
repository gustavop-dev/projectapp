/**
 * La cascada cliente ↔ proyecto de los formularios del panel.
 *
 * Dos reglas que iban copiadas a mano en cada formulario que lleva el par:
 *
 * - Limpiar el cliente limpia el proyecto. Sin cliente el proyecto no se
 *   sostiene: el backend lo derivaría de vuelta desde el proyecto y la
 *   limpieza no habría limpiado nada.
 * - Elegir el proyecto primero completa el cliente solo (cascada inversa),
 *   pero nunca pisa un cliente ya elegido.
 *
 * El acotado de la lista de proyectos al cliente vive dentro de
 * `ProjectSelect.vue` y no se toca desde acá.
 *
 * @param {object} form Objeto reactivo con `client` (pk de UserProfile) y `project`.
 * @param {import('vue').Ref<string>} clientDisplayName Rótulo visible del cliente.
 * @param {{ onOperatorChoice?: () => void }} [options] `onOperatorChoice` avisa
 *   que el valor lo decidió el operador — es lo que permite a quien prellena
 *   (una carpeta, una sugerencia) dejar de proponer y no volver a pisarlo.
 */
export function useClientProjectCascade(form, clientDisplayName, options = {}) {
  const notifyChoice = () => options.onOperatorChoice?.();

  function onClientSelect(client) {
    notifyChoice();
    if (!client) {
      form.client = null;
      clientDisplayName.value = '';
      form.project = null;
      return;
    }
    form.client = client.id;
    clientDisplayName.value = client.name || '';
  }

  function onProjectSelect(row) {
    if (!row || !row.client_profile_id || form.client) return;
    form.client = row.client_profile_id;
    clientDisplayName.value = row.client_display_name || '';
    notifyChoice();
  }

  return { onClientSelect, onProjectSelect };
}

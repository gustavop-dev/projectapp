/**
 * Generic technical-document epic stub for an optional commercial module.
 * Shown in public view only when that module id is in the client's selection.
 *
 * @param {string} moduleId - e.g. module-12, group-34, or investment module id
 * @param {string} [label] - human label for titles (from FR/investment)
 */
export function createGenericTechnicalEpicStub(moduleId, label = '') {
  const short = label || moduleId;
  return {
    epicKey: '',
    title: `Alcance ampliado: ${short}`,
    description:
      'Bloque técnico preliminar vinculado a un módulo opcional de la propuesta comercial. '
      + 'Revise y complete el detalle antes de enviar al cliente.',
    linked_module_ids: [moduleId],
    requirements: [
      {
        flowKey: '',
        title: 'Funcionalidad del módulo opcional',
        description:
          'Descripción del comportamiento esperado una vez contratado este alcance. Sustituya este texto por el detalle real.',
        configuration:
          'Roles, permisos, datos maestros y parámetros: por definir con el cliente tras la firma.',
        usageFlow:
          'Pasos típicos de uso (p. ej. acceso → acción principal → resultado): completar según el módulo.',
        priority: '',
        linked_module_ids: [moduleId],
      },
    ],
  };
}

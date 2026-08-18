import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { capitalizeFirst, joinEs } from '~/utils/spanishList';

/** Más de esto y la lista deja de leerse: pasa a contarse. */
const MAX_NAMED = 3;

const LEAVE = {
  saveText: 'Guardar y salir',
  discardText: 'Salir sin guardar',
  tail: 'Si sales de esta página ahora, se pierden.',
};

const REFRESH = {
  saveText: 'Guardar y actualizar',
  discardText: 'Descartar y actualizar',
  tail: 'Actualizar vuelve a traer los datos del servidor y los reemplaza.',
};

// El archivo lo arma el servidor con lo GUARDADO. Sin este aviso, cambiar una
// opción de exportación y descargar entrega en silencio un archivo que no es
// el que la pantalla está mostrando.
const EXPORT_VERBS = {
  download: {
    saveText: 'Guardar y descargar',
    discardText: 'Descargar lo guardado',
    tail: 'La descarga se arma con la última versión guardada.',
  },
  preview: {
    saveText: 'Guardar y previsualizar',
    discardText: 'Previsualizar lo guardado',
    tail: 'La vista previa se arma con la última versión guardada.',
  },
};

/**
 * Aviso de cambios sin guardar para un editor de página completa del panel.
 *
 * Empaqueta las tres salidas por las que se pierde trabajo —navegar con el
 * router, cerrar la pestaña y el botón global de refrescar— detrás de un solo
 * modal de tres botones, y nombra QUÉ está sin guardar en vez de decir que
 * "algo" lo está: un aviso genérico se vuelve parte del paisaje.
 *
 * Dos fuentes de suciedad, excluyentes:
 *   - `snapshot()` -> objeto plano; se difiere contra la baseline por clave.
 *     Cubre tanto un `reactive` como refs sueltos.
 *   - `flags`      -> { clave: () => boolean } para páginas cuyo estado sucio
 *                     lo reportan sus hijos (propuestas no tiene formulario).
 *
 * Contrato de `save`: persiste y devuelve truthy en éxito. NO debe navegar —
 * se la llama desde dentro de un guard de navegación.
 */
export function useUnsavedGuard({
  snapshot = null,
  flags = null,
  labels = {},
  save = null,
  canSave = null,
  blockedReason = '',
  reload = null,
  discard = null,
  confirm = null,
} = {}) {
  // No hay <ConfirmModal> global: cada página monta el suyo. Una página que ya
  // llama useConfirmModal() inyecta su requestConfirm; crear un segundo
  // confirmState abriría un modal que nadie renderiza —falla en silencio—.
  const own = confirm ? null : useConfirmModal();
  const requestConfirm = confirm || own.requestConfirm;

  const baseline = ref(null);
  const warnedKeys = new Set();

  function readSnapshot() {
    const raw = (snapshot ? snapshot() : null) || {};
    const out = {};
    Object.keys(raw).forEach((key) => {
      out[key] = JSON.stringify(raw[key] ?? null);
    });
    return out;
  }

  /** Vuelve a fijar la baseline. Se llama tras cargar y tras guardar. */
  function commit() {
    if (snapshot) baseline.value = readSnapshot();
  }

  const dirtyKeys = computed(() => {
    if (flags) {
      return Object.keys(flags).filter((key) => {
        const flag = flags[key];
        return Boolean(typeof flag === 'function' ? flag() : flag?.value ?? flag);
      });
    }
    if (!baseline.value) return [];
    const current = readSnapshot();
    return Object.keys(current).filter((key) => current[key] !== baseline.value[key]);
  });

  const hasChanges = computed(() => dirtyKeys.value.length > 0);

  function isFieldDirty(key) {
    return dirtyKeys.value.includes(key);
  }

  const dirtyLabels = computed(() => dirtyKeys.value.map((key) => {
    if (labels[key]) return labels[key];
    // El requisito es nombrar el campo: una clave sin etiqueta es un bug de la
    // página que la monta, no un caso de uso. Se avisa una vez por clave.
    if (!warnedKeys.has(key)) {
      warnedKeys.add(key);
      console.warn(`[useUnsavedGuard] falta labels['${key}']`);
    }
    return key;
  }));

  /** "Cliente y proyecto sin guardar" · "5 campos sin guardar" */
  const unsavedTitle = computed(() => {
    const list = dirtyLabels.value;
    if (!list.length) return '';
    if (list.length <= MAX_NAMED) return capitalizeFirst(`${joinEs(list)} sin guardar`);
    return `${list.length} campos sin guardar`;
  });

  /** Sólo cuando el título dejó de nombrarlos uno por uno. */
  const unsavedDetail = computed(() => (
    dirtyLabels.value.length > MAX_NAMED
      ? `${capitalizeFirst(joinEs(dirtyLabels.value))}.`
      : ''
  ));

  const unsavedSummary = computed(() => (
    hasChanges.value ? `Sin guardar: ${joinEs(dirtyLabels.value)}.` : ''
  ));

  const canSaveNow = computed(
    () => typeof save === 'function' && (!canSave || Boolean(canSave())),
  );

  /**
   * Las tres salidas sobre una promesa booleana.
   *
   * La restricción vive en useConfirmModal: `handleSecondaryAction` resuelve
   * FALSE igual que Cancelar, y ~25 call sites dependen de esa semántica, así
   * que no se toca. El truco es que esa función es async y hace `await fn()`
   * ANTES de resolver: una bandera escrita por el callback ya está puesta
   * cuando vuelve el `await requestConfirm(...)`. El booleano sigue siendo el
   * booleano; el resultado se lee de las banderas.
   */
  async function confirmExit(verb) {
    if (!canSaveNow.value) {
      // Sin guardado posible no hay tres salidas que ofrecer: hay dos, y
      // decirlo es más honesto que un botón que fallaría.
      return requestConfirm({
        title: unsavedTitle.value || 'Cambios sin guardar',
        message: blockedReason
          ? `${blockedReason} ${unsavedSummary.value}`
          : `${unsavedSummary.value} ${verb.tail}`,
        variant: 'warning',
        confirmText: verb.discardText,
        cancelText: 'Seguir editando',
      });
    }

    let saved = false;
    let discarded = false;

    const confirmed = await requestConfirm({
      title: unsavedTitle.value,
      message: `${unsavedSummary.value} ${verb.tail}`,
      variant: 'warning',
      confirmText: verb.saveText,
      waitForConfirm: true,
      onConfirm: async () => { saved = Boolean(await save()); },
      secondaryText: verb.discardText,
      secondaryVariant: 'secondary',
      onSecondary: () => { discarded = true; },
      cancelText: 'Seguir editando',
    });

    // Guardar y que falle NO es salir: el error ya se notificó y la página se
    // queda donde está, con los cambios intactos.
    return confirmed ? saved : discarded;
  }

  onBeforeRouteLeave(async () => {
    if (!hasChanges.value) return true;
    return confirmExit(LEAVE);
  });

  function warnBeforeUnload(event) {
    if (!hasChanges.value) return;
    event.preventDefault();
    // Los navegadores ignoran el texto propio; returnValue es lo único que
    // sigue disparando el diálogo genérico.
    event.returnValue = '';
  }

  onMounted(() => {
    if (typeof window === 'undefined') return;
    window.addEventListener('beforeunload', warnBeforeUnload);
  });

  onBeforeUnmount(() => {
    if (typeof window === 'undefined') return;
    window.removeEventListener('beforeunload', warnBeforeUnload);
  });

  /**
   * El botón global de refrescar vuelve a pedir los datos y pisa el formulario
   * sin avisar. Se registra ESTO en usePanelRefresh, no el reload crudo.
   */
  async function guardedReload() {
    if (hasChanges.value && !(await confirmExit(REFRESH))) return;
    if (reload) await reload();
  }

  /**
   * Puerta para las acciones que consumen la versión GUARDADA (descargar el
   * PDF, previsualizarlo). Devuelve true cuando se puede seguir: o se guardó,
   * o se aceptó explícitamente usar lo guardado.
   */
  async function guardedExport(kind = 'download') {
    if (!hasChanges.value) return true;
    return confirmExit(EXPORT_VERBS[kind] || EXPORT_VERBS.download);
  }

  /** El botón "Descartar cambios" del aviso. */
  async function discardChanges() {
    if (!hasChanges.value) return;
    const ok = await requestConfirm({
      title: unsavedTitle.value,
      message: 'Se descartan y vuelve lo último guardado. No se puede deshacer.',
      variant: 'danger',
      confirmText: 'Descartar cambios',
      cancelText: 'Seguir editando',
    });
    if (!ok) return;
    const revert = discard || reload;
    if (revert) await revert();
  }

  return {
    hasChanges,
    dirtyKeys,
    dirtyLabels,
    isFieldDirty,
    unsavedTitle,
    unsavedDetail,
    unsavedSummary,
    canSaveNow,
    commit,
    guardedReload,
    guardedExport,
    discardChanges,
    // Sólo cuando la página no inyectó su propio requestConfirm.
    confirmState: own?.confirmState,
    handleConfirmed: own?.handleConfirmed,
    handleSecondaryAction: own?.handleSecondaryAction,
    handleCancelled: own?.handleCancelled,
  };
}

import { watch } from 'vue';

import { usePersistedRef } from '~/composables/usePersistedRef';

export const SIDEBAR_SECTIONS_KEY = 'projectapp-documents-sidebar-sections';

// Abiertas por defecto: es lo que hacían los `<details open>` que reemplazan, y
// entrar al gestor con el panel plegado escondería la navegación sin que nadie
// la haya plegado. Recoger es una decisión del usuario, y se recuerda.
const DEFAULTS = { entities: true, manual: true };

// El estado vive a nivel de MÓDULO, no dentro de la función: el panel se monta
// dos veces a la vez —fijo en escritorio y dentro del drawer en táctil— y dos
// refs independientes harían que plegar en uno no se viera en el otro.
const { ref: sections, write } = usePersistedRef(SIDEBAR_SECTIONS_KEY, { ...DEFAULTS });

// Un storage viejo, a medias o manipulado no puede dejar una sección sin valor:
// se completa contra el default en vez de rendir `undefined` a `:open`.
sections.value = { ...DEFAULTS, ...(sections.value || {}) };

watch(sections, write, { deep: true });

/**
 * Secciones plegables del panel lateral del gestor documental.
 *
 * El panel crecía a lo alto sin techo —navegación por entidad más carpetas
 * propias— y desbalanceaba la tabla de la derecha. `toggle` es lo único que
 * necesita el consumidor; el trigger accesible vive en el componente, como
 * pide `BaseCollapse`.
 */
export function useFolderSidebarSections() {
  function toggle(name) {
    sections.value = { ...sections.value, [name]: !sections.value[name] };
  }

  return { sections, toggle };
}

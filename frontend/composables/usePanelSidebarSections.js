import { watch } from 'vue';

import { usePersistedRef } from '~/composables/usePersistedRef';

// Un store por clave, creado la primera vez que un módulo la pide. El estado
// vive a nivel de MÓDULO y no dentro de la función porque cada panel se monta
// dos veces a la vez —fijo en escritorio y dentro del drawer en táctil— y dos
// refs independientes harían que plegar en uno no se viera en el otro.
const stores = new Map();

function storeFor(key, defaults) {
  if (stores.has(key)) return stores.get(key);

  const { ref: sections, write } = usePersistedRef(key, { ...defaults });
  // Un storage viejo, a medias o manipulado no puede dejar una sección sin
  // valor: se completa contra el default en vez de rendir `undefined` a `:open`.
  sections.value = { ...defaults, ...(sections.value || {}) };
  watch(sections, write, { deep: true });

  const store = {
    sections,
    toggle(name) {
      sections.value = { ...sections.value, [name]: !sections.value[name] };
    },
  };
  stores.set(key, store);
  return store;
}

/**
 * Secciones plegables del panel lateral de un módulo del panel.
 *
 * Los paneles laterales crecen a lo alto sin techo —navegación por entidad más
 * las secciones propias del módulo— y desbalancean la tabla de la derecha. El
 * pliegue se recuerda por navegador; `toggle` es lo único que necesita el
 * consumidor, porque el trigger accesible vive en el componente, como pide
 * `BaseCollapse`.
 *
 * Abiertas por defecto: entrar al módulo con el panel plegado escondería la
 * navegación sin que nadie la haya plegado. Recoger es decisión del usuario.
 *
 * @param {string} key       clave de localStorage, propia de cada módulo
 * @param {object} defaults  secciones y su estado inicial
 */
export function usePanelSidebarSections(key, defaults) {
  return storeFor(key, defaults);
}

import { usePanelSidebarSections } from '~/composables/usePanelSidebarSections';

export const SIDEBAR_SECTIONS_KEY = 'projectapp-documents-sidebar-sections';

const DEFAULTS = { entities: true, manual: true };

/**
 * Secciones plegables del panel lateral del gestor documental.
 *
 * Envoltorio con la clave y los defaults de este módulo sobre
 * `usePanelSidebarSections`, que es el mismo mecanismo que usa comunicaciones.
 */
export function useFolderSidebarSections() {
  return usePanelSidebarSections(SIDEBAR_SECTIONS_KEY, DEFAULTS);
}

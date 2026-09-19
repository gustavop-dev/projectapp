import { useNuxtApp } from '#imports'
import { createPanelPwa } from '~/utils/panelPwa'

export function usePanelPwa() {
  return useNuxtApp().$panelPwa || createPanelPwa()
}

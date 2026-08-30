import { ref, watch } from 'vue'

import { usePersistedRef } from '~/composables/usePersistedRef'

export const ADDITIONAL_MODULE_VIEW_MODES = ['cards', 'list', 'accordion']

export function useAdditionalModulesViewMode(scope = 'public') {
  const safeScope = scope === 'panel' ? 'panel' : 'public'
  const persisted = usePersistedRef(
    `projectapp-additional-modules-view-mode-${safeScope}`,
    'cards',
  )
  const initial = ADDITIONAL_MODULE_VIEW_MODES.includes(persisted.ref.value)
    ? persisted.ref.value
    : 'cards'
  const viewMode = ref(initial)

  watch(viewMode, (mode) => {
    persisted.write(ADDITIONAL_MODULE_VIEW_MODES.includes(mode) ? mode : 'cards')
  })

  return { viewMode }
}

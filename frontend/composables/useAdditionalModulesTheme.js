import { usePublicDocumentTheme } from '~/composables/usePublicDocumentTheme'

export const ADDITIONAL_MODULES_THEME_STORAGE_KEY = 'projectapp-additional-modules-theme'

export function useAdditionalModulesTheme() {
  return usePublicDocumentTheme(ADDITIONAL_MODULES_THEME_STORAGE_KEY)
}

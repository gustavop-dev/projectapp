import { usePublicDocumentTheme } from '~/composables/usePublicDocumentTheme'

export const FINANCING_THEME_STORAGE_KEY = 'projectapp-financing-theme'

export function useFinancingTheme() {
  return usePublicDocumentTheme(FINANCING_THEME_STORAGE_KEY)
}

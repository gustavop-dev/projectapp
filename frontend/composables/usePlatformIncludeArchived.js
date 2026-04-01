/**
 * Estado compartido (Nuxt useState): admin activa "Mostrar archivados" para
 * listados GET con include_archived=1 y coherencia entre tablero / proyecto / dashboard.
 */
export function usePlatformIncludeArchived() {
  return useState('platform-admin-include-archived', () => false)
}

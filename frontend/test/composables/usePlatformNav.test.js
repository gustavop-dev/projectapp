/**
 * Tests for usePlatformNav — la fuente única de navegación de la plataforma.
 *
 * Protege contra la regresión que motivó este composable: el sidebar desktop
 * y el drawer móvil tenían la nav duplicada y derivaron (el drawer seguía
 * enlazando Dashboard y los módulos globales que el refactor de IA convirtió
 * en redirects).
 */

global.useLocalePath = jest.fn(() => (path) => path)
global.useRoute = jest.fn(() => ({ path: '/platform/projects' }))

const mockAuth = { isAdmin: false }
jest.mock('../../stores/platform-auth', () => ({
  usePlatformAuthStore: jest.fn(() => mockAuth),
}))
jest.mock('../../stores/platform-notifications', () => ({
  usePlatformNotificationsStore: jest.fn(() => ({ unreadCount: 5 })),
}))

import { usePlatformNav } from '../../composables/usePlatformNav'

describe('usePlatformNav', () => {
  beforeEach(() => {
    mockAuth.isAdmin = false
    global.useRoute = jest.fn(() => ({ path: '/platform/projects' }))
  })

  it('expone Notificaciones y Proyectos para cualquier rol', () => {
    const { primaryItems } = usePlatformNav()
    const labels = primaryItems.value.map((i) => i.label)
    expect(labels).toContain('Notificaciones')
    expect(labels).toContain('Proyectos')
  })

  it('oculta Clientes para el rol client y lo muestra para admin', () => {
    let { primaryItems } = usePlatformNav()
    expect(primaryItems.value.map((i) => i.label)).not.toContain('Clientes')

    mockAuth.isAdmin = true
    ;({ primaryItems } = usePlatformNav())
    expect(primaryItems.value.map((i) => i.label)).toContain('Clientes')
  })

  it('no expone las rutas globales eliminadas por el refactor de IA', () => {
    mockAuth.isAdmin = true
    const { primaryItems, accountItems, adminItems } = usePlatformNav()
    const hrefs = [...primaryItems.value, ...accountItems.value, ...adminItems.value].map((i) => i.href)
    for (const dead of [
      '/platform/dashboard',
      '/platform/board',
      '/platform/bugs',
      '/platform/changes',
      '/platform/deliverables',
      '/platform/payments',
    ]) {
      expect(hrefs).not.toContain(dead)
    }
  })

  it('isActive coincide en ruta exacta y anidada, ignorando el prefijo de locale', () => {
    global.useRoute = jest.fn(() => ({ path: '/en-us/platform/projects/5/board' }))
    const { isActive } = usePlatformNav()
    expect(isActive('/en-us/platform/projects')).toBe(true)
    expect(isActive('/en-us/platform/clients')).toBe(false)
  })
})

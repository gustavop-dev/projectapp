import {
  capabilityCatalogFindings,
  capabilityNodePath,
  capabilityViewRecords,
  findCapabilityNode,
  flattenCapabilityCatalog,
  viewCapabilityCatalog,
} from '../../config/viewCapabilityCatalog'
import { viewCatalogSections } from '../../config/viewCatalog'

describe('viewCapabilityCatalog', () => {
  it('starts with every high-level application domain', () => {
    expect(viewCapabilityCatalog.children.map((node) => node.id)).toEqual(
      viewCatalogSections.map((section) => section.id),
    )
  })

  it('classifies every Platform view once', () => {
    expect(capabilityCatalogFindings()).toEqual([])
  })

  it('organizes Platform into business capabilities', () => {
    const platform = findCapabilityNode('client-platform')

    expect(platform.children.map((node) => node.label)).toEqual([
      'Acceso y cuenta',
      'Clientes y proyectos',
      'Seguimiento del trabajo',
      'Entregables y recursos',
      'Documentos y aprobaciones',
      'Pagos, hosting y cobros',
      'Comunicación y notificaciones',
      'Administración de accesos',
    ])
  })

  it('resolves the breadcrumb path for a feature', () => {
    expect(capabilityNodePath('platform-project-board').map((node) => node.id)).toEqual([
      'projectapp',
      'client-platform',
      'platform-work-tracking',
      'platform-project-board',
    ])
  })

  it('resolves technical references only from the canonical catalog', () => {
    const node = findCapabilityNode('platform-document-portal')

    expect(capabilityViewRecords(node)).toEqual([
      expect.objectContaining({
        label: 'Documentos del cliente',
        url: '/platform/documents',
      }),
    ])
  })

  it('gives every node a unique identifier', () => {
    const ids = flattenCapabilityCatalog().map((node) => node.id)

    expect(new Set(ids).size).toBe(ids.length)
  })
})

import {
  auditViewCatalog,
  catalogAuditFindings,
  routeFromPageFile,
} from '../../config/viewCatalogAudit'

const validCatalog = [{
  id: 'platform',
  views: [{
    label: 'Detalle',
    url: '/platform/projects/:id',
    group: 'Proyectos',
    file: 'frontend/pages/platform/projects/[id]/index.vue',
    reference: 'detalle de proyecto',
    audience: 'client',
    viewType: 'detail',
  }],
}]

const audit = (overrides = {}) => auditViewCatalog({
  pageFiles: ['frontend/pages/platform/projects/[id]/index.vue'],
  sections: validCatalog,
  validAudiences: ['client'],
  validViewTypes: ['detail'],
  ...overrides,
})

describe('viewCatalogAudit', () => {
  it.each([
    ['frontend/pages/index.vue', '/'],
    ['frontend/pages/blog/[slug].vue', '/blog/:slug'],
    ['frontend/pages/platform/projects/[id]/index.vue', '/platform/projects/:id'],
    ['frontend/pages/[...slug].vue', '/:slug*'],
  ])('derives the Nuxt route for %s', (file, expected) => {
    expect(routeFromPageFile(file)).toBe(expected)
  })

  it('accepts a catalog aligned with its page inventory', () => {
    expect(catalogAuditFindings(audit())).toEqual([])
  })

  it('reports a page missing from the catalog', () => {
    const report = audit({
      pageFiles: [
        'frontend/pages/platform/projects/[id]/index.vue',
        'frontend/pages/platform/profile.vue',
      ],
    })

    expect(report.orphanPages).toEqual(['frontend/pages/platform/profile.vue'])
  })

  it('reports duplicate URLs', () => {
    const duplicate = {
      ...validCatalog[0].views[0],
      label: 'Otro detalle',
      file: 'frontend/pages/platform/other.vue',
    }
    const report = audit({
      pageFiles: [
        'frontend/pages/platform/projects/[id]/index.vue',
        'frontend/pages/platform/other.vue',
      ],
      sections: [{ ...validCatalog[0], views: [...validCatalog[0].views, duplicate] }],
    })

    expect(report.duplicateUrls).toEqual([
      {
        value: '/platform/projects/:id',
        entries: ['platform:Detalle', 'platform:Otro detalle'],
      },
    ])
  })

  it('reports invalid metadata', () => {
    const report = audit({ validViewTypes: ['list'] })

    expect(report.invalidMetadata).toEqual([
      {
        sectionId: 'platform',
        label: 'Detalle',
        audience: 'client',
        viewType: 'detail',
      },
    ])
  })

  it('reports filter options that no catalog entry uses', () => {
    const report = audit({
      validAudiences: ['client', 'admin'],
      validViewTypes: ['detail', 'redirect'],
    })

    expect(report.unusedAudiences).toEqual(['admin'])
    expect(report.unusedViewTypes).toEqual(['redirect'])
  })
})

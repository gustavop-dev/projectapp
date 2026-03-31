import { createGenericTechnicalEpicStub } from '~/utils/technicalModuleStub'

describe('createGenericTechnicalEpicStub', () => {
  it('uses moduleId in title when label empty', () => {
    const stub = createGenericTechnicalEpicStub('module-1')
    expect(stub.title).toContain('module-1')
    expect(stub.linked_module_ids).toEqual(['module-1'])
    expect(stub.requirements[0].linked_module_ids).toEqual(['module-1'])
  })

  it('uses label in title when provided', () => {
    const stub = createGenericTechnicalEpicStub('g-2', 'Extra')
    expect(stub.title).toContain('Extra')
  })
})

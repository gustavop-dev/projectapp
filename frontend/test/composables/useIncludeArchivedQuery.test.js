import { buildPlatformListUrl } from '../../composables/useIncludeArchivedQuery'

describe('buildPlatformListUrl', () => {
  it('returns path when no query', () => {
    expect(buildPlatformListUrl('projects/1/deliverables/')).toBe('projects/1/deliverables/')
  })

  it('merges params and include_archived', () => {
    expect(buildPlatformListUrl('a/', { status: 'open', empty: '' }, true)).toBe(
      'a/?status=open&include_archived=1',
    )
  })

  it('appends with ampersand when path has query', () => {
    expect(buildPlatformListUrl('a/?x=1', {}, true)).toBe('a/?x=1&include_archived=1')
  })
})

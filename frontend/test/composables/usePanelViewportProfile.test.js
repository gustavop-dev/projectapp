import { panelProfileForWidth } from '../../composables/usePanelViewportProfile'

describe('panelProfileForWidth', () => {
  it.each([
    [412, 'compact'],
    [639, 'compact'],
    [640, 'portrait'],
    [1024, 'landscape'],
    [1280, 'desktop'],
    [1920, 'wide'],
  ])('maps %ipx to %s', (width, expected) => {
    expect(panelProfileForWidth(width)).toBe(expected)
  })
})

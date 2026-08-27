import {
  clampExplorerZoom,
  orbitalPosition,
} from '../../composables/useOrbitalExplorer'

describe('orbitalPosition', () => {
  it('places the first node above the center', () => {
    const position = orbitalPosition(0, 4, 0, 'desktop', 1)

    expect(position.x).toBeCloseTo(50)
    expect(position.y).toBeCloseTo(11)
  })

  it('rotates nodes around the center', () => {
    const position = orbitalPosition(0, 4, 90, 'desktop', 1)

    expect(position.x).toBeCloseTo(86)
    expect(position.y).toBeCloseTo(50)
  })

  it('keeps compact positions inside the stage', () => {
    const positions = Array.from({ length: 8 }, (_, index) => (
      orbitalPosition(index, 8, 0, 'compact', 1.07)
    ))

    expect(positions.every(({ x, y }) => x >= 11 && x <= 89 && y >= 8 && y <= 92)).toBe(true)
  })
})

describe('clampExplorerZoom', () => {
  it.each([
    [0.2, 0.82],
    [1, 1],
    [2, 1.07],
  ])('clamps %s to %s', (value, expected) => {
    expect(clampExplorerZoom(value)).toBe(expected)
  })
})

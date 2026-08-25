import {
  createPanelActionItem,
  getPanelAction,
  PANEL_ACTION_KEYS,
  PANEL_ACTIONS,
} from '../../config/panelActions'

describe('panelActions', () => {
  it('defines complete immutable metadata for every action', () => {
    expect(PANEL_ACTION_KEYS.length).toBeGreaterThan(40)
    for (const action of PANEL_ACTION_KEYS) {
      expect(PANEL_ACTIONS[action].label).toEqual(expect.any(String))
      expect(PANEL_ACTIONS[action].iconName).toMatch(/Icon$/)
      expect(PANEL_ACTIONS[action].icon).toBeTruthy()
      expect(Object.isFrozen(PANEL_ACTIONS[action])).toBe(true)
    }
    expect(Object.isFrozen(PANEL_ACTIONS)).toBe(true)
  })

  it('never assigns one component to two distinct actions', () => {
    const icons = PANEL_ACTION_KEYS.map((action) => PANEL_ACTIONS[action].icon)
    expect(new Set(icons).size).toBe(icons.length)
  })

  it('keeps copy and duplicate visually distinct', () => {
    expect(getPanelAction('copy').iconName).toBe('DocumentDuplicateIcon')
    expect(getPanelAction('duplicate').iconName).toBe('Square2StackIcon')
  })

  it('keeps other previously-colliding actions distinct', () => {
    expect(getPanelAction('edit').icon).not.toBe(getPanelAction('rename').icon)
    expect(getPanelAction('send').icon).not.toBe(getPanelAction('email-history').icon)
    expect(getPanelAction('close').icon).not.toBe(getPanelAction('delete').icon)
    expect(getPanelAction('remove').icon).not.toBe(getPanelAction('delete').icon)
  })

  it('builds menu items without moving behavior into the catalog', () => {
    const onClick = jest.fn()
    const item = createPanelActionItem('copy', {
      label: 'Copiar URL', onClick, disabled: true, testid: 'copy-url',
    })
    expect(item).toEqual({
      action: 'copy',
      label: 'Copiar URL',
      onClick,
      disabled: true,
      testid: 'copy-url',
    })
  })

  it('rejects unknown actions and icon overrides', () => {
    expect(() => getPanelAction('invented')).toThrow('Unknown panel action')
    expect(() => createPanelActionItem('copy', { icon: 'different' })).toThrow('cannot override')
    expect(() => createPanelActionItem('copy', { iconName: 'DifferentIcon' })).toThrow('cannot override')
  })
})

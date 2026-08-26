import { resolveResizableColumnWidths } from '../../composables/useResizableTableColumns'

const columns = [
  { key: 'title', columnWidth: { min: 240, default: 320, max: 520, resizable: true, shrinkPriority: null, fillPriority: null, fixed: false } },
  { key: 'tags', columnWidth: { min: 96, default: 160, max: 224, resizable: false, shrinkPriority: 1, fillPriority: 1, fixed: false } },
  { key: 'project', columnWidth: { min: 112, default: 160, max: 224, resizable: false, shrinkPriority: 2, fillPriority: 2, fixed: false } },
  { key: 'client', columnWidth: { min: 128, default: 176, max: 240, resizable: false, shrinkPriority: 3, fillPriority: 3, fixed: false } },
  { key: 'date', columnWidth: { min: 112, default: 128, max: 640, resizable: false, shrinkPriority: 4, fillPriority: 4, fixed: false } },
  { key: 'status', columnWidth: { min: 112, default: 112, max: 112, resizable: false, shrinkPriority: null, fillPriority: null, fixed: true } },
  { key: 'actions', columnWidth: { min: 80, default: 80, max: 80, resizable: false, shrinkPriority: null, fillPriority: null, fixed: true } },
]

describe('resolveResizableColumnWidths', () => {
  it('shrinks tags before later donors', () => {
    const layout = resolveResizableColumnWidths(columns, { title: 320 }, null, 1100)

    expect(layout.widths.tags).toBe(124)
    expect(layout.widths.project).toBe(160)
    expect(layout.widths.client).toBe(176)
  })

  it('continues with project after tags reaches its floor', () => {
    const layout = resolveResizableColumnWidths(columns, { title: 320 }, null, 1040)

    expect(layout.widths.tags).toBe(96)
    expect(layout.widths.project).toBe(128)
    expect(layout.widths.client).toBe(176)
  })

  it('takes an enlarged title from donors in business order on wide screens', () => {
    const layout = resolveResizableColumnWidths(columns, { title: 520 }, null, 1440)

    expect(layout.widths.tags).toBe(96)
    expect(layout.widths.project).toBe(152)
    expect(layout.widths.client).toBe(240)
    expect(layout.widths.date).toBe(240)
  })

  it('preserves the fixed status width', () => {
    const layout = resolveResizableColumnWidths(columns, { title: 520 }, null, 900)

    expect(layout.widths.status).toBe(112)
  })

  it('preserves the fixed action width', () => {
    const layout = resolveResizableColumnWidths(columns, { title: 520 }, null, 900)

    expect(layout.widths.actions).toBe(80)
  })

  it('keeps internal overflow after donors reach their floors', () => {
    const layout = resolveResizableColumnWidths(columns, { title: 520 }, null, 800)

    expect(layout.minWidth).toBeGreaterThan(800)
    expect(layout.widths.tags).toBe(96)
    expect(layout.widths.project).toBe(112)
    expect(layout.widths.client).toBe(128)
    expect(layout.widths.date).toBe(112)
  })

  it('excludes hidden desktop columns from landscape sizing', () => {
    const layout = resolveResizableColumnWidths(
      columns,
      { title: 320 },
      ['title', 'date', 'actions'],
      720,
    )

    expect(layout.widths.client).toBeUndefined()
    expect(layout.minWidth).toBe(720)
  })
})

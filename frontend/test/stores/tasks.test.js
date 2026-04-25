/**
 * Tests for tasks store (Kanban admin panel).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useTaskStore } from '../../stores/tasks'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const {
  get_request,
  create_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http')

describe('useTaskStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTaskStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('fetchTasks populates standard board columns by status', async () => {
    get_request.mockResolvedValueOnce({
      data: {
        todo: [{ id: 1, title: 'A', status: 'todo', priority: 'medium' }],
        in_progress: [],
        blocked: [],
        done: [{ id: 2, title: 'B', status: 'done', priority: 'low' }],
      },
    })
    await store.fetchTasks()
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
    expect(store.boardTasks.standard.todo.map((t) => t.id)).toEqual([1])
    expect(store.boardTasks.standard.done.map((t) => t.id)).toEqual([2])
    expect(store.boardTasks.standard.blocked).toEqual([])
  })

  it('fetchTasks returns failure result when request errors', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.fetchTasks()
    expect(result.success).toBe(false)
  })

  it('createTask refetches the board after creation', async () => {
    create_request.mockResolvedValueOnce({
      data: { id: 2, title: 'New', status: 'todo', priority: 'medium', board_type: 'standard' },
    })
    get_request.mockResolvedValueOnce({
      data: {
        todo: [{ id: 2, title: 'New', status: 'todo', priority: 'medium', board_type: 'standard' }],
        in_progress: [], blocked: [], done: [],
      },
    })
    await store.createTask({ title: 'New' })
    expect(create_request).toHaveBeenCalledWith('tasks/create/', { title: 'New' })
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
    expect(store.boardTasks.standard.todo.map((t) => t.id)).toEqual([2])
  })

  it('moveTask updates the board from the backend response', async () => {
    store.boardTasks.standard.todo = [{ id: 1, title: 'A', status: 'todo', board_type: 'standard' }]
    patch_request.mockResolvedValueOnce({
      data: {
        todo: [],
        in_progress: [{ id: 1, title: 'A', status: 'in_progress' }],
        blocked: [],
        done: [],
      },
    })
    await store.moveTask(1, 'in_progress', 0)
    expect(patch_request).toHaveBeenCalledWith(
      'tasks/1/reorder/', { status: 'in_progress', position: 0 },
    )
    expect(store.boardTasks.standard.todo).toEqual([])
    expect(store.boardTasks.standard.in_progress.map((t) => t.id)).toEqual([1])
  })

  it('moveTask triggers full board refetch on error', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const emptyBoard = { data: { todo: [], in_progress: [], blocked: [], done: [] } }
    get_request
      .mockResolvedValueOnce(emptyBoard)
      .mockResolvedValueOnce(emptyBoard)
      .mockResolvedValueOnce(emptyBoard)
      .mockResolvedValueOnce({ data: { items: [] } })
    const result = await store.moveTask(1, 'done', 0)
    expect(result.success).toBe(false)
    expect(store.error).toBe('reorder_failed')
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
  })

  it('updateTask refetches the board after patching', async () => {
    store.boardTasks.standard.todo = [{ id: 5, title: 'Old', status: 'todo', priority: 'low' }]
    patch_request.mockResolvedValueOnce({
      data: { id: 5, title: 'New', status: 'todo', priority: 'high', board_type: 'standard' },
    })
    get_request.mockResolvedValueOnce({
      data: {
        todo: [{ id: 5, title: 'New', status: 'todo', priority: 'high', board_type: 'standard' }],
        in_progress: [], blocked: [], done: [],
      },
    })
    await store.updateTask(5, { title: 'New', priority: 'high' })
    expect(patch_request).toHaveBeenCalledWith('tasks/5/update/', { title: 'New', priority: 'high' })
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
    expect(store.boardTasks.standard.todo[0].title).toBe('New')
  })

  it('updateTask refetches the correct board when status changes', async () => {
    store.boardTasks.standard.todo = [{ id: 5, title: 'A', status: 'todo', board_type: 'standard' }]
    patch_request.mockResolvedValueOnce({
      data: { id: 5, title: 'A', status: 'done', board_type: 'standard' },
    })
    get_request.mockResolvedValueOnce({
      data: { todo: [], in_progress: [], blocked: [], done: [{ id: 5, title: 'A', status: 'done', board_type: 'standard' }] },
    })
    await store.updateTask(5, { status: 'done' })
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
    expect(store.boardTasks.standard.done.map((t) => t.id)).toEqual([5])
  })

  it('deleteTask refetches the board after deletion', async () => {
    store.boardTasks.standard.todo = [{ id: 1, board_type: 'standard' }, { id: 2, board_type: 'standard' }]
    store.boardTasks.standard.done = [{ id: 3, board_type: 'standard' }]
    delete_request.mockResolvedValueOnce({})
    get_request.mockResolvedValueOnce({
      data: { todo: [{ id: 1, board_type: 'standard' }], in_progress: [], blocked: [], done: [{ id: 3, board_type: 'standard' }] },
    })
    await store.deleteTask(2)
    expect(delete_request).toHaveBeenCalledWith('tasks/2/delete/')
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
    expect(store.boardTasks.standard.todo.map((t) => t.id)).toEqual([1])
  })

  it('getTaskById searches across all board columns', () => {
    store.boardTasks.standard.in_progress = [{ id: 42, title: 'Deep' }]
    expect(store.getTaskById(42)).toEqual({ id: 42, title: 'Deep' })
    expect(store.getTaskById(99)).toBeNull()
  })

  it('getTaskById finds task in boardTasks.macro flat array', () => {
    store.boardTasks.macro = [{ id: 99, title: 'Macro task' }]
    expect(store.getTaskById(99)).toEqual({ id: 99, title: 'Macro task' })
  })

  // ── fetchAssignees ─────────────────────────────────────────────────────────

  it('fetchAssignees populates store.assignees from GET tasks/assignees/', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 1, name: 'Alice' }] })
    await store.fetchAssignees()
    expect(get_request).toHaveBeenCalledWith('tasks/assignees/')
    expect(store.assignees).toEqual([{ id: 1, name: 'Alice' }])
  })

  it('fetchAssignees returns failure result when request errors', async () => {
    get_request.mockRejectedValueOnce(new Error('network'))
    const result = await store.fetchAssignees()
    expect(result.success).toBe(false)
  })

  // ── fetchAllBoards ─────────────────────────────────────────────────────────

  it('fetchAllBoards calls GET for all four board keys', async () => {
    const emptyColumns = { data: { todo: [], in_progress: [], blocked: [], done: [] } }
    get_request
      .mockResolvedValueOnce(emptyColumns)
      .mockResolvedValueOnce(emptyColumns)
      .mockResolvedValueOnce(emptyColumns)
      .mockResolvedValueOnce({ data: { items: [] } })
    await store.fetchAllBoards()
    expect(get_request).toHaveBeenCalledWith('tasks/?board=standard')
    expect(get_request).toHaveBeenCalledWith('tasks/?board=weekly')
    expect(get_request).toHaveBeenCalledWith('tasks/?board=monthly')
    expect(get_request).toHaveBeenCalledWith('tasks/?board=macro')
  })

  // ── fetchTaskComments ──────────────────────────────────────────────────────

  it('fetchTaskComments populates store.comments[taskId] on success', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 10, text: 'Hello' }] })
    await store.fetchTaskComments(42)
    expect(get_request).toHaveBeenCalledWith('tasks/42/comments/')
    expect(store.comments[42]).toEqual([{ id: 10, text: 'Hello' }])
  })

  it('fetchTaskComments returns failure result when request errors', async () => {
    get_request.mockRejectedValueOnce(new Error('net'))
    const result = await store.fetchTaskComments(42)
    expect(result.success).toBe(false)
  })

  // ── addTaskComment ─────────────────────────────────────────────────────────

  it('addTaskComment posts to correct endpoint and appends comment to store', async () => {
    store.comments = { 7: [{ id: 1, text: 'existing' }] }
    create_request.mockResolvedValueOnce({ data: { id: 2, text: 'new comment' } })
    await store.addTaskComment(7, 'new comment')
    expect(create_request).toHaveBeenCalledWith('tasks/7/comments/create/', { text: 'new comment' })
    expect(store.comments[7]).toHaveLength(2)
    expect(store.comments[7][1]).toEqual({ id: 2, text: 'new comment' })
  })

  it('addTaskComment returns failure when request errors', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { text: ['required'] } } })
    const result = await store.addTaskComment(7, '')
    expect(result.success).toBe(false)
  })

  // ── deleteTaskComment ──────────────────────────────────────────────────────

  it('deleteTaskComment removes comment from store.comments[taskId]', async () => {
    store.comments = { 7: [{ id: 1, text: 'keep' }, { id: 2, text: 'remove' }] }
    delete_request.mockResolvedValueOnce({})
    await store.deleteTaskComment(7, 2)
    expect(delete_request).toHaveBeenCalledWith('tasks/7/comments/2/delete/')
    expect(store.comments[7]).toEqual([{ id: 1, text: 'keep' }])
  })

  it('deleteTaskComment returns failure when request errors', async () => {
    store.comments = { 7: [{ id: 1, text: 'x' }] }
    delete_request.mockRejectedValueOnce(new Error('net'))
    const result = await store.deleteTaskComment(7, 1)
    expect(result.success).toBe(false)
  })

  // ── fetchTaskAlerts ────────────────────────────────────────────────────────

  it('fetchTaskAlerts populates store.taskAlerts[taskId] on success', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 5, message: 'Alert!' }] })
    await store.fetchTaskAlerts(99)
    expect(get_request).toHaveBeenCalledWith('tasks/99/alerts/')
    expect(store.taskAlerts[99]).toEqual([{ id: 5, message: 'Alert!' }])
  })

  it('fetchTaskAlerts returns failure when request errors', async () => {
    get_request.mockRejectedValueOnce(new Error('net'))
    const result = await store.fetchTaskAlerts(99)
    expect(result.success).toBe(false)
  })

  // ── createTaskAlert ────────────────────────────────────────────────────────

  it('createTaskAlert posts to correct endpoint and appends alert to store', async () => {
    store.taskAlerts = { 10: [{ id: 1, message: 'existing' }] }
    create_request.mockResolvedValueOnce({ data: { id: 2, message: 'new alert' } })
    await store.createTaskAlert(10, { message: 'new alert' })
    expect(create_request).toHaveBeenCalledWith('tasks/10/alerts/create/', { message: 'new alert' })
    expect(store.taskAlerts[10]).toHaveLength(2)
    expect(store.taskAlerts[10][1]).toEqual({ id: 2, message: 'new alert' })
  })

  it('createTaskAlert returns failure when request errors', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.createTaskAlert(10, {})
    expect(result.success).toBe(false)
  })

  // ── deleteTaskAlert ────────────────────────────────────────────────────────

  it('deleteTaskAlert removes alert from store.taskAlerts[taskId]', async () => {
    store.taskAlerts = { 10: [{ id: 1, message: 'keep' }, { id: 2, message: 'remove' }] }
    delete_request.mockResolvedValueOnce({})
    await store.deleteTaskAlert(10, 2)
    expect(delete_request).toHaveBeenCalledWith('tasks/10/alerts/2/delete/')
    expect(store.taskAlerts[10]).toEqual([{ id: 1, message: 'keep' }])
  })

  it('deleteTaskAlert returns failure when request errors', async () => {
    store.taskAlerts = { 10: [{ id: 1, message: 'x' }] }
    delete_request.mockRejectedValueOnce(new Error('net'))
    const result = await store.deleteTaskAlert(10, 1)
    expect(result.success).toBe(false)
  })

  // ── replaceTaskInPlace ─────────────────────────────────────────────────────

  it('replaceTaskInPlace updates task in standard board without an API call', () => {
    store.boardTasks.standard.todo = [{ id: 3, title: 'Old', status: 'todo' }]
    const result = store.replaceTaskInPlace({ id: 3, title: 'Updated', status: 'todo' })
    expect(result).toBe(false)
    expect(store.boardTasks.standard.todo[0].title).toBe('Updated')
    expect(get_request).not.toHaveBeenCalled()
  })

  it('replaceTaskInPlace updates task found in weekly board', () => {
    store.boardTasks.weekly.in_progress = [{ id: 7, title: 'Orig', status: 'in_progress' }]
    const result = store.replaceTaskInPlace({ id: 7, title: 'Changed', status: 'in_progress' })
    expect(result).toBe(false)
    expect(store.boardTasks.weekly.in_progress[0].title).toBe('Changed')
  })

  it('replaceTaskInPlace returns true when task status changed (column mismatch)', () => {
    store.boardTasks.standard.todo = [{ id: 5, title: 'X', status: 'todo' }]
    const result = store.replaceTaskInPlace({ id: 5, title: 'X', status: 'done' })
    expect(result).toBe(true)
  })

  // ── archiveTask / unarchiveTask error paths ────────────────────────────────

  it('archiveTask sets store.error to archive_failed when PATCH errors', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.archiveTask(1, 'reason')
    expect(result.success).toBe(false)
    expect(store.error).toBe('archive_failed')
  })

  it('unarchiveTask sets store.error to unarchive_failed when PATCH errors', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.unarchiveTask(1)
    expect(result.success).toBe(false)
    expect(store.error).toBe('unarchive_failed')
  })
})

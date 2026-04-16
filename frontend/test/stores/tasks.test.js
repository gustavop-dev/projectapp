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
})

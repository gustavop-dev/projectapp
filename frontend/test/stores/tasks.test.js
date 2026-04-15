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

  it('fetchTasks populates columns by status', async () => {
    get_request.mockResolvedValueOnce({
      data: {
        todo: [{ id: 1, title: 'A', status: 'todo', priority: 'medium' }],
        in_progress: [],
        blocked: [],
        done: [{ id: 2, title: 'B', status: 'done', priority: 'low' }],
      },
    })
    await store.fetchTasks()
    expect(get_request).toHaveBeenCalledWith('tasks/')
    expect(store.columns.todo.map((t) => t.id)).toEqual([1])
    expect(store.columns.done.map((t) => t.id)).toEqual([2])
    expect(store.columns.blocked).toEqual([])
  })

  it('fetchTasks sets error on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.fetchTasks()
    expect(result.success).toBe(false)
    expect(store.error).toBe('fetch_failed')
  })

  it('createTask appends to the matching column', async () => {
    store.columns.todo = [{ id: 1, title: 'Existing', status: 'todo' }]
    create_request.mockResolvedValueOnce({
      data: { id: 2, title: 'New', status: 'todo', priority: 'medium' },
    })
    await store.createTask({ title: 'New' })
    expect(create_request).toHaveBeenCalledWith('tasks/create/', { title: 'New' })
    expect(store.columns.todo.map((t) => t.id)).toEqual([1, 2])
  })

  it('moveTask replaces the whole board from backend response', async () => {
    store.columns.todo = [{ id: 1, title: 'A', status: 'todo' }]
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
    expect(store.columns.todo).toEqual([])
    expect(store.columns.in_progress.map((t) => t.id)).toEqual([1])
  })

  it('moveTask refetches on error to resync', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    get_request.mockResolvedValueOnce({
      data: { todo: [], in_progress: [], blocked: [], done: [] },
    })
    const result = await store.moveTask(1, 'done', 0)
    expect(result.success).toBe(false)
    expect(store.error).toBe('reorder_failed')
    expect(get_request).toHaveBeenCalledWith('tasks/')
  })

  it('updateTask replaces in place when status unchanged', async () => {
    store.columns.todo = [{ id: 5, title: 'Old', status: 'todo', priority: 'low' }]
    patch_request.mockResolvedValueOnce({
      data: { id: 5, title: 'New', status: 'todo', priority: 'high' },
    })
    await store.updateTask(5, { title: 'New', priority: 'high' })
    expect(patch_request).toHaveBeenCalledWith('tasks/5/update/', { title: 'New', priority: 'high' })
    expect(store.columns.todo[0].title).toBe('New')
    expect(store.columns.todo[0].priority).toBe('high')
  })

  it('updateTask refetches when status changes', async () => {
    store.columns.todo = [{ id: 5, title: 'A', status: 'todo' }]
    patch_request.mockResolvedValueOnce({
      data: { id: 5, title: 'A', status: 'done' },
    })
    get_request.mockResolvedValueOnce({
      data: { todo: [], in_progress: [], blocked: [], done: [{ id: 5, title: 'A', status: 'done' }] },
    })
    await store.updateTask(5, { status: 'done' })
    expect(get_request).toHaveBeenCalledWith('tasks/')
    expect(store.columns.done.map((t) => t.id)).toEqual([5])
  })

  it('deleteTask removes the task from all columns', async () => {
    store.columns.todo = [{ id: 1 }, { id: 2 }]
    store.columns.done = [{ id: 3 }]
    delete_request.mockResolvedValueOnce({})
    await store.deleteTask(2)
    expect(delete_request).toHaveBeenCalledWith('tasks/2/delete/')
    expect(store.columns.todo.map((t) => t.id)).toEqual([1])
    expect(store.columns.done.map((t) => t.id)).toEqual([3])
  })

  it('getTaskById searches across all columns', () => {
    store.columns.in_progress = [{ id: 42, title: 'Deep' }]
    expect(store.getTaskById(42)).toEqual({ id: 42, title: 'Deep' })
    expect(store.getTaskById(99)).toBeNull()
  })
})

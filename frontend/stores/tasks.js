import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

const EMPTY_COLUMNS = () => ({ todo: [], in_progress: [], blocked: [], done: [] });
const BOARD_KEYS = ['standard', 'weekly', 'monthly', 'macro'];

export const useTaskStore = defineStore('tasks', {
  state: () => ({
    boardTasks: {
      standard: EMPTY_COLUMNS(),
      weekly: EMPTY_COLUMNS(),
      monthly: EMPTY_COLUMNS(),
      macro: [],
    },
    archivedTasks: [],
    archivedLoading: false,
    isLoading: false,
    isUpdating: false,
    error: null,
    assignees: [],
    taskAlerts: {},
    alertsLoading: false,
    comments: {},
    commentsLoading: false,
  }),

  getters: {
    /** Backward-compat alias used by existing tests. */
    columns: (state) => state.boardTasks.standard,

    getTaskById: (state) => (id) => {
      for (const boardKey of BOARD_KEYS) {
        const board = state.boardTasks[boardKey];
        const list = Array.isArray(board) ? board : Object.values(board).flat();
        const found = list.find((t) => t.id === id);
        if (found) return found;
      }
      return null;
    },

    taskCount: (state) => (status) => (state.boardTasks.standard[status] || []).length,
  },

  actions: {
    /** Fetch tasks for a single board and update boardTasks in place. */
    async fetchBoardTasks(board) {
      try {
        const response = await get_request(`tasks/?board=${board}`);
        if (board === 'macro') {
          this.boardTasks.macro = response.data.items || [];
        } else {
          this.boardTasks[board] = { ...EMPTY_COLUMNS(), ...response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        console.error(`Error fetching board ${board}:`, error);
        return { success: false, errors: error.response?.data };
      }
    },

    /** Fetch all 4 boards in parallel. */
    async fetchAllBoards() {
      this.isLoading = true;
      this.error = null;
      try {
        await Promise.all(BOARD_KEYS.map((b) => this.fetchBoardTasks(b)));
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /** Backward-compat alias used by tests and existing consumers. */
    async fetchTasks() {
      return this.fetchBoardTasks('standard');
    },

    /** Refetch a single board after a mutation (create/update/delete). */
    async refetchBoard(boardType) {
      return this.fetchBoardTasks(boardType || 'standard');
    },

    /** Create a new task. Backend places it at the end of its status column. */
    async createTask(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('tasks/create/', payload);
        const task = response.data;
        const board = task.board_type || 'standard';
        await this.refetchBoard(board);
        return { success: true, data: task };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating task:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Patch task fields. Refetches the affected board after changes. */
    async updateTask(id, patch) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`tasks/${id}/update/`, patch);
        const updated = response.data;
        await this.refetchBoard(updated.board_type || 'standard');
        return { success: true, data: updated };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating task:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Move a task to a new (status, position) via drag&drop. */
    async moveTask(id, newStatus, newPosition) {
      this.isUpdating = true;
      this.error = null;
      try {
        const task = this.getTaskById(id);
        const response = await patch_request(
          `tasks/${id}/reorder/`,
          { status: newStatus, position: newPosition },
        );
        const board = task?.board_type || 'standard';
        if (board === 'macro') {
          this.boardTasks.macro = response.data.items || [];
        } else {
          this.boardTasks[board] = { ...EMPTY_COLUMNS(), ...response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error reordering task:', error);
        await this.fetchAllBoards();
        this.error = 'reorder_failed';
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Fetch staff users for the assignee dropdown. */
    async fetchAssignees() {
      try {
        const response = await get_request('tasks/assignees/');
        this.assignees = response.data;
        return { success: true };
      /* c8 ignore next 4 */
      } catch (error) {
        console.error('Error fetching task assignees:', error);
        return { success: false };
      }
    },

    /** Delete a task. */
    async deleteTask(id) {
      this.isUpdating = true;
      this.error = null;
      const task = this.getTaskById(id);
      const board = task?.board_type || 'standard';
      try {
        await delete_request(`tasks/${id}/delete/`);
        await this.refetchBoard(board);
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting task:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Archive a task with an optional reason. */
    async archiveTask(id, reason) {
      this.isUpdating = true;
      this.error = null;
      const task = this.getTaskById(id);
      const board = task?.board_type || 'standard';
      try {
        await patch_request(`tasks/${id}/archive/`, { archive_reason: reason || '' });
        await this.refetchBoard(board);
        return { success: true };
      } catch (error) {
        this.error = 'archive_failed';
        console.error('Error archiving task:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Restore an archived task to its board. */
    async unarchiveTask(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`tasks/${id}/unarchive/`, {});
        const task = response.data;
        this.archivedTasks = this.archivedTasks.filter((t) => t.id !== id);
        await this.refetchBoard(task.board_type || 'standard');
        return { success: true };
      } catch (error) {
        this.error = 'unarchive_failed';
        console.error('Error unarchiving task:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Fetch all archived tasks (lazy — called when the accordion first opens). */
    async fetchArchivedTasks() {
      this.archivedLoading = true;
      try {
        const response = await get_request('tasks/archived/');
        this.archivedTasks = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching archived tasks:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.archivedLoading = false;
      }
    },

    /** Fetch comments for a task. */
    async fetchTaskComments(taskId) {
      this.commentsLoading = true;
      try {
        const response = await get_request(`tasks/${taskId}/comments/`);
        this.comments = { ...this.comments, [taskId]: response.data };
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching task comments:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.commentsLoading = false;
      }
    },

    /** Add a comment to a task. */
    async addTaskComment(taskId, text) {
      try {
        const response = await create_request(`tasks/${taskId}/comments/create/`, { text });
        const comment = response.data;
        const current = this.comments[taskId] ?? [];
        this.comments = { ...this.comments, [taskId]: [...current, comment] };
        return { success: true, data: comment };
      } catch (error) {
        console.error('Error adding task comment:', error);
        return { success: false, errors: error.response?.data };
      }
    },

    /** Delete a comment from a task. */
    async deleteTaskComment(taskId, commentId) {
      try {
        await delete_request(`tasks/${taskId}/comments/${commentId}/delete/`);
        const current = this.comments[taskId] ?? [];
        this.comments = { ...this.comments, [taskId]: current.filter((c) => c.id !== commentId) };
        return { success: true };
      } catch (error) {
        console.error('Error deleting task comment:', error);
        return { success: false };
      }
    },

    /** Fetch manual alerts for a task. */
    async fetchTaskAlerts(taskId) {
      this.alertsLoading = true;
      try {
        const response = await get_request(`tasks/${taskId}/alerts/`);
        this.taskAlerts = { ...this.taskAlerts, [taskId]: response.data };
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching task alerts:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.alertsLoading = false;
      }
    },

    /** Create a manual alert for a task. */
    async createTaskAlert(taskId, payload) {
      try {
        const response = await create_request(`tasks/${taskId}/alerts/create/`, payload);
        const alert = response.data;
        const current = this.taskAlerts[taskId] ?? [];
        this.taskAlerts = { ...this.taskAlerts, [taskId]: [...current, alert] };
        return { success: true, data: alert };
      } catch (error) {
        console.error('Error creating task alert:', error);
        return { success: false, errors: error.response?.data };
      }
    },

    /** Delete a manual alert from a task. */
    async deleteTaskAlert(taskId, alertId) {
      try {
        await delete_request(`tasks/${taskId}/alerts/${alertId}/delete/`);
        const current = this.taskAlerts[taskId] ?? [];
        this.taskAlerts = { ...this.taskAlerts, [taskId]: current.filter((a) => a.id !== alertId) };
        return { success: true };
      } catch (error) {
        console.error('Error deleting task alert:', error);
        return { success: false };
      }
    },

    /**
     * Replace a task within its current column (searches all boards).
     * Returns true if the task moved to a different column (caller should refetch).
     */
    replaceTaskInPlace(updated) {
      for (const boardKey of BOARD_KEYS) {
        const board = this.boardTasks[boardKey];
        if (Array.isArray(board)) {
          const idx = board.findIndex((t) => t.id === updated.id);
          if (idx !== -1) {
            this.boardTasks[boardKey].splice(idx, 1, updated);
            return false;
          }
        } else {
          for (const key of Object.keys(board)) {
            const idx = board[key].findIndex((t) => t.id === updated.id);
            if (idx === -1) continue;
            if (key === updated.status) {
              this.boardTasks[boardKey][key].splice(idx, 1, updated);
              return false;
            }
            return true;
          }
        }
      }
      return true;
    },
  },
});

import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

const EMPTY_COLUMNS = () => ({ todo: [], in_progress: [], blocked: [], done: [] });

export const useTaskStore = defineStore('tasks', {
  /**
   * State of the Kanban Task store.
   *
   * Properties:
   * - columns (Object): Tasks grouped by status ({todo, in_progress, blocked, done}).
   * - isLoading (Boolean): Fetch operation in progress.
   * - isUpdating (Boolean): Mutation operation in progress.
   * - error (String|null): Last error code.
   */
  state: () => ({
    columns: EMPTY_COLUMNS(),
    isLoading: false,
    isUpdating: false,
    error: null,
    assignees: [],
  }),

  getters: {
    getTaskById: (state) => (id) => {
      for (const list of Object.values(state.columns)) {
        const found = list.find((t) => t.id === id);
        if (found) return found;
      }
      return null;
    },
    taskCount: (state) => (status) => (state.columns[status] || []).length,
  },

  actions: {
    /** Fetch all tasks grouped by status. */
    async fetchTasks() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('tasks/');
        this.columns = { ...EMPTY_COLUMNS(), ...response.data };
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching tasks:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /** Create a new task. Backend places it at the end of its status column. */
    async createTask(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('tasks/create/', payload);
        const task = response.data;
        this.columns[task.status].push(task);
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

    /** Patch task fields. If status changes, refetch to keep columns consistent. */
    async updateTask(id, patch) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`tasks/${id}/update/`, patch);
        const updated = response.data;
        const statusChanged = this.replaceTaskInPlace(updated);
        if (statusChanged) {
          await this.fetchTasks();
        }
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
        const response = await patch_request(
          `tasks/${id}/reorder/`,
          { status: newStatus, position: newPosition },
        );
        this.columns = { ...EMPTY_COLUMNS(), ...response.data };
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error reordering task:', error);
        await this.fetchTasks();
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
      try {
        await delete_request(`tasks/${id}/delete/`);
        for (const key of Object.keys(this.columns)) {
          this.columns[key] = this.columns[key].filter((t) => t.id !== id);
        }
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

    /**
     * Replace a task within its current column.
     * Returns true if the task moved to a different column (caller should refetch).
     */
    replaceTaskInPlace(updated) {
      for (const key of Object.keys(this.columns)) {
        const idx = this.columns[key].findIndex((t) => t.id === updated.id);
        if (idx === -1) continue;
        if (key === updated.status) {
          this.columns[key].splice(idx, 1, updated);
          return false;
        }
        return true;
      }
      return true;
    },
  },
});

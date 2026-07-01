import { ref } from 'vue';

/**
 * Panel-wide notification queue.
 *
 * Module-level singleton (shared across all callers) rendered by a single
 * global <PanelNotificationHost /> mounted in layouts/admin.vue. Supports rich
 * notifications with title + optional detail line + optional action button.
 *
 * Usage:
 *   const notify = usePanelNotify();
 *   notify.error({
 *     title: 'No se pudo enviar la propuesta',
 *     detail: 'Falta el correo del cliente.',
 *     action: { label: 'Editar propuesta', to: '/panel/proposals/103/edit' },
 *   });
 *   notify.success({ title: 'Propuesta enviada al cliente' });
 *
 * An action is either { label, to } (router navigation) or { label, handler }
 * (a function). In both cases the notification is dismissed when clicked.
 */

const notifications = ref([]);
const timers = new Map();
let seq = 0;

const DEFAULT_DURATION = {
  success: 4000,
  info: 5000,
  warning: 7000,
  error: 8000,
};

function dismiss(id) {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
  notifications.value = notifications.value.filter((n) => n.id !== id);
}

function clearAll() {
  timers.forEach((timer) => clearTimeout(timer));
  timers.clear();
  notifications.value = [];
}

/**
 * Push a notification. `opts` may be a string (used as the title) or an object.
 * Returns the notification id (useful to dismiss it programmatically).
 */
function push(opts = {}) {
  const normalized = typeof opts === 'string' ? { title: opts } : opts;
  const {
    type = 'info',
    title = '',
    detail = '',
    action = null,
    duration,
  } = normalized;

  const id = ++seq;
  notifications.value = [...notifications.value, { id, type, title, detail, action }];

  const ms = duration != null ? duration : (DEFAULT_DURATION[type] ?? DEFAULT_DURATION.info);
  if (ms > 0) {
    timers.set(id, setTimeout(() => dismiss(id), ms));
  }
  return id;
}

function success(opts) { return push({ ...(typeof opts === 'string' ? { title: opts } : opts), type: 'success' }); }
function error(opts) { return push({ ...(typeof opts === 'string' ? { title: opts } : opts), type: 'error' }); }
function warning(opts) { return push({ ...(typeof opts === 'string' ? { title: opts } : opts), type: 'warning' }); }
function info(opts) { return push({ ...(typeof opts === 'string' ? { title: opts } : opts), type: 'info' }); }

export function usePanelNotify() {
  return { notifications, push, success, error, warning, info, dismiss, clearAll };
}

export const COMMUNICATION_PREFERENCE_DEFAULTS = Object.freeze({
  navigation_mode: 'project',
  thread_order: 'recent',
  page_size: 20,
  default_channel: 'whatsapp',
  show_manual_help: true,
  navigation_width: 288,
});

export const COMMUNICATION_ORDER_STORAGE_KEY = 'panel.communications.order';
export const COMMUNICATION_PANEL_STORAGE_KEY = 'projectapp-communications-navigation-width';
export const COMMUNICATION_NOTICE_STORAGE_KEY = 'projectapp-communications-manual-notice-v1';

const NAVIGATION_MODES = new Set(['project', 'client']);
const THREAD_ORDERS = new Set(['recent', 'oldest', 'title']);
const PAGE_SIZES = new Set([10, 20, 50]);
const CHANNELS = new Set(['whatsapp', 'email']);

export function clampCommunicationPanelWidth(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return COMMUNICATION_PREFERENCE_DEFAULTS.navigation_width;
  return Math.min(400, Math.max(240, Math.round(parsed)));
}

export function normalizeCommunicationPreferences(value = {}) {
  return {
    navigation_mode: NAVIGATION_MODES.has(value.navigation_mode)
      ? value.navigation_mode
      : COMMUNICATION_PREFERENCE_DEFAULTS.navigation_mode,
    thread_order: THREAD_ORDERS.has(value.thread_order)
      ? value.thread_order
      : COMMUNICATION_PREFERENCE_DEFAULTS.thread_order,
    page_size: PAGE_SIZES.has(Number(value.page_size))
      ? Number(value.page_size)
      : COMMUNICATION_PREFERENCE_DEFAULTS.page_size,
    default_channel: CHANNELS.has(value.default_channel)
      ? value.default_channel
      : COMMUNICATION_PREFERENCE_DEFAULTS.default_channel,
    show_manual_help: typeof value.show_manual_help === 'boolean'
      ? value.show_manual_help
      : COMMUNICATION_PREFERENCE_DEFAULTS.show_manual_help,
    navigation_width: clampCommunicationPanelWidth(value.navigation_width),
  };
}

export function readLegacyCommunicationPreferences(storage) {
  if (!storage) return {};
  try {
    const preferences = {};
    const order = storage.getItem(COMMUNICATION_ORDER_STORAGE_KEY);
    if (THREAD_ORDERS.has(order)) preferences.thread_order = order;

    const rawWidth = storage.getItem(COMMUNICATION_PANEL_STORAGE_KEY);
    if (rawWidth !== null && Number.isFinite(Number(rawWidth))) {
      preferences.navigation_width = clampCommunicationPanelWidth(rawWidth);
    }

    if (storage.getItem(COMMUNICATION_NOTICE_STORAGE_KEY) === 'dismissed') {
      preferences.show_manual_help = false;
    }
    return preferences;
  } catch {
    return {};
  }
}

export function clearLegacyCommunicationPreferences(storage) {
  if (!storage) return;
  try {
    storage.removeItem(COMMUNICATION_ORDER_STORAGE_KEY);
    storage.removeItem(COMMUNICATION_PANEL_STORAGE_KEY);
    storage.removeItem(COMMUNICATION_NOTICE_STORAGE_KEY);
  } catch {
    // Some privacy modes expose Storage but reject every read/write operation.
  }
}

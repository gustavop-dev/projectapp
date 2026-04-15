export const TAG_COLOR_OPTIONS = [
  { value: 'gray', label: 'Gris' },
  { value: 'emerald', label: 'Verde' },
  { value: 'blue', label: 'Azul' },
  { value: 'yellow', label: 'Amarillo' },
  { value: 'red', label: 'Rojo' },
  { value: 'purple', label: 'Morado' },
];

export const TAG_BADGE_CLASS = {
  gray: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200',
  emerald: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
  yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200',
  red: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200',
  purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
};

export const TAG_ACTIVE_CLASS = {
  gray: 'bg-gray-200 text-gray-800 dark:bg-gray-600 dark:text-gray-100',
  emerald: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200',
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200',
  yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-200',
  red: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200',
  purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200',
};

export const TAG_DOT_CLASS = {
  gray: 'bg-gray-400',
  emerald: 'bg-emerald-500',
  blue: 'bg-blue-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
  purple: 'bg-purple-500',
};

export const TAG_IDLE_CHIP_CLASS = 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700';

export function tagBadgeClass(color) {
  return TAG_BADGE_CLASS[color] || TAG_BADGE_CLASS.gray;
}

export function tagActiveClass(color) {
  return TAG_ACTIVE_CLASS[color] || TAG_ACTIVE_CLASS.gray;
}

export function tagDotClass(color) {
  return TAG_DOT_CLASS[color] || TAG_DOT_CLASS.gray;
}

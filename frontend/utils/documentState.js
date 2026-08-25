export const DOCUMENT_STATE_COLORS = [
  { value: 'gray', label: 'Gris' },
  { value: 'emerald', label: 'Verde' },
  { value: 'blue', label: 'Azul' },
  { value: 'yellow', label: 'Amarillo' },
  { value: 'orange', label: 'Naranja' },
  { value: 'red', label: 'Rojo' },
  { value: 'purple', label: 'Morado' },
];

export function stateBadgeVariant(state) {
  if (state?.system_key === 'needs_fix') return 'danger';
  return {
    emerald: 'success',
    blue: 'info',
    yellow: 'warning',
    orange: 'warning',
    red: 'danger',
    purple: 'accent',
    gray: 'neutral',
  }[state?.color] || 'neutral';
}

export function formatStateDuration(seconds) {
  if (seconds === null || seconds === undefined) return 'fecha desconocida';
  const value = Math.max(0, Number(seconds) || 0);
  const days = Math.floor(value / 86400);
  if (days >= 1) return `${days} ${days === 1 ? 'día' : 'días'}`;
  const hours = Math.floor(value / 3600);
  if (hours >= 1) return `${hours} ${hours === 1 ? 'hora' : 'horas'}`;
  const minutes = Math.floor(value / 60);
  if (minutes >= 1) return `${minutes} min`;
  return 'ahora';
}

export function relativeStateTime(value) {
  if (!value) return 'momento desconocido';
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  return `hace ${formatStateDuration(seconds)}`;
}

export function sortStateEpisodes(episodes = []) {
  return [...episodes].sort((left, right) => {
    const leftState = left.state || {};
    const rightState = right.state || {};
    return (leftState.group_order ?? 99) - (rightState.group_order ?? 99)
      || (leftState.system_key === 'needs_fix' ? -1 : 0)
      - (rightState.system_key === 'needs_fix' ? -1 : 0)
      || (leftState.order ?? 99) - (rightState.order ?? 99)
      || String(leftState.name || '').localeCompare(String(rightState.name || ''), 'es');
  });
}

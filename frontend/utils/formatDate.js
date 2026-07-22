// Estándar de fechas del sistema: 'Jue, 16 jul 2026' / 'Jue, 16 jul 2026, 15:20'.
// Tablas manuales (no Intl para nombres): el output de toLocaleDateString varía
// entre el ICU de Node y los browsers ('jue' vs 'jue.'). Intl se usa SOLO para
// la conversión a America/Bogota vía formatToParts (campos numéricos, estables).
const BOGOTA_TZ = 'America/Bogota';

const WEEKDAYS = {
  es: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
  en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
};
const MONTHS = {
  es: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
};

const DATE_ONLY_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

const partsFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: BOGOTA_TZ,
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

// Devuelve {y, mo, d, h, mi} en Bogotá, o null si el valor es inválido.
// Strings date-only ('2026-07-16') se toman literales: new Date() los parsea
// como UTC medianoche y desplazaría el día en zonas UTC-5.
function getBogotaParts(value) {
  if (typeof value === 'string') {
    const m = DATE_ONLY_RE.exec(value.trim());
    if (m) return { y: +m[1], mo: +m[2], d: +m[3], h: null, mi: null };
  }
  const dt = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(dt.getTime())) return null;
  const parts = {};
  for (const p of partsFormatter.formatToParts(dt)) parts[p.type] = p.value;
  return { y: +parts.year, mo: +parts.month, d: +parts.day, h: +parts.hour, mi: +parts.minute };
}

function weekdayIndex(y, mo, d) {
  return new Date(Date.UTC(y, mo - 1, d)).getUTCDay();
}

/** 'Jue, 16 jul 2026' (es) / 'Thu, Jul 16, 2026' (en). */
export function formatDate(value, { locale = 'es', fallback = '—' } = {}) {
  if (value === null || value === undefined || value === '') return fallback;
  const p = getBogotaParts(value);
  if (!p) return fallback;
  const wd = WEEKDAYS[locale][weekdayIndex(p.y, p.mo, p.d)];
  const mo = MONTHS[locale][p.mo - 1];
  return locale === 'en' ? `${wd}, ${mo} ${p.d}, ${p.y}` : `${wd}, ${p.d} ${mo} ${p.y}`;
}

/** 'Jue, 16 jul 2026, 15:20'. Para valores date-only omite la hora. */
export function formatDateTime(value, opts = {}) {
  const { fallback = '—' } = opts;
  if (value === null || value === undefined || value === '') return fallback;
  const p = getBogotaParts(value);
  if (!p) return fallback;
  const base = formatDate(value, opts);
  if (p.h === null) return base;
  return `${base}, ${String(p.h).padStart(2, '0')}:${String(p.mi).padStart(2, '0')}`;
}

/** Compacto para tarjetas/espacios chicos: '15 may' (es) / 'May 15' (en). */
export function formatDayMonth(value, { locale = 'es', fallback = '' } = {}) {
  if (value === null || value === undefined || value === '') return fallback;
  const p = getBogotaParts(value);
  if (!p) return fallback;
  const mo = MONTHS[locale][p.mo - 1];
  return locale === 'en' ? `${mo} ${p.d}` : `${p.d} ${mo}`;
}

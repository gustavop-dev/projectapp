// Local-time today: toISOString() would shift to tomorrow after 19:00
// in Bogotá (UTC-5).
export function todayISO() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

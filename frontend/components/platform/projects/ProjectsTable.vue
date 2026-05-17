<template>
  <div class="overflow-hidden rounded-2xl border border-border-default bg-surface">
    <table class="min-w-full text-left text-sm">
      <thead class="bg-surface-muted/40 text-xs font-medium uppercase tracking-wider text-green-light/70">
        <tr>
          <th class="px-4 py-3">Proyecto</th>
          <th v-if="isAdmin" class="px-4 py-3">Cliente</th>
          <th class="px-4 py-3">Progreso</th>
          <th class="px-4 py-3">Bugs abiertos</th>
          <th v-if="isAdmin" class="px-4 py-3">Solicitudes pendientes</th>
          <th class="px-4 py-3">Próximo entregable</th>
          <th class="px-4 py-3">Última actividad</th>
          <th class="w-10 px-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="p in projects"
          :key="p.id"
          :data-testid="`project-row-${p.id}`"
          class="cursor-pointer border-t border-border-muted transition hover:bg-primary-soft/30"
          @click="$emit('navigate', p.id)"
        >
          <td class="px-4 py-3">
            <div class="font-medium text-text-default">{{ p.name }}</div>
            <span :class="statusChipClass(p.status)">{{ statusLabel(p.status) }}</span>
          </td>
          <td v-if="isAdmin" class="px-4 py-3 text-green-light">
            {{ p.client_name }}<br>
            <span class="text-xs text-green-light/60">{{ p.client_email }}</span>
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <div class="h-1.5 w-20 overflow-hidden rounded-full bg-surface-muted">
                <div class="h-full bg-primary" :style="{ width: `${p.progress || 0}%` }"></div>
              </div>
              <span class="text-xs">{{ p.progress || 0 }}%</span>
            </div>
          </td>
          <td class="px-4 py-3">
            <span :class="(p.bugs_open_count || 0) > 0 ? 'rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700' : 'text-green-light/60'">
              {{ p.bugs_open_count || 0 }}
            </span>
          </td>
          <td v-if="isAdmin" class="px-4 py-3">
            <span :class="(p.changes_pending_count || 0) > 0 ? 'rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700' : 'text-green-light/60'">
              {{ p.changes_pending_count || 0 }}
            </span>
          </td>
          <td class="px-4 py-3 text-sm">
            <template v-if="p.next_deliverable">
              {{ p.next_deliverable.title }}<br>
              <span class="text-xs text-green-light/60">{{ formatDate(p.next_deliverable.due_date) }}</span>
            </template>
            <span v-else class="text-green-light/60">—</span>
          </td>
          <td class="px-4 py-3 text-sm text-green-light/70">{{ relativeTime(p.last_activity_at) }}</td>
          <td class="px-2 py-3 text-right text-green-light/40">›</td>
        </tr>
        <tr v-if="!projects.length">
          <td :colspan="isAdmin ? 8 : 6" class="px-4 py-12 text-center text-green-light/60">
            No hay proyectos para mostrar.
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  projects: { type: Array, required: true },
  role: { type: String, default: 'admin' },
})

defineEmits(['navigate'])

const isAdmin = computed(() => props.role === 'admin')

const STATUS_LABELS = {
  active: 'Activo', paused: 'Pausado',
  completed: 'Completado', archived: 'Archivado',
}
function statusLabel(s) { return STATUS_LABELS[s] || s }
function statusChipClass(s) {
  const base = 'mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    active: 'bg-green-100 text-green-700',
    paused: 'bg-amber-100 text-amber-700',
    completed: 'bg-sky-100 text-sky-700',
    archived: 'bg-slate-100 text-slate-600',
  }
  return `${base} ${map[s] || map.archived}`
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

function relativeTime(iso) {
  if (!iso) return '—'
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24))
  if (days < 1) return 'Hoy'
  if (days === 1) return 'Ayer'
  if (days < 30) return `Hace ${days} días`
  if (days < 365) return `Hace ${Math.floor(days / 30)} meses`
  return `Hace ${Math.floor(days / 365)} años`
}
</script>

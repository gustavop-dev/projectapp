<template>
  <div id="platform-unified-changes">
    <!-- Header -->
    <div class="mb-6" data-enter>
      <h1 class="text-2xl font-bold text-esmerald dark:text-white">
        {{ authStore.isAdmin ? 'Solicitudes de cambio' : 'Mis solicitudes' }}
      </h1>
      <p class="mt-1 text-sm text-green-light">
        {{ authStore.isAdmin ? 'Todas las solicitudes de cambio de todos los proyectos.' : 'Solicitudes de cambio de tus proyectos.' }}
      </p>
    </div>

    <!-- Loading -->
    <div v-if="crStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <!-- Empty -->
    <div v-else-if="crStore.changeRequests.length === 0" class="rounded-3xl border border-dashed border-esmerald/10 py-20 text-center dark:border-white/10" data-enter>
      <p class="text-sm text-green-light">No hay solicitudes de cambio en este momento.</p>
    </div>

    <template v-else>
      <!-- Summary pills -->
      <div class="mb-6 flex flex-wrap gap-3" data-enter>
        <div
          v-for="pill in summaryPills"
          :key="pill.key"
          class="flex items-center gap-2 rounded-full border border-esmerald/[0.06] bg-white px-4 py-2 dark:border-white/[0.06] dark:bg-esmerald"
        >
          <span class="h-2 w-2 rounded-full" :class="pill.dotClass" />
          <span class="text-xs font-medium text-esmerald dark:text-white">{{ pill.label }}</span>
          <span class="text-xs font-bold text-green-light">{{ pill.count }}</span>
        </div>
      </div>

      <!-- Grouped by project -->
      <div class="space-y-8" data-enter>
        <div v-for="group in groupedByProject" :key="group.projectId">
          <div class="mb-3 flex items-center gap-3">
            <NuxtLink
              :to="localePath(`/platform/projects/${group.projectId}`)"
              class="text-base font-semibold text-esmerald transition hover:text-esmerald/70 dark:text-white dark:hover:text-lemon"
            >
              {{ group.projectName }}
            </NuxtLink>
            <NuxtLink
              :to="localePath(`/platform/projects/${group.projectId}/changes`)"
              class="rounded-full border border-esmerald/10 px-3 py-1 text-[10px] font-medium text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
            >
              Ver solicitudes →
            </NuxtLink>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <div
              v-for="cr in group.items"
              :key="cr.id"
              class="group cursor-pointer rounded-xl border border-esmerald/[0.06] bg-white p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
              @click="navigateTo(`/platform/projects/${group.projectId}/changes`)"
            >
              <div class="mb-2 flex items-center gap-2">
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="statusBadgeClass(cr.status)">
                  {{ statusLabel(cr.status) }}
                </span>
                <span v-if="cr.is_urgent" class="rounded-full bg-red-500/15 px-1.5 py-0.5 text-[9px] font-bold uppercase text-red-600 dark:text-red-400">
                  Urgente
                </span>
                <span v-if="cr.module_or_screen" class="ml-auto text-[10px] text-green-light/40">{{ cr.module_or_screen }}</span>
              </div>
              <h4 class="text-sm font-medium text-esmerald dark:text-white">{{ cr.title }}</h4>
              <div class="mt-2 flex items-center gap-2">
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="priorityBadgeClass(cr.suggested_priority)">
                  {{ priorityLabel(cr.suggested_priority) }}
                </span>
                <span class="text-[10px] text-green-light/50">{{ cr.created_by_name }}</span>
                <span v-if="cr.screenshot_url" class="ml-auto text-green-light/30">
                  <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'

const localePath = useLocalePath()
import { usePlatformChangeRequestsStore } from '~/stores/platform-change-requests'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

useHead({ title: 'Solicitudes de cambio — ProjectApp' })
usePageEntrance('#platform-unified-changes')

const authStore = usePlatformAuthStore()
const crStore = usePlatformChangeRequestsStore()

const activeStatuses = ['pending', 'evaluating', 'needs_clarification']

const summaryPills = computed(() => {
  const pills = [
    { key: 'pending', label: 'Pendientes', dotClass: 'bg-amber-500' },
    { key: 'evaluating', label: 'En evaluación', dotClass: 'bg-blue-500' },
    { key: 'approved', label: 'Aprobadas', dotClass: 'bg-emerald-500' },
    { key: 'needs_clarification', label: 'Requiere aclaración', dotClass: 'bg-purple-500' },
    { key: 'rejected', label: 'Rechazadas', dotClass: 'bg-red-500' },
  ]
  return pills
    .map((p) => ({
      ...p,
      count: crStore.changeRequests.filter((cr) => cr.status === p.key).length,
    }))
    .filter((p) => p.count > 0)
})

const groupedByProject = computed(() => {
  const groups = {}
  for (const cr of crStore.changeRequests) {
    const pid = cr.project_id
    if (!pid) continue
    if (!groups[pid]) {
      groups[pid] = {
        projectId: pid,
        projectName: cr.project_name || `Proyecto #${pid}`,
        items: [],
      }
    }
    groups[pid].items.push(cr)
  }
  const sortOrder = { pending: 0, evaluating: 1, needs_clarification: 2, approved: 3, rejected: 4, out_of_scope: 5 }
  for (const g of Object.values(groups)) {
    g.items.sort((a, b) => (sortOrder[a.status] ?? 99) - (sortOrder[b.status] ?? 99))
  }
  return Object.values(groups).sort((a, b) => {
    const aActive = a.items.filter((cr) => activeStatuses.includes(cr.status)).length
    const bActive = b.items.filter((cr) => activeStatuses.includes(cr.status)).length
    return bActive - aActive
  })
})

function statusBadgeClass(s) {
  const map = {
    pending: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    evaluating: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    approved: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    rejected: 'bg-red-500/15 text-red-600 dark:text-red-400',
    needs_clarification: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    out_of_scope: 'bg-gray-500/15 text-gray-500',
  }
  return map[s] || map.pending
}

function statusLabel(s) {
  const map = {
    pending: 'Pendiente',
    evaluating: 'En evaluación',
    approved: 'Aprobada',
    rejected: 'Rechazada',
    needs_clarification: 'Requiere aclaración',
    out_of_scope: 'Fuera de alcance',
  }
  return map[s] || s
}

function priorityBadgeClass(p) {
  const map = {
    critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
    high: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    medium: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    low: 'bg-gray-500/15 text-gray-500',
  }
  return map[p] || map.medium
}

function priorityLabel(p) {
  const map = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' }
  return map[p] || p
}

onMounted(async () => {
  await crStore.fetchAllChangeRequests()
})
</script>

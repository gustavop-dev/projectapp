<template>
  <div id="platform-unified-bugs">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
      <div>
        <h1 class="text-2xl font-bold text-esmerald dark:text-white">
          {{ authStore.isAdmin ? 'Reporte de bugs' : 'Mis bugs reportados' }}
        </h1>
        <p class="mt-1 text-sm text-green-light">
          {{ authStore.isAdmin ? 'Todos los bugs reportados en todos los proyectos.' : 'Bugs reportados en tus proyectos.' }}
        </p>
      </div>
      <label
        v-if="authStore.isAdmin"
        class="flex cursor-pointer items-center gap-2 rounded-full border border-esmerald/10 px-3 py-1.5 text-xs font-medium text-green-light dark:border-white/10"
      >
        <input v-model="includeArchived" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
        Mostrar archivados
      </label>
    </div>

    <!-- Loading -->
    <div v-if="bugStore.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <!-- Empty -->
    <div v-else-if="bugStore.bugReports.length === 0" class="rounded-3xl border border-dashed border-esmerald/10 py-20 text-center dark:border-white/10" data-enter>
      <p class="text-sm text-green-light">No hay bugs reportados en este momento.</p>
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
              :to="localePath(`/platform/projects/${group.projectId}/bugs`)"
              class="rounded-full border border-esmerald/10 px-3 py-1 text-[10px] font-medium text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
            >
              Ver bugs →
            </NuxtLink>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <div
              v-for="bug in group.items"
              :key="bug.id"
              class="group cursor-pointer rounded-xl border border-esmerald/[0.06] bg-white p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
              @click="navigateTo(`/platform/projects/${group.projectId}/bugs`)"
            >
              <div class="mb-2 flex items-center gap-2">
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="statusBadgeClass(bug.status)">
                  {{ statusLabel(bug.status) }}
                </span>
                <span v-if="bug.is_archived" class="rounded-full bg-gray-500/15 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-gray-600 dark:text-gray-400">
                  Archivado
                </span>
                <span v-if="bug.is_recurring" class="rounded-full bg-purple-500/15 px-1.5 py-0.5 text-[9px] font-bold uppercase text-purple-600 dark:text-purple-400">
                  Recurrente
                </span>
                <span v-if="bug.screenshot_url" class="ml-auto text-green-light/30">
                  <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                </span>
              </div>
              <h4 class="text-sm font-medium text-esmerald dark:text-white">{{ bug.title }}</h4>
              <div class="mt-2 flex items-center gap-2">
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="severityBadgeClass(bug.severity)">
                  {{ severityLabel(bug.severity) }}
                </span>
                <span class="text-[10px] text-green-light/50">{{ bug.reported_by_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformIncludeArchived } from '~/composables/usePlatformIncludeArchived'
import { usePlatformAuthStore } from '~/stores/platform-auth'

const localePath = useLocalePath()
import { usePlatformBugReportsStore } from '~/stores/platform-bug-reports'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
usePageEntrance('#platform-unified-bugs')

const authStore = usePlatformAuthStore()
const bugStore = usePlatformBugReportsStore()
const includeArchived = usePlatformIncludeArchived()

const summaryPills = computed(() => {
  const pills = [
    { key: 'reported', label: 'Reportados', dotClass: 'bg-red-500' },
    { key: 'confirmed', label: 'Confirmados', dotClass: 'bg-amber-500' },
    { key: 'fixing', label: 'En corrección', dotClass: 'bg-blue-500' },
    { key: 'qa', label: 'En QA', dotClass: 'bg-purple-500' },
    { key: 'resolved', label: 'Resueltos', dotClass: 'bg-emerald-500' },
  ]
  return pills
    .map((p) => ({ ...p, count: bugStore.bugReports.filter((b) => b.status === p.key).length }))
    .filter((p) => p.count > 0)
})

const groupedByProject = computed(() => {
  const groups = {}
  for (const bug of bugStore.bugReports) {
    const pid = bug.project_id
    if (!pid) continue
    if (!groups[pid]) {
      groups[pid] = { projectId: pid, projectName: bug.project_name || `Proyecto #${pid}`, items: [] }
    }
    groups[pid].items.push(bug)
  }
  const activeStatuses = ['reported', 'confirmed', 'fixing', 'qa']
  return Object.values(groups).sort((a, b) => {
    const aActive = a.items.filter((bug) => activeStatuses.includes(bug.status)).length
    const bActive = b.items.filter((bug) => activeStatuses.includes(bug.status)).length
    return bActive - aActive
  })
})

function statusBadgeClass(s) {
  const map = {
    reported: 'bg-red-500/15 text-red-600 dark:text-red-400',
    confirmed: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    fixing: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    qa: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    resolved: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    not_reproducible: 'bg-gray-500/15 text-gray-500',
    wont_fix: 'bg-gray-500/15 text-gray-500',
    duplicate: 'bg-gray-500/15 text-gray-500',
  }
  return map[s] || map.reported
}

function statusLabel(s) {
  const map = {
    reported: 'Reportado', confirmed: 'Confirmado', fixing: 'En corrección',
    qa: 'En QA', resolved: 'Resuelto', not_reproducible: 'No reproducible',
    wont_fix: 'No se corregirá', duplicate: 'Duplicado',
  }
  return map[s] || s
}

function severityBadgeClass(sev) {
  const map = {
    critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
    high: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    medium: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    low: 'bg-gray-500/15 text-gray-500',
  }
  return map[sev] || map.medium
}

function severityLabel(sev) {
  const map = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' }
  return map[sev] || sev
}

async function loadBugs() {
  await bugStore.fetchAllBugReports(null, authStore.isAdmin && includeArchived.value)
}

onMounted(async () => {
  await loadBugs()
})

watch(includeArchived, () => {
  if (authStore.isAdmin) loadBugs()
})
</script>

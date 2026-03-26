<template>
  <div id="platform-unified-board">
    <!-- Header -->
    <div class="mb-6" data-enter>
      <h1 class="text-2xl font-bold text-esmerald dark:text-white">
        {{ authStore.isAdmin ? 'Actividad general' : 'Mi tablero' }}
      </h1>
      <p class="mt-1 text-sm text-green-light">
        {{ authStore.isAdmin ? 'Requerimientos activos de todos los proyectos.' : 'Estado de los requerimientos de tus proyectos.' }}
      </p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <!-- Empty -->
    <div v-else-if="allCards.length === 0" class="rounded-3xl border border-dashed border-esmerald/10 py-20 text-center dark:border-white/10" data-enter>
      <p class="text-sm text-green-light">No hay requerimientos activos en este momento.</p>
    </div>

    <template v-else>
      <!-- Summary pills -->
      <div class="mb-6 flex flex-wrap gap-3" data-enter>
        <div
          v-for="col in summaryColumns"
          :key="col.key"
          class="flex items-center gap-2 rounded-full border border-esmerald/[0.06] bg-white px-4 py-2 dark:border-white/[0.06] dark:bg-esmerald"
        >
          <span class="h-2 w-2 rounded-full" :class="colDotClass(col.color)" />
          <span class="text-xs font-medium text-esmerald dark:text-white">{{ col.label }}</span>
          <span class="text-xs font-bold text-green-light">{{ col.count }}</span>
        </div>
      </div>

      <!-- Cards grouped by project -->
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
              :to="localePath(`/platform/projects/${group.projectId}/board`)"
              class="rounded-full border border-esmerald/10 px-3 py-1 text-[10px] font-medium text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
            >
              Ver tablero →
            </NuxtLink>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <div
              v-for="card in group.cards"
              :key="card.id"
              class="group cursor-pointer rounded-xl border border-esmerald/[0.06] bg-white p-4 transition hover:border-esmerald/15 hover:shadow-sm dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
              @click="navigateTo(`/platform/projects/${group.projectId}/board`)"
            >
              <div class="mb-2 flex items-center gap-2">
                <span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass(card.status)" />
                <span class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">{{ statusLabel(card.status) }}</span>
                <span v-if="card.module" class="ml-auto text-[10px] text-green-light/40">{{ card.module }}</span>
              </div>
              <h4 class="text-sm font-medium text-esmerald dark:text-white">{{ card.title }}</h4>
              <div class="mt-2 flex items-center gap-2">
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="priorityBadgeClass(card.priority)">
                  {{ priorityLabel(card.priority) }}
                </span>
                <span v-if="card.estimated_hours" class="text-[10px] text-green-light/50">{{ card.estimated_hours }}h</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'

const localePath = useLocalePath()
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import { usePlatformApi } from '~/composables/usePlatformApi'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

useHead({ title: 'Tablero general — ProjectApp' })
usePageEntrance('#platform-unified-board')

const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()

const isLoading = ref(true)
const allCards = ref([])
const projectMap = ref({})

const activeStatuses = ['todo', 'in_progress', 'in_review']

const summaryColumns = computed(() => {
  const cols = [
    { key: 'todo', label: 'Por hacer', color: 'blue' },
    { key: 'in_progress', label: 'En progreso', color: 'amber' },
    { key: 'in_review', label: 'En revisión', color: 'purple' },
  ]
  return cols.map((c) => ({
    ...c,
    count: allCards.value.filter((card) => card.status === c.key).length,
  })).filter((c) => c.count > 0)
})

const groupedByProject = computed(() => {
  const groups = {}
  for (const card of allCards.value) {
    if (!activeStatuses.includes(card.status)) continue
    const pid = card._projectId
    if (!groups[pid]) {
      groups[pid] = {
        projectId: pid,
        projectName: projectMap.value[pid] || `Proyecto #${pid}`,
        cards: [],
      }
    }
    groups[pid].cards.push(card)
  }
  return Object.values(groups).sort((a, b) => b.cards.length - a.cards.length)
})

function colDotClass(color) {
  const map = { blue: 'bg-blue-500', amber: 'bg-amber-500', purple: 'bg-purple-500', teal: 'bg-teal-500' }
  return map[color] || 'bg-gray-400'
}

function statusDotClass(status) {
  const map = { todo: 'bg-blue-500', in_progress: 'bg-amber-500', in_review: 'bg-purple-500', approval: 'bg-teal-500' }
  return map[status] || 'bg-gray-400'
}

function statusLabel(s) {
  const map = { todo: 'Por hacer', in_progress: 'En progreso', in_review: 'En revisión', done: 'Completado' }
  return map[s] || s
}

function priorityBadgeClass(priority) {
  const map = {
    critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
    high: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    medium: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    low: 'bg-gray-500/15 text-gray-500',
  }
  return map[priority] || map.medium
}

function priorityLabel(p) {
  const map = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' }
  return map[p] || p
}

onMounted(async () => {
  isLoading.value = true
  try {
    await projectsStore.fetchProjects()
    const projects = projectsStore.projects

    const pMap = {}
    for (const p of projects) {
      pMap[p.id] = p.name
    }
    projectMap.value = pMap

    const { get } = usePlatformApi()
    const cards = []
    for (const p of projects) {
      if (p.status === 'archived') continue
      try {
        const res = await get(`projects/${p.id}/requirements/`)
        for (const card of res.data) {
          cards.push({ ...card, _projectId: p.id })
        }
      } catch {
        // skip projects with errors
      }
    }
    allCards.value = cards
  } finally {
    isLoading.value = false
  }
})
</script>

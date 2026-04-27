<template>
  <div id="platform-unified-deliverables">
    <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
      <div>
        <h1 class="text-2xl font-bold text-text-default">
          {{ authStore.isAdmin ? 'Entregables' : 'Mis entregables' }}
        </h1>
        <p class="mt-1 text-sm text-green-light">
          {{ authStore.isAdmin ? 'Todos los entregables de todos los proyectos.' : 'Entregables de tus proyectos.' }}
        </p>
      </div>
      <label
        v-if="authStore.isAdmin"
        class="flex cursor-pointer items-center gap-2 rounded-full border border-border-default px-3 py-1.5 text-xs font-medium text-green-light"
      >
        <input v-model="includeArchived" type="checkbox" class="rounded border-border-default" />
        Mostrar archivados
      </label>
    </div>

    <div v-if="store.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-esmerald dark:border-t-lemon" />
    </div>

    <div v-else-if="store.deliverables.length === 0" class="rounded-3xl border border-dashed border-border-default py-20 text-center" data-enter>
      <p class="text-sm text-green-light">No hay entregables en este momento.</p>
    </div>

    <template v-else>
      <div class="mb-6 flex flex-wrap gap-3" data-enter>
        <div
          v-for="pill in summaryPills"
          :key="pill.key"
          class="flex items-center gap-2 rounded-full border border-border-default bg-surface px-4 py-2"
        >
          <span class="h-2 w-2 rounded-full" :class="pill.dotClass" />
          <span class="text-xs font-medium text-text-default">{{ pill.label }}</span>
          <span class="text-xs font-bold text-green-light">{{ pill.count }}</span>
        </div>
      </div>

      <div class="space-y-8" data-enter>
        <div v-for="group in groupedByProject" :key="group.projectId">
          <div class="mb-3 flex items-center gap-3">
            <NuxtLink
              :to="localePath(`/platform/projects/${group.projectId}`)"
              class="text-base font-semibold text-text-default transition hover:text-esmerald/70 dark:text-white dark:hover:text-accent"
            >
              {{ group.projectName }}
            </NuxtLink>
            <NuxtLink
              :to="localePath(`/platform/projects/${group.projectId}/deliverables`)"
              class="rounded-full border border-border-default px-3 py-1 text-[10px] font-medium text-green-light transition hover:text-text-default dark:hover:text-white"
            >
              Ver entregables →
            </NuxtLink>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <div
              v-for="d in group.items"
              :key="d.id"
              class="group cursor-pointer rounded-xl border border-border-default bg-surface p-4 transition hover:border-border-default hover:shadow-sm dark:hover:border-white/12"
              @click="navigateTo(`/platform/projects/${group.projectId}/deliverables`)"
            >
              <div class="mb-2 flex flex-wrap items-center gap-2">
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="categoryBadgeClass(d.category)">
                  {{ categoryLabel(d.category) }}
                </span>
                <span v-if="d.is_archived" class="rounded-full bg-gray-500/15 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-text-muted dark:text-text-subtle">Archivado</span>
                <span class="ml-auto rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold text-green-light dark:bg-white/10">v{{ d.current_version }}</span>
              </div>
              <h4 class="text-sm font-medium text-text-default">{{ d.title }}</h4>
              <div class="mt-2 flex items-center gap-2 text-[10px] text-green-light/50">
                <span>{{ d.file_name }}</span>
                <span class="ml-auto">{{ d.uploaded_by_name }}</span>
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
import { usePlatformDeliverablesStore } from '~/stores/platform-deliverables'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
usePageEntrance('#platform-unified-deliverables')

const authStore = usePlatformAuthStore()
const store = usePlatformDeliverablesStore()
const includeArchived = usePlatformIncludeArchived()

const summaryPills = computed(() => {
  const pills = [
    { key: 'designs', label: 'Diseños', dotClass: 'bg-purple-500' },
    { key: 'documents', label: 'Documentos', dotClass: 'bg-blue-500' },
    { key: 'credentials', label: 'Credenciales', dotClass: 'bg-amber-500' },
    { key: 'apks', label: 'APKs', dotClass: 'bg-emerald-500' },
    { key: 'other', label: 'Otros', dotClass: 'bg-gray-400' },
  ]
  return pills
    .map((p) => ({ ...p, count: store.deliverables.filter((d) => d.category === p.key).length }))
    .filter((p) => p.count > 0)
})

const groupedByProject = computed(() => {
  const groups = {}
  for (const d of store.deliverables) {
    const pid = d.project_id
    if (!pid) continue
    if (!groups[pid]) {
      groups[pid] = { projectId: pid, projectName: d.project_name || `Proyecto #${pid}`, items: [] }
    }
    groups[pid].items.push(d)
  }
  return Object.values(groups).sort((a, b) => b.items.length - a.items.length)
})

function categoryLabel(cat) {
  const map = { designs: 'Diseños', credentials: 'Credenciales', documents: 'Documentos', apks: 'APKs', other: 'Otros' }
  return map[cat] || cat
}
function categoryBadgeClass(cat) {
  const map = {
    designs: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    credentials: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    documents: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    apks: 'bg-emerald-500/15 text-text-brand dark:text-emerald-400',
    other: 'bg-gray-500/15 text-text-muted',
  }
  return map[cat] || map.other
}

async function loadDeliverables() {
  await store.fetchAllDeliverables(null, authStore.isAdmin && includeArchived.value)
}

onMounted(async () => {
  await loadDeliverables()
})

watch(includeArchived, () => {
  if (authStore.isAdmin) loadDeliverables()
})
</script>

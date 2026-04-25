<template>
  <div id="platform-access" class="space-y-6">
    <section class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between" data-enter>
      <div>
        <h1 class="font-light text-3xl text-esmerald dark:text-white">Accesos</h1>
        <p class="mt-2 max-w-2xl text-sm leading-7 text-green-light">
          URLs y credenciales de cada proyecto para entrar rápido a producción, staging, admin de Django y el repo.
        </p>
      </div>

      <div class="flex flex-col items-start gap-2 lg:items-end">
        <div class="w-full lg:max-w-sm">
          <input
            v-model="search"
            type="text"
            placeholder="Buscar por proyecto, cliente o URL"
            class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-esmerald dark:text-white dark:placeholder:text-green-light/40 dark:focus:border-lemon/40 dark:focus:ring-lemon/20"
          >
        </div>
        <button
          type="button"
          class="text-xs font-medium text-green-light transition hover:text-esmerald dark:hover:text-lemon"
          @click="load"
        >
          Actualizar
        </button>
      </div>
    </section>

    <div v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackVariant === 'success' ? 'border-emerald-500/20 bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300' : 'border-red-500/20 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-200'">
      {{ feedback }}
    </div>

    <div v-if="isLoading" class="rounded-3xl border border-esmerald/[0.06] bg-white px-6 py-14 text-center text-sm text-green-light dark:border-white/[0.06] dark:bg-esmerald">
      Cargando accesos...
    </div>

    <div v-else-if="filteredProjects.length === 0" class="rounded-3xl border border-esmerald/[0.06] bg-white px-6 py-14 text-center text-sm text-green-light dark:border-white/[0.06] dark:bg-esmerald">
      {{ search.trim() ? 'Ningún proyecto coincide con esa búsqueda.' : 'Todavía no hay proyectos con accesos configurados.' }}
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <article
        v-for="project in filteredProjects"
        :key="project.id"
        data-testid="access-card"
        class="flex flex-col gap-4 rounded-3xl border border-esmerald/[0.06] bg-white p-5 shadow-sm dark:border-white/[0.06] dark:bg-esmerald"
      >
        <header class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h2 class="truncate text-base font-semibold text-esmerald dark:text-white">
              {{ project.name }}
            </h2>
            <p class="mt-1 truncate text-xs text-green-light">
              {{ project.client_company || project.client_name }}
            </p>
          </div>
          <span
            class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
            :class="statusBadgeClass(project.status)"
          >
            {{ statusLabel(project.status) }}
          </span>
        </header>

        <div class="flex flex-col gap-2">
          <UrlRow label="Producción" :url="project.production_url" data-testid="url-production" />
          <UrlRow label="Staging" :url="project.staging_url" data-testid="url-staging" />
          <UrlRow label="Admin Django" :url="project.admin_url" data-testid="url-admin" />
          <UrlRow label="Repositorio" :url="project.repository_url" data-testid="url-repo" />
        </div>

        <div class="rounded-2xl border border-esmerald/10 bg-esmerald-light/40 p-3 dark:border-white/[0.06] dark:bg-esmerald-dark">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-[10px] font-semibold uppercase tracking-widest text-green-light/70">Credenciales admin</span>
            <button
              v-if="project.admin_password"
              type="button"
              class="text-xs font-medium text-esmerald transition hover:underline dark:text-lemon"
              @click="toggleReveal(project.id)"
            >
              {{ revealed[project.id] ? 'Ocultar' : 'Revelar' }}
            </button>
          </div>

          <div v-if="!project.admin_username && !project.admin_password" class="text-xs text-green-light/70">
            Sin credenciales. Añádelas en el admin de Django.
          </div>

          <div v-else class="space-y-2">
            <CopyField
              label="Usuario"
              :value="project.admin_username"
              :is-secret="false"
              data-testid="copy-username"
              @copy="flash('Usuario copiado.')"
            />
            <CopyField
              label="Contraseña"
              :value="project.admin_password"
              :is-secret="!revealed[project.id]"
              data-testid="copy-password"
              @copy="flash('Contraseña copiada.')"
            />
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import { usePageEntrance } from '~/composables/usePageEntrance'
import UrlRow from '~/components/platform/access/UrlRow.vue'
import CopyField from '~/components/platform/access/CopyField.vue'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
  platformRole: 'admin',
})

useHead({ title: 'Accesos — ProjectApp' })
usePageEntrance('#platform-access')

const store = usePlatformProjectsStore()
const projects = ref([])
const isLoading = ref(false)
const search = ref('')
const revealed = reactive({})
const feedback = ref('')
const feedbackVariant = ref('success')
let flashTimer = null

const load = async () => {
  isLoading.value = true
  const result = await store.fetchAccessList()
  isLoading.value = false
  if (result.success) {
    projects.value = result.data
  } else {
    projects.value = []
    feedback.value = result.message
    feedbackVariant.value = 'error'
  }
}

const toggleReveal = (id) => {
  revealed[id] = !revealed[id]
}

const flash = (message) => {
  feedback.value = message
  feedbackVariant.value = 'success'
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => { feedback.value = '' }, 2500)
}

const filteredProjects = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return projects.value
  return projects.value.filter((p) => {
    const haystack = [
      p.name, p.client_name, p.client_company, p.client_email,
      p.production_url, p.staging_url, p.admin_url, p.repository_url,
    ].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

const statusLabel = (s) => ({
  active: 'Activo',
  paused: 'Pausado',
  completed: 'Completado',
  archived: 'Archivado',
}[s] || s)

const statusBadgeClass = (s) => ({
  active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
  paused: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300',
  completed: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300',
  archived: 'bg-neutral-100 text-neutral-600 dark:bg-white/5 dark:text-green-light',
}[s] || 'bg-neutral-100 text-neutral-600 dark:bg-white/5 dark:text-green-light')

onMounted(load)
onUnmounted(() => {
  if (flashTimer) clearTimeout(flashTimer)
})
</script>

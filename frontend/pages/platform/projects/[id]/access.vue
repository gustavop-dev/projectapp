<template>
  <ProjectShell>
    <section v-if="project" class="space-y-6">
      <h2 class="text-base font-medium text-text-default">Accesos del proyecto</h2>

      <div class="grid gap-4 sm:grid-cols-2">
        <UrlCard label="Producción" :url="project.production_url" />
        <UrlCard label="Staging" :url="project.staging_url" />
        <UrlCard label="Repositorio" :url="project.repository_url" />
        <div class="rounded-2xl border border-border-default bg-surface p-4">
          <p class="text-xs uppercase tracking-wider text-green-light/70">Admin Django</p>
          <a v-if="project.admin_url" :href="project.admin_url" target="_blank" rel="noopener" class="mt-2 block text-sm text-text-default hover:underline">
            {{ project.admin_url }}
          </a>
          <p v-else class="mt-2 text-sm text-green-light/60">—</p>
          <div v-if="project.admin_username || project.admin_password" class="mt-3 space-y-1 text-sm">
            <p v-if="project.admin_username">
              Usuario:
              <code class="rounded bg-surface-muted px-1 text-xs">{{ project.admin_username }}</code>
            </p>
            <p v-if="project.admin_password">
              Contraseña:
              <code class="rounded bg-surface-muted px-1 text-xs" :class="{ 'blur-sm select-none': !revealPassword }">{{ project.admin_password }}</code>
              <button class="ml-2 text-xs text-text-brand underline" @click="revealPassword = !revealPassword">
                {{ revealPassword ? 'Ocultar' : 'Mostrar' }}
              </button>
            </p>
          </div>
        </div>
      </div>
    </section>
    <div v-else class="px-6 py-12 text-center text-green-light/60">Cargando…</div>
  </ProjectShell>
</template>

<script setup>
import { computed, h, ref } from 'vue'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'

definePageMeta({
  middleware: ['platform-auth'],
  platformRole: 'admin',
  layout: 'platform',
})

const projectsStore = usePlatformProjectsStore()
const project = computed(() => projectsStore.currentProject)
const revealPassword = ref(false)

// Inline component to avoid yet another file for a 6-line card.
const UrlCard = (props) =>
  h('div', { class: 'rounded-2xl border border-border-default bg-surface p-4' }, [
    h('p', { class: 'text-xs uppercase tracking-wider text-green-light/70' }, props.label),
    props.url
      ? h('a', { href: props.url, target: '_blank', rel: 'noopener', class: 'mt-2 block text-sm text-text-default hover:underline' }, props.url)
      : h('p', { class: 'mt-2 text-sm text-green-light/60' }, '—'),
  ])
UrlCard.props = ['label', 'url']
</script>

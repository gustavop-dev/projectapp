<template>
  <ProjectShell>
    <div id="platform-project-collection-accounts" class="space-y-6">
    <div data-enter>
      <h1 class="text-2xl font-bold text-text-default">Cuentas de cobro</h1>
      <p class="mt-1 text-sm text-green-light">Documentos de este proyecto.</p>
    </div>

    <div v-if="store.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border-default border-t-esmerald" />
    </div>

    <div v-else-if="store.accounts.length === 0" class="text-sm text-green-light">No collection accounts for this project.</div>

    <ul v-else class="space-y-3">
      <li
        v-for="row in store.accounts"
        :key="row.id"
        class="flex items-center justify-between rounded-2xl border border-border-default bg-surface px-4 py-3"
      >
        <div>
          <p class="font-medium text-text-default">{{ row.title }}</p>
          <p class="text-xs text-green-light">{{ row.public_number || 'draft' }} · {{ row.commercial_status }}</p>
        </div>
        <NuxtLink
          :to="localePath(`/platform/collection-accounts/${row.id}`)"
          class="text-sm font-medium text-text-brand"
        >
          Open
        </NuxtLink>
      </li>
    </ul>
  </div>
  </ProjectShell>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { usePlatformCollectionAccountsStore } from '~/stores/platform-collection-accounts'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'

const route = useRoute()
const localePath = useLocalePath()

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

const projectId = computed(() => route.params.id)
const deliverableFilterId = computed(() => route.query.deliverable_id || null)
const store = usePlatformCollectionAccountsStore()

onMounted(async () => {
  await store.fetchByProject(projectId.value, deliverableFilterId.value || null)
})
</script>

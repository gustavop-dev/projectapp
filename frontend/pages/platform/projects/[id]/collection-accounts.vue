<template>
  <div id="platform-project-collection-accounts" class="space-y-6">
    <NuxtLink
      :to="localePath(`/platform/projects/${projectId}`)"
      class="text-sm text-green-light hover:text-esmerald dark:hover:text-white"
    >
      ← Back to project
    </NuxtLink>

    <div data-enter>
      <h1 class="text-2xl font-bold text-esmerald dark:text-white">Collection accounts</h1>
      <p class="mt-1 text-sm text-green-light">Documents for this project.</p>
    </div>

    <div v-if="store.isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald" />
    </div>

    <div v-else-if="store.accounts.length === 0" class="text-sm text-green-light">No collection accounts for this project.</div>

    <ul v-else class="space-y-3">
      <li
        v-for="row in store.accounts"
        :key="row.id"
        class="flex items-center justify-between rounded-2xl border border-esmerald/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-esmerald"
      >
        <div>
          <p class="font-medium text-esmerald dark:text-white">{{ row.title }}</p>
          <p class="text-xs text-green-light">{{ row.public_number || 'draft' }} · {{ row.commercial_status }}</p>
        </div>
        <NuxtLink
          :to="localePath(`/platform/collection-accounts/${row.id}`)"
          class="text-sm font-medium text-esmerald dark:text-lemon"
        >
          Open
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { usePlatformCollectionAccountsStore } from '~/stores/platform-collection-accounts'

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

<script setup>
import { oneOf } from '~/components/base/propValidators'

/**
 * Loading silhouette for the documents list. Mirrors the real layout
 * (table rows on desktop / cards on grid) so content doesn't jump when
 * data arrives. Pulse pauses under prefers-reduced-motion (BaseSkeleton).
 */
defineProps({
  mode: { type: String, default: 'list', validator: oneOf(['list', 'grid']) },
  rows: { type: Number, default: 5 },
})
</script>

<template>
  <div role="status" data-testid="documents-skeleton">
    <span class="sr-only">Cargando documentos...</span>

    <!-- Table silhouette -->
    <div
      v-if="mode === 'list'"
      class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden"
      aria-hidden="true"
    >
      <div class="px-6 py-3 border-b border-border-muted flex items-center gap-6">
        <BaseSkeleton class="w-24" />
        <BaseSkeleton class="w-20" />
        <BaseSkeleton class="w-16" />
        <BaseSkeleton class="w-16 hidden md:block" />
      </div>
      <div
        v-for="i in rows"
        :key="i"
        class="px-6 py-4 border-b border-border-muted last:border-b-0 flex items-center gap-6"
      >
        <div class="flex-1 min-w-0 space-y-2">
          <BaseSkeleton class="w-2/5" />
          <BaseSkeleton class="w-1/4" />
        </div>
        <BaseSkeleton class="w-20 hidden sm:block" />
        <BaseSkeleton variant="circle" class="!w-6 !h-6" />
      </div>
    </div>

    <!-- Card grid silhouette -->
    <div
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4"
      aria-hidden="true"
    >
      <div
        v-for="i in rows"
        :key="i"
        class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden"
      >
        <BaseSkeleton variant="card" class="h-36 !rounded-none" />
        <div class="p-4 space-y-2">
          <BaseSkeleton class="w-3/4" />
          <BaseSkeleton class="w-1/2" />
        </div>
      </div>
    </div>
  </div>
</template>

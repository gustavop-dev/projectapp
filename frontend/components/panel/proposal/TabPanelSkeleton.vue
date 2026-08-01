<script setup>
/**
 * Placeholder shown while a lazily-loaded proposal tab chunk is in flight.
 *
 * Used as the `loadingComponent` of the defineAsyncComponent wrappers in
 * pages/panel/proposals/[id]/edit.vue. Vue's default 200ms delay applies, so
 * a chunk that resolves quickly never flashes this.
 */
import BaseSkeleton from '~/components/base/BaseSkeleton.vue';
</script>

<template>
  <div class="space-y-4 py-4" data-testid="tab-panel-skeleton">
    <span class="sr-only" role="status">Cargando pestaña...</span>
    <BaseSkeleton variant="line" class="w-1/3" />
    <BaseSkeleton variant="card" class="h-32" />
    <BaseSkeleton variant="line" class="w-2/3" />
    <BaseSkeleton variant="line" class="w-1/2" />
  </div>
</template>

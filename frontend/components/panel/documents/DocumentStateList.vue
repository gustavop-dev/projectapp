<script setup>
import { computed } from 'vue';
import {
  formatStateDuration,
  sortStateEpisodes,
  stateBadgeVariant,
} from '~/utils/documentState';

const props = defineProps({
  episodes: { type: Array, default: () => [] },
  maxVisible: { type: Number, default: 3 },
  showUnclassified: { type: Boolean, default: true },
  showHistory: { type: Boolean, default: false },
});
defineEmits(['history']);

const sorted = computed(() => sortStateEpisodes(props.episodes));
const visible = computed(() => sorted.value.slice(0, props.maxVisible));
const hiddenCount = computed(() => Math.max(0, sorted.value.length - visible.value.length));
const hasCycle = computed(() => sorted.value.some(
  (episode) => episode.state?.group_mode === 'exclusive',
));
</script>

<template>
  <div class="flex min-w-0 flex-wrap items-center gap-1.5" data-testid="document-state-list">
    <BaseBadge
      v-if="showUnclassified && !hasCycle"
      variant="neutral"
      size="sm"
      data-testid="document-state-unclassified"
    >
      Por clasificar
    </BaseBadge>
    <BaseBadge
      v-for="episode in visible"
      :key="episode.id"
      :variant="stateBadgeVariant(episode.state)"
      size="sm"
      :class="episode.state?.system_key === 'needs_fix' ? 'ring-2 ring-danger-strong/30 font-semibold' : ''"
      :data-testid="episode.state?.system_key === 'needs_fix' ? 'document-state-needs-fix' : `document-state-${episode.state?.id}`"
      :title="`${episode.state?.name}: ${formatStateDuration(episode.duration_seconds)}`"
    >
      <span v-if="episode.state?.system_key === 'needs_fix'" aria-hidden="true">⚠</span>
      <span>{{ episode.state?.name }}</span>
      <span class="opacity-75">· {{ formatStateDuration(episode.duration_seconds) }}</span>
    </BaseBadge>
    <BaseBadge v-if="hiddenCount" variant="neutral" size="sm" :title="`${hiddenCount} estados más`">
      +{{ hiddenCount }}
    </BaseBadge>
    <BaseButton
      v-if="showHistory"
      type="button"
      variant="ghost"
      size="sm"
      icon-only
      aria-label="Ver historial de estados"
      title="Ver historial de estados"
      data-testid="document-state-history-open"
      @click="$emit('history')"
    >
      ◷
    </BaseButton>
  </div>
</template>

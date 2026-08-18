<template>
  <div class="border border-border-muted rounded-lg" :data-testid="`tabs-manager-${view}`">
    <div class="flex items-center justify-between gap-3 px-3 py-2.5">
      <button
        type="button"
        class="flex items-center gap-2 text-sm text-text-default"
        :data-testid="`tabs-manager-toggle-${view}`"
        @click="toggle"
      >
        <ChevronRightIcon
          class="w-4 h-4 text-text-muted transition-transform"
          :class="{ 'rotate-90': isOpen }"
        />
        {{ label }}
      </button>
      <BaseButton
        variant="secondary"
        size="sm"
        :disabled="isResetting"
        :data-testid="`settings-reset-tabs-${view}`"
        @click="emit('reset', { view, label })"
      >
        {{ isResetting ? 'Restableciendo...' : 'Restablecer' }}
      </BaseButton>
    </div>

    <div v-if="isOpen" class="border-t border-border-muted px-3 py-2.5">
      <p v-if="tabs.isLoading.value" class="text-xs text-text-subtle">
        Cargando pestañas...
      </p>
      <p v-else-if="!orderedTabs.length" class="text-xs text-text-subtle">
        Esta vista todavía no tiene pestañas guardadas.
      </p>
      <ul v-else class="space-y-1">
        <li
          v-for="(tab, index) in orderedTabs"
          :key="tab.id"
          class="flex items-center gap-2"
          :data-testid="`tabs-manager-row-${tab.id}`"
        >
          <BaseCheckbox
            :model-value="!tab.is_hidden"
            :data-testid="`tabs-manager-visible-${tab.id}`"
            @update:model-value="setVisible(tab, $event)"
          />
          <span
            class="text-sm flex-1 truncate"
            :class="tab.is_hidden ? 'text-text-subtle line-through' : 'text-text-default'"
          >
            {{ tab.name }}
          </span>
          <!--
            A builtin's placeholder is a factory chip too: it carries no
            filters of its own, but here it reads exactly like a seeded tab,
            and that the distinction is invisible is the point.
          -->
          <span
            v-if="tab.is_seeded || tab.builtin_key"
            class="text-[10px] uppercase tracking-wider text-text-subtle"
          >
            De fábrica
          </span>
          <BaseButton
            variant="ghost"
            size="sm"
            :disabled="index === 0"
            :data-testid="`tabs-manager-up-${tab.id}`"
            aria-label="Subir"
            @click="move(index, -1)"
          >
            <ChevronUpIcon class="w-4 h-4" />
          </BaseButton>
          <BaseButton
            variant="ghost"
            size="sm"
            :disabled="index === orderedTabs.length - 1"
            :data-testid="`tabs-manager-down-${tab.id}`"
            aria-label="Bajar"
            @click="move(index, 1)"
          >
            <ChevronDownIcon class="w-4 h-4" />
          </BaseButton>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
/**
 * Administration of one view's filter strip: which tabs show, in what order,
 * and the button that puts the factory ones back.
 *
 * Loads its tabs lazily. Settings lists eight views, and fetching all of
 * them on mount would spend eight round-trips on a card most visits never
 * open.
 */
import { computed, ref } from 'vue';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  ChevronUpIcon,
} from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseCheckbox from '~/components/base/BaseCheckbox.vue';
import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

const props = defineProps({
  view: { type: String, required: true },
  label: { type: String, required: true },
  isResetting: { type: Boolean, default: false },
});

const emit = defineEmits(['reset']);

const tabs = useSavedFilterTabs(props.view);
const isOpen = ref(false);

const orderedTabs = computed(() =>
  [...tabs.savedTabs.value].sort((a, b) => (a.order || 0) - (b.order || 0)),
);

async function toggle() {
  isOpen.value = !isOpen.value;
  if (isOpen.value && !tabs.isReady.value) await tabs.loadTabs();
}

function setVisible(tab, visible) {
  tabs.updateTab(tab.id, { is_hidden: !visible });
}

function move(index, delta) {
  const next = [...orderedTabs.value];
  const target = index + delta;
  if (target < 0 || target >= next.length) return;
  [next[index], next[target]] = [next[target], next[index]];
  tabs.reorderTabs(next.map((tab) => tab.id));
}

/** Re-read after the parent's reset, so the list is not left stale. */
async function refresh() {
  if (isOpen.value) await tabs.loadTabs();
}

defineExpose({ refresh });
</script>

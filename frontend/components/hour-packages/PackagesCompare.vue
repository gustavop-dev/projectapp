<template>
  <div class="flex gap-4 overflow-x-auto pb-2">
    <article
      v-for="pkg in packages"
      :key="pkg.id"
      class="relative flex-1 min-w-[210px] max-w-[280px] bg-surface rounded-xl shadow-sm border p-5 flex flex-col"
      :class="[
        pkg.id === bestValueId ? 'border-primary ring-1 ring-primary' : 'border-border-muted',
        { 'opacity-60': !pkg.is_active },
      ]"
      :data-testid="`hour-package-tier-${pkg.id}`"
    >
      <span
        v-if="pkg.id === bestValueId"
        class="absolute -top-2.5 left-1/2 -translate-x-1/2 text-[10px] px-2.5 py-0.5 rounded-full font-medium bg-primary text-white whitespace-nowrap"
      >
        Mejor tarifa
      </span>

      <h3 class="text-sm font-medium text-text-default">{{ pkg.name_es }}</h3>
      <p class="text-xs text-text-subtle mb-4">{{ pkg.name_en }}</p>

      <p class="text-4xl font-light text-text-default">
        {{ pkg.hours }}<span class="text-base text-text-muted ml-1">h</span>
      </p>

      <div class="mt-3">
        <p class="text-lg font-medium text-text-default leading-tight">
          {{ money(effectiveRate(pkg), pkg.currency) }}<span class="text-xs text-text-muted">/h</span>
        </p>
        <p v-if="Number(pkg.discount_percent) > 0" class="text-xs text-text-subtle">
          <span class="line-through">{{ money(pkg.hourly_rate, pkg.currency) }}/h</span>
          <span class="ml-1.5 px-1.5 py-0.5 rounded-full font-medium bg-primary-soft text-text-brand no-underline">
            -{{ pkg.discount_percent }}%
          </span>
        </p>
      </div>

      <p class="mt-3 pt-3 border-t border-border-muted text-sm text-text-muted">
        Total <span class="font-medium text-text-default">{{ money(totalPrice(pkg), pkg.currency) }}</span>
      </p>

      <p v-if="pkg.note_es" class="mt-2 text-xs text-text-subtle flex-1">{{ pkg.note_es }}</p>
      <span v-else class="flex-1" />

      <div class="mt-4 flex items-center gap-3">
        <NuxtLink
          :to="localePath(`/panel/hour-packages/${pkg.id}/edit`)"
          class="text-xs text-text-brand font-medium"
        >
          Editar
        </NuxtLink>
        <button
          type="button"
          class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors"
          @click="$emit('delete', pkg)"
        >
          Eliminar
        </button>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import {
  bestValuePackageId,
  effectiveRate,
  totalPrice,
  formatPackageMoney as money,
} from '~/utils/hourPackagePricing';

const props = defineProps({
  packages: { type: Array, required: true },
});

defineEmits(['delete']);

const localePath = useLocalePath();
const bestValueId = computed(() => bestValuePackageId(props.packages));
</script>

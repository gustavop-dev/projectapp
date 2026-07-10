<template>
  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
    <article
      v-for="pkg in packages"
      :key="pkg.id"
      class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 flex flex-col"
      :class="{ 'opacity-60': !pkg.is_active }"
      :data-testid="`hour-package-card-${pkg.id}`"
    >
      <div class="flex items-start justify-between gap-3">
        <div>
          <NuxtLink
            :to="localePath(`/panel/hour-packages/${pkg.id}/edit`)"
            class="text-sm font-medium text-text-default hover:text-text-brand transition-colors"
          >
            {{ pkg.name_es }}
          </NuxtLink>
          <p class="text-xs text-text-subtle">{{ pkg.name_en }}</p>
        </div>
        <span
          class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0"
          :class="pkg.is_active ? 'bg-primary-soft text-text-brand' : 'bg-surface-raised text-text-muted'"
        >
          {{ pkg.is_active ? 'Activo' : 'Inactivo' }}
        </span>
      </div>

      <p class="mt-4 text-3xl font-light text-text-default">
        {{ pkg.hours }}<span class="text-base text-text-muted ml-1">h</span>
      </p>

      <dl class="mt-3 space-y-1.5 text-sm flex-1">
        <div class="flex items-center justify-between">
          <dt class="text-text-muted">Tarifa efectiva</dt>
          <dd class="font-medium text-text-default">{{ money(effectiveRate(pkg), pkg.currency) }}/h</dd>
        </div>
        <div v-if="Number(pkg.discount_percent) > 0" class="flex items-center justify-between">
          <dt class="text-text-muted">Sobre {{ money(pkg.hourly_rate, pkg.currency) }}/h</dt>
          <dd>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium bg-primary-soft text-text-brand">
              -{{ pkg.discount_percent }}%
            </span>
          </dd>
        </div>
        <div class="flex items-center justify-between border-t border-border-muted pt-2">
          <dt class="text-text-muted">Total</dt>
          <dd class="font-medium text-text-default">{{ money(totalPrice(pkg), pkg.currency) }}</dd>
        </div>
      </dl>

      <p v-if="pkg.note_es" class="mt-3 text-xs text-text-subtle">{{ pkg.note_es }}</p>

      <div class="mt-4 pt-3 border-t border-border-muted flex items-center gap-3">
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
import { effectiveRate, totalPrice, formatPackageMoney as money } from '~/utils/hourPackagePricing';

defineProps({
  packages: { type: Array, required: true },
});

defineEmits(['delete']);

const localePath = useLocalePath();
</script>

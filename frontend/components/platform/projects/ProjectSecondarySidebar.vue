<template>
  <aside class="w-full shrink-0 self-start rounded-3xl border border-border-default bg-surface px-3 py-3 shadow-sm lg:w-56 lg:py-4">
    <div class="flex gap-1 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible lg:pb-0">
      <template v-for="item in items" :key="item.disabled ? item.label : item.href">
        <span
          v-if="item.disabled"
          class="flex shrink-0 cursor-not-allowed items-center justify-between gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium opacity-40"
        >
          {{ item.label }}
          <span class="rounded-full bg-surface-muted px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-text-muted">Pronto</span>
        </span>
        <NuxtLink
          v-else
          :to="item.href"
          :class="[
            'flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium transition',
            isActive(item.href)
              ? 'bg-primary-soft text-text-brand dark:bg-lemon/10 dark:text-accent'
              : 'text-green-light hover:bg-primary-soft hover:text-text-brand dark:hover:text-accent',
          ]"
        >
          {{ item.label }}
        </NuxtLink>
      </template>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  projectId: { type: [String, Number], required: true },
})

const localePath = useLocalePath()
const route = useRoute()

const items = computed(() => {
  const base = `/platform/projects/${props.projectId}`
  return [
    { label: 'Resumen',           href: localePath(base) },
    { label: 'Tablero',           href: localePath(`${base}/board`) },
    { label: 'Solicitudes',       href: localePath(`${base}/changes`) },
    { label: 'Bugs',              href: localePath(`${base}/bugs`) },
    { label: 'Recursos',          href: localePath(`${base}/deliverables`) },
    { label: 'Hosting',           href: localePath(`${base}/payments`) },
    { label: 'Cuentas de cobro',  href: localePath(`${base}/collection-accounts`), disabled: true },
    { label: 'Modelo de datos',   href: localePath(`${base}/data-model`), disabled: true },
    { label: 'Accesos',           href: localePath(`${base}/access`), disabled: true },
  ]
})

function isActive(href) {
  const stripped = (p) => p.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  return stripped(route.path) === stripped(href)
}
</script>

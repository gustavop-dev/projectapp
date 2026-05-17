<template>
  <aside class="w-56 shrink-0 self-start rounded-3xl border border-border-default bg-surface px-3 py-4 shadow-sm">
    <NuxtLink
      v-for="item in items"
      :key="item.href"
      :to="item.href"
      :class="[
        'mb-1 flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition',
        isActive(item.href)
          ? 'bg-primary-soft text-text-brand dark:bg-lemon/10 dark:text-accent'
          : 'text-green-light hover:bg-primary-soft/50 hover:text-text-brand dark:hover:text-accent',
      ]"
    >
      {{ item.label }}
    </NuxtLink>
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
    { label: 'Pagos',             href: localePath(`${base}/payments`) },
    { label: 'Cuentas de cobro',  href: localePath(`${base}/collection-accounts`) },
    { label: 'Modelo de datos',   href: localePath(`${base}/data-model`) },
    { label: 'Accesos',           href: localePath(`${base}/access`) },
  ]
})

function isActive(href) {
  const stripped = (p) => p.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  return stripped(route.path) === stripped(href)
}
</script>

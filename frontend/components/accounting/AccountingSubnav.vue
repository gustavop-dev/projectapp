<template>
  <nav class="flex flex-wrap items-center gap-2 mb-5" aria-label="Secciones de contabilidad">
    <NuxtLink
      v-for="item in items"
      :key="item.key"
      :to="localePath(item.to)"
      :data-testid="`accounting-subnav-${item.key}`"
      :aria-current="active === item.key ? 'page' : undefined"
      :class="[
        'px-4 py-2 rounded-xl text-sm font-medium transition-colors',
        active === item.key
          ? 'bg-primary text-white'
          : 'bg-surface-raised text-text-muted hover:bg-border-muted',
      ]"
    >
      {{ item.label }}
    </NuxtLink>
  </nav>
</template>

<script setup>
defineProps({
  active: { type: String, default: 'index' },
});

const localePath = useLocalePath();

const items = [
  { key: 'index', label: 'Resumen', to: '/panel/accounting' },
  { key: 'incomes', label: 'Ingresos', to: '/panel/accounting/incomes' },
  { key: 'expenses', label: 'Gastos', to: '/panel/accounting/expenses' },
  { key: 'hostings', label: 'Hostings', to: '/panel/accounting/hostings' },
  { key: 'pocket', label: 'Bolsillo', to: '/panel/accounting/pocket' },
  { key: 'recurring', label: 'Recurrentes', to: '/panel/accounting/recurring' },
  { key: 'ads', label: 'Ads', to: '/panel/accounting/ads' },
  { key: 'cards', label: 'Tarjetas', to: '/panel/accounting/cards' },
  { key: 'history', label: 'Historial', to: '/panel/accounting/history' },
  { key: 'settings', label: 'Configuración', to: '/panel/accounting/settings' },
];
</script>

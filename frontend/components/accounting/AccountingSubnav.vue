<template>
  <div class="mb-5">
    <!--
      Móvil: las doce secciones colapsan en un selector.

      Envolviendo en pastillas ocupaban cuatro filas en un celular, casi media
      pantalla, y empujaban el contenido debajo del pliegue: al entrar al
      Bolsillo lo primero que se veía era la navegación y había que desplazarse
      para llegar al saldo, que es el dato por el que se entró. Una fila.
    -->
    <BaseMobileTabSelect
      variant="nav"
      test-id="accounting-subnav-select"
      aria-label="Sección de contabilidad"
      :model-value="active"
      :options="selectOptions"
      @update:model-value="goTo"
    />

    <nav
      class="hidden md:flex flex-wrap items-center gap-2"
      aria-label="Secciones de contabilidad"
    >
      <NuxtLink
        v-for="item in items"
        :key="item.key"
        :to="localePath(item.to)"
        :data-testid="`accounting-subnav-${item.key}`"
        :aria-current="active === item.key ? 'page' : undefined"
        :class="[
          'px-4 py-2 rounded-xl text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50',
          active === item.key
            ? 'bg-primary text-white'
            : 'bg-surface-raised text-text-muted hover:bg-border-muted',
        ]"
      >
        {{ item.label }}
      </NuxtLink>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue';

defineProps({
  active: { type: String, default: 'index' },
});

const localePath = useLocalePath();
const router = useRouter();

const items = [
  { key: 'index', label: 'Resumen', to: '/panel/accounting' },
  { key: 'pocket', label: 'Bolsillo', to: '/panel/accounting/pocket' },
  { key: 'incomes', label: 'Ingresos', to: '/panel/accounting/incomes' },
  { key: 'expenses', label: 'Gastos', to: '/panel/accounting/expenses' },
  { key: 'hostings', label: 'Hostings', to: '/panel/accounting/hostings' },
  { key: 'collections', label: 'Cuentas de cobro', to: '/panel/accounting/collections' },
  { key: 'recurring', label: 'Recurrentes', to: '/panel/accounting/recurring' },
  { key: 'ads', label: 'Ads', to: '/panel/accounting/ads' },
  { key: 'cards', label: 'Tarjetas', to: '/panel/accounting/cards' },
  { key: 'statements', label: 'Extractos', to: '/panel/accounting/statements' },
  { key: 'history', label: 'Historial', to: '/panel/accounting/history' },
  { key: 'settings', label: 'Configuración', to: '/panel/accounting/settings' },
];

// El desplegable se arma del MISMO array que las pastillas, así que el orden no
// puede divergir entre móvil y escritorio: son dos lecturas de una sola lista,
// no dos listas que hay que mantener de acuerdo.
const selectOptions = computed(() =>
  items.map((item) => ({ value: item.key, label: item.label })),
);

function goTo(key) {
  const item = items.find((candidate) => candidate.key === key);
  if (item) router.push(localePath(item.to));
}
</script>

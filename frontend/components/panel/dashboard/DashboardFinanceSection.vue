<template>
  <section
    v-if="finance"
    aria-labelledby="dashboard-finance-title"
    data-testid="dashboard-finance-section"
  >
    <div class="mb-3 flex items-center justify-between">
      <h2
        id="dashboard-finance-title"
        class="text-xs font-semibold uppercase tracking-widest text-text-muted"
      >
        Finanzas
      </h2>
      <NuxtLink
        :to="localePath('/panel/accounting')"
        class="text-xs text-text-brand hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring rounded"
      >
        Ver contabilidad →
      </NuxtLink>
    </div>

    <div class="grid gap-4 lg:grid-cols-3">
      <AccountingHeroKpi
        class="lg:col-span-2"
        :label="`Utilidad líquida ${finance.year}`"
        :value="Number(finance.liquid_utility) || 0"
        :sub="`Ingresos líquidos menos gastos de la empresa en ${finance.year}`"
        :tone="Number(finance.liquid_utility) >= 0 ? 'success' : 'danger'"
        :monthly="finance.monthly || []"
      />
      <div class="grid gap-4 content-start">
        <DashboardStatTile
          label="Bolsillo"
          :value="Number(finance.pocket_balance)"
          format="currency"
          tone="brand"
          :to="localePath('/panel/accounting/pocket')"
        />
        <DashboardStatTile
          label="Deuda tarjetas"
          :value="Number(finance.card_debt?.total)"
          format="currency"
          :tone="Number(finance.card_debt?.total) > 0 ? 'warning' : 'default'"
          :sub="utilizationSub"
          :to="localePath('/panel/accounting/cards')"
        />
      </div>
    </div>

    <div class="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-3">
      <DashboardStatTile
        label="Por cobrar este mes"
        :value="Number(finance.expected_current_month?.total)"
        format="currency"
        :sub="finance.expected_current_month?.label || ''"
        :to="localePath('/panel/accounting/incomes')"
      />
      <DashboardStatTile
        label="Recurrentes / mes"
        :value="Number(finance.recurring_monthly_cost)"
        format="currency"
        :to="localePath('/panel/accounting/recurring')"
      />
      <DashboardStatTile
        label="Hostings activos"
        :value="Number(finance.hostings?.active_count)"
        format="number"
        :sub="hostingSub"
        :to="localePath('/panel/accounting/hostings')"
      />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import AccountingHeroKpi from '~/components/accounting/AccountingHeroKpi.vue';
import DashboardStatTile from '~/components/panel/dashboard/DashboardStatTile.vue';
import { formatMoney } from '~/utils/formatMoney';

/** Finance block of the global dashboard; superuser-only (null hides it). */
const props = defineProps({
  finance: { type: Object, default: null },
});

const localePath = useLocalePath();

const utilizationSub = computed(() => {
  const pct = props.finance?.card_debt?.utilization_pct;
  return pct !== null && pct !== undefined ? `${pct}% del cupo` : '';
});

const hostingSub = computed(() => {
  const income = Number(props.finance?.hostings?.monthly_income) || 0;
  return income > 0 ? `${formatMoney(income)}/mes` : '';
});
</script>

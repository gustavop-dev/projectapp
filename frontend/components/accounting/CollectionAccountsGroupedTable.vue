<template>
  <IncomeGroupedTable
    v-bind="$attrs"
    aria-label="Cuentas de cobro agrupadas"
    row-noun="cuentas de cobro"
    all-selection-article="todas las"
    selection-article="las"
    filtered-adjective="filtradas"
    group-noun="grupos"
    group-test-prefix="collection"
  >
    <template v-for="(_, slotName) in $slots" #[slotName]="slotProps">
      <slot :name="slotName" v-bind="slotProps" />
    </template>
  </IncomeGroupedTable>
</template>

<script setup>
import IncomeGroupedTable from '~/components/accounting/IncomeGroupedTable.vue';

defineOptions({ inheritAttrs: false });
</script>

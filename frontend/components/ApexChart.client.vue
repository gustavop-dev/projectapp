<template>
  <VueApexCharts v-bind="$attrs" />
</template>

<script setup>
import VueApexCharts from 'vue3-apexcharts/core';
import 'apexcharts/line';
import 'apexcharts/area';
import 'apexcharts/bar';
import 'apexcharts/donut';
import 'apexcharts/radialBar';
import 'apexcharts/features/legend';
import 'apexcharts/features/annotations';
import 'apexcharts/features/exports';

defineOptions({ inheritAttrs: false });
</script>

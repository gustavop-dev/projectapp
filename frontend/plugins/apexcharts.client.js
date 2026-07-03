import VueApexCharts from 'vue3-apexcharts';

// Client-only: ApexCharts touches window/document at import time.
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(VueApexCharts);
});

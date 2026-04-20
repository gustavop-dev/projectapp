<script setup>
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const router = useRouter();

onMounted(() => {
  router.replace(localePath('/panel/defaults') + '?mode=proposal&tab=emails');
});
</script>

<template>
  <div class="text-center py-16 text-gray-400 dark:text-green-light/60 text-sm">
    Redirigiendo...
  </div>
</template>

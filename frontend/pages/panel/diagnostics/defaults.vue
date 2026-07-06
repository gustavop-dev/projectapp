<script setup>
definePageMeta({
  middleware: [
    'admin-auth',
    (to) => {
      const query = { ...to.query, mode: 'diagnostic' };
      return navigateTo({ path: '/panel/defaults', query }, { replace: true });
    },
  ],
});
</script>

<template>
  <div />
</template>

<script setup>
definePageMeta({
  middleware: [
    'admin-auth',
    (to) => {
      const query = { ...to.query, mode: 'proposal' };
      return navigateTo({ path: '/panel/defaults', query }, { replace: true });
    },
  ],
});
</script>

<template>
  <div />
</template>

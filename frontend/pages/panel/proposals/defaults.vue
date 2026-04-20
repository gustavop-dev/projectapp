<script setup>
definePageMeta({
  middleware: [
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

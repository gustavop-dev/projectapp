<script setup>
definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

await navigateTo('/platform/dashboard')
</script>

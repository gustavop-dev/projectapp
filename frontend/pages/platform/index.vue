<script setup>
definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

defineI18nRoute(false)

await navigateTo('/platform/dashboard')
</script>

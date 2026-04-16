<script setup>
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
await navigateTo(localePath('/panel/tasks'), { replace: true });
</script>

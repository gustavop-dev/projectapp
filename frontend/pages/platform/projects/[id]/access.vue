<script setup>
import { computed } from 'vue'
import ProjectAccessEditor from '~/components/projects/ProjectAccessEditor.vue'
import ProjectShell from '~/components/platform/projects/ProjectShell.vue'
import { usePlatformApi } from '~/composables/usePlatformApi'
import { createProjectAccessApi } from '~/services/projectAccessApi'

definePageMeta({
  middleware: ['platform-auth'],
  platformRole: 'admin',
  layout: 'platform',
})

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const platformApi = usePlatformApi()
const accessApi = computed(() => createProjectAccessApi({
  get: platformApi.get,
  post: platformApi.post,
  patch: platformApi.patch,
  remove: platformApi.delete,
}, `projects/${projectId.value}/access/`))
</script>

<template>
  <ProjectShell>
    <ProjectAccessEditor v-if="projectId" :key="projectId" :api="accessApi" />
  </ProjectShell>
</template>

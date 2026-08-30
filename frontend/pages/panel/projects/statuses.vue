<script setup>
import StateCatalogManager from '~/components/panel/states/StateCatalogManager.vue';
import { useProjectStateStore } from '~/stores/project_states';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });
useHead({ title: 'Estados de proyectos | ProjectApp' });

const stateStore = useProjectStateStore();
const operationalEffects = [
  { value: 'development', label: 'En construcción' },
  { value: 'operating', label: 'Operando y cobrable' },
  { value: 'suspended', label: 'Suspendido por servicio' },
  { value: 'completed', label: 'Cierre correcto' },
  { value: 'decommissioned', label: 'Baja definitiva' },
];
</script>

<template>
  <StateCatalogManager
    :state-store="stateStore"
    title="Estados de proyectos"
    description="Administra los nombres y colores del ciclo real. El efecto operativo conserva el significado de negocio aunque un estado se renombre."
    back-to="/panel/projects"
    back-label="Volver a proyectos"
    test-id="project-state-catalog"
    active-count-field="active_project_count"
    active-count-label="proyectos"
    :manage-groups="false"
    :operational-effects="operationalEffects"
  />
</template>

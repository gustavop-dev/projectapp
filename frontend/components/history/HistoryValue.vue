<script setup>
import { computed } from 'vue';
const props = defineProps({ value: { default: null }, labels: { type: Object, default: () => ({}) } });
const labels = {
  title: 'Título', content_markdown: 'Contenido', content_json: 'Contenido', sections: 'Secciones',
  client: 'Cliente', client_user: 'Cliente', folder: 'Carpeta', project: 'Proyecto', tags: 'Etiquetas',
  states: 'Estados', status: 'Estado', notes: 'Notas', document_notes: 'Notas del documento', name: 'Nombre', description: 'Descripción',
  first_name: 'Nombre', last_name: 'Apellido', email: 'Correo', phone: 'Teléfono',
  company_name: 'Empresa', cedula: 'Documento de identidad', nit: 'NIT', billing_code: 'Código de facturación',
  access: 'Accesos', access_notes: 'Notas del proyecto', production: 'Producción', staging: 'Staging',
  admin_url: 'URL de administración', admin_username: 'Usuario', password: 'Contraseña', content: 'Contenido',
  total_investment: 'Inversión', currency: 'Moneda', discount_percent: 'Descuento', language: 'Idioma',
  items: 'Ítems', collection_account: 'Datos de cobro', payment_methods: 'Medios de pago',
  client_email_subject: 'Asunto preparado', client_email_body: 'Correo preparado',
  client_whatsapp_message: 'WhatsApp preparado', client_custom_notes: 'Notas privadas',
  production_url: 'URL de producción', staging_url: 'URL de staging', repository_url: 'Repositorio',
  generated_file: 'Archivo emitido', commercial_status: 'Estado comercial', total: 'Total',
};
const isObject = computed(() => props.value !== null && typeof props.value === 'object');
const readable = (key) => props.labels[key] || labels[key] || key.replaceAll('_', ' ');
</script>

<template>
  <span v-if="value === null || value === ''" class="text-text-subtle">Sin valor</span>
  <span v-else-if="value?.protected" class="text-text-subtle">{{ value.present ? '••••••••' : 'Sin valor' }}</span>
  <span v-else-if="isObject && 'id' in value && 'label' in value">{{ value.label }}</span>
  <dl v-else-if="isObject" class="space-y-2 break-words">
    <div v-for="(item, key) in value" :key="key" class="border-l border-border-muted pl-3">
      <dt class="text-xs font-medium text-text-muted">{{ Array.isArray(value) ? Number(key) + 1 : readable(key) }}</dt>
      <dd class="mt-1 text-sm text-text-default"><HistoryValue :value="item" :labels="props.labels" /></dd>
    </div>
  </dl>
  <span v-else class="whitespace-pre-wrap break-words">{{ typeof value === 'boolean' ? (value ? 'Sí' : 'No') : value }}</span>
</template>

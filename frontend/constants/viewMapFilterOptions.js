import { viewCatalogSections } from '~/config/viewCatalog';

export const viewCategoryOptions = viewCatalogSections.map((s) => ({
  value: s.id,
  label: s.label,
}));

export const viewAudienceOptions = [
  { value: 'public', label: 'Publico (cualquiera)' },
  { value: 'admin', label: 'Admin / Vendedor' },
  { value: 'client', label: 'Cliente' },
];

export const viewTypeOptions = [
  { value: 'list', label: 'Listado' },
  { value: 'detail', label: 'Detalle' },
  { value: 'create', label: 'Crear' },
  { value: 'edit', label: 'Editar' },
  { value: 'readonly', label: 'Solo lectura' },
  { value: 'dashboard', label: 'Dashboard' },
  { value: 'config', label: 'Configuracion' },
  { value: 'auth', label: 'Autenticacion' },
];

export const viewCategoryLabelMap = Object.fromEntries(
  viewCategoryOptions.map((o) => [o.value, o.label]),
);

export const viewAudienceLabelMap = Object.fromEntries(
  viewAudienceOptions.map((o) => [o.value, o.label]),
);

export const viewTypeLabelMap = Object.fromEntries(
  viewTypeOptions.map((o) => [o.value, o.label]),
);

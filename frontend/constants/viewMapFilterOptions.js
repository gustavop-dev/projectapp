import {
  VIEW_AUDIENCES,
  VIEW_TYPES,
  viewCatalogSections,
} from '~/config/viewCatalog';

export const viewCategoryOptions = viewCatalogSections.map((s) => ({
  value: s.id,
  label: s.label,
}));

const audienceLabels = {
  public: 'Publico (cualquiera)',
  admin: 'Admin / Vendedor',
  client: 'Cliente',
};

export const viewAudienceOptions = VIEW_AUDIENCES.map((value) => ({
  value,
  label: audienceLabels[value],
}));

const viewTypeLabels = {
  list: 'Listado',
  detail: 'Detalle',
  create: 'Crear',
  edit: 'Editar',
  readonly: 'Solo lectura',
  dashboard: 'Dashboard',
  config: 'Configuracion',
  auth: 'Autenticacion',
  redirect: 'Redirección',
};

export const viewTypeOptions = VIEW_TYPES.map((value) => ({
  value,
  label: viewTypeLabels[value],
}));

export const viewCategoryLabelMap = Object.fromEntries(
  viewCategoryOptions.map((o) => [o.value, o.label]),
);

export const viewAudienceLabelMap = Object.fromEntries(
  viewAudienceOptions.map((o) => [o.value, o.label]),
);

export const viewTypeLabelMap = Object.fromEntries(
  viewTypeOptions.map((o) => [o.value, o.label]),
);

# Tema del Programa de Alianza

- **Rol:** visitante.
- **Success:** cambiar entre claro y oscuro conserva legibilidad de contenido,
  controles y diálogos en los cinco perfiles responsive. Recargar restaura la
  elección sin cambiar el tema del panel.
- **Presentación:** tarjetas elevadas sobre el fondo, interiores diferenciados
  y encabezado sin separador horizontal, tanto en claro como en oscuro. Las
  secciones entran una sola vez con transición breve; movimiento reducido
  desactiva esa entrada. El nuevo observer no impone un estado oculto previo.
- **Failure:** una carga fallida conserva el tema guardado en el mensaje de
  error y al recuperar el programa con Reintentar.
- **Error:** no hay entradas inválidas para este interruptor; almacenamiento
  no disponible no impide usar el tema durante la visita.
- **Display:** no se registra una interacción adicional; se valida como parte
  del cambio de tema.

# Señales pendientes — bandeja de candidatas

Cuando la calculadora clasifica una funcionalidad *"sin señal — por analogía"*, registra aquí la señal propuesta (append, nunca sobrescribir). Este archivo es la bandeja de entrada para la próxima versión del catálogo (`effort-indicators.md`); las señales se promueven manualmente tras revisión del dueño — el skill nunca modifica el catálogo directamente.

Formato de cada entrada:

`- <DDMMYYYY> · nivel sugerido: <XS|S|M|L|XL> · señal propuesta: "<texto>" · origen: "<funcionalidad del requerimiento>"`

---

- 02072026 · nivel sugerido: M · señal propuesta: "Texto sugerido automáticamente por el sistema a partir de datos ya registrados, editable por el usuario antes de persistir (observaciones, descripciones, respuestas precargadas)" · origen: "CD-06 Observación automática sugerida desde traslados + comentarios del usuario (Vástago Conteo Diario)" · **promovida al catálogo el 02072026**
- 02072026 · nivel sugerido: S · señal propuesta: "Retiro controlado de un comportamiento ya entregado — eliminar endpoint/acción + su UI + reescribir las pruebas que lo cubrían (≠ ocultar un elemento, que es XS; sube a M si exige decidir/archivar datos históricos)" · origen: "CD-11 Retirar la generación de ajustes del conteo actual (Vástago Conteo Diario)" · **promovida al catálogo el 02072026**
- 02072026 · nivel sugerido: M · señal propuesta: "Bloqueo/reserva exclusiva de un registro por usuario — al iniciar el trabajo el registro queda reservado a quien lo tomó y el segundo usuario recibe un mensaje de bloqueo (lock con select_for_update o equivalente; suele sumar el modificador Concurrencia/atomicidad; la liberación por timeout/vencimiento se cotiza con su tarea programada)" · origen: "ID-11 Bloqueo de concurrencia por Grupo+Bodega (Vástago Inventario Detallado)" · **promovida al catálogo el 02072026**

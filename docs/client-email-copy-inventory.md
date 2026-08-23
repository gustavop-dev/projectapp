# Inventario de correos enviados a clientes

**Actualizado:** 2026-08-23  
**Fuente ejecutable:** `backend/content/services/client_email_inventory.py`  
**Punto único de salida:** `backend/content/services/email_delivery_service.py`

Este documento enumera todas las salidas que ProjectApp clasifica como correo
dirigido a un cliente. Cada clave está registrada en el inventario ejecutable y
asignada a una familia administrable. El gateway rechaza una clasificación
`client` que no figure aquí; además, una prueba estática impide que código de
producción envíe por SMTP por fuera del gateway.

## Inventario completo

| # | Familia configurable | Clave de plantilla | Salida / disparador |
|---:|---|---|---|
| 1 | Propuestas | `proposal_sent_client` | Envío o reenvío individual de la propuesta comercial. |
| 2 | Propuestas | `proposal_multi_sent_client` | Un solo correo que agrupa varias propuestas del mismo cliente. |
| 3 | Propuestas | `proposal_reminder` | Recordatorio automático de propuesta vigente. |
| 4 | Propuestas | `proposal_urgency` | Aviso de urgencia con descuento, automático o manual. |
| 5 | Propuestas | `proposal_urgency_no_discount` | Aviso de urgencia sin descuento. |
| 6 | Propuestas | `proposal_accepted_client` | Confirmación al cliente cuando acepta la propuesta. |
| 7 | Propuestas | `proposal_finished_client` | Confirmación al cliente cuando la propuesta/proyecto termina. |
| 8 | Propuestas | `proposal_rejected_client` | Agradecimiento/confirmación al rechazar la propuesta. |
| 9 | Propuestas | `proposal_reengagement` | Seguimiento de reactivación posterior al rechazo o inactividad. |
| 10 | Propuestas | `proposal_abandonment_followup` | Seguimiento por abandono después de consultar la propuesta. |
| 11 | Propuestas | `proposal_investment_interest_followup` | Seguimiento por interacción con la inversión/calculadora. |
| 12 | Propuestas | `proposal_scheduled_followup` | Seguimiento programado desde el ciclo comercial. |
| 13 | Propuestas | `proposal_negotiation_confirmation` | Confirmación al cliente de su solicitud de negociación. |
| 14 | Propuestas | `magic_link` | Enlaces de acceso solicitados para consultar sus propuestas. |
| 15 | Diagnósticos | `diagnostic_initial_sent` | Envío inicial del diagnóstico técnico. |
| 16 | Diagnósticos | `diagnostic_final_sent` | Entrega del diagnóstico técnico terminado. |
| 17 | Diagnósticos | `diagnostic_custom_email` | Correo compuesto desde un diagnóstico cuando se dirige al email real del cliente. |
| 18 | Diagnósticos | `diagnostic_documents_sent` | Envío de documentos adjuntos del diagnóstico. |
| 19 | Documentos y correos manuales | `proposal_documents_sent` | Envío de documentos adjuntos de una propuesta. |
| 20 | Documentos y correos manuales | `branded_email` | Correo manual con marca; los independientes se tratan como salida externa y los asociados a propuesta se copian cuando van al email del cliente. |
| 21 | Documentos y correos manuales | `proposal_email` | Correo manual asociado a propuesta cuando se dirige al email del cliente. |
| 22 | Cuentas de cobro | `collection_account_sent` | Emisión, reenvío y retry manual de una cuenta de cobro; los tres caminos conservan la misma clave. |
| 23 | Plataforma | `document_signed_client` | Confirmación al cliente de que su firma quedó registrada. |

## Lo que no pertenece al inventario de clientes

- Los avisos de cobro, calendario de pagos, vencimientos de hosting, saldos de
  tarjetas, extractos, cambios contables y estados de pago que existen hoy se
  envían al equipo interno. No son correos al cliente y no generan esta copia.
- Las alertas internas del ciclo de propuestas —aperturas, comentarios,
  interés, etapas, vencimientos y actividad— siguen usando su lista de avisos
  internos y no la lista de copias.
- Invitaciones, contraseñas temporales, OTP, verificación de correo y
  restablecimiento/cambio de contraseña se clasifican como seguridad. No se
  copian para no duplicar credenciales ni enlaces de acceso.
- Un correo compuesto para una propuesta o diagnóstico que se dirige a una
  dirección distinta de la del cliente se clasifica como interno. Esto permite
  escribir a un stakeholder o a la agencia sin provocar una copia adicional.

Si en el futuro aparece un aviso de cobro o vencimiento dirigido realmente al
cliente, deberá recibir una clave nueva o reutilizar una clave cliente adecuada,
entrar al inventario y pasar su prueba parametrizada antes de poder enviarse.

## Política de copia y trazabilidad

1. El correo principal se entrega primero.
2. Sólo si esa entrega devuelve éxito, el gateway resuelve los destinatarios
   activos de la familia correspondiente.
3. Cada destinatario interno recibe un sobre independiente, sólo en `BCC`; su
   dirección no aparece en los encabezados visibles para el cliente.
4. Una falla de BCC no cambia el resultado del envío principal ni dispara su
   retry. Se guarda como un `EmailLog` interno con rol `copy`, asociado por
   `delivery_id` al registro principal.
5. Los historiales muestran esas copias debajo del envío principal, con
   destinatario, estado y error. Los dashboards, rate limits, contadores de
   contacto y retries operan sólo sobre filas `primary`.

## Configuración y volumen

La lista vive en **Panel → Emails → Configuración → Copias de correos a
clientes** y es independiente de los destinatarios de avisos internos. Cada
fila puede pausarse, eliminarse o limitarse a estas familias:

- Propuestas
- Diagnósticos
- Documentos y correos manuales
- Cuentas de cobro
- Plataforma

Al crear un destinatario quedan seleccionadas todas las familias, de modo que
el comportamiento inicial es “copiar todo”. La segmentación permite reducir el
volumen después sin cambiar código. Cada correo principal puede producir hasta
un correo SMTP adicional por destinatario configurado; conviene vigilar cuota,
ruido de bandeja y almacenamiento del historial.

## Activación inicial

No se sembró una dirección personal en una migración ni en settings. Después de
desplegar y aplicar la migración, se debe agregar `carlos18bp@gmail.com` desde la
pantalla de Configuración con las cinco familias seleccionadas. Así la dirección
queda como dato administrable y puede cambiarse sin una nueva versión.

## Evidencia de prueba

- 23 casos parametrizados validan uno por uno que cada clave resuelva su familia.
- Un caso valida que la audiencia de propuestas coincida exactamente con este
  inventario, sin claves faltantes ni sobrantes.
- Un guard estático recorre todo el backend productivo y falla ante imports o
  llamadas SMTP directas fuera del gateway.
- Las pruebas del gateway cubren éxito principal, copia BCC, múltiples copias,
  destinatarios inactivos, dirección duplicada, error de configuración, falla
  SMTP de la copia, falla del correo principal, adjuntos y HTML idénticos,
  clasificación interna/seguridad y claves cliente desconocidas.
- Las pruebas de integración cubren recordatorio de propuesta, emisión/reenvío
  de cuenta de cobro y confirmación de firma; Playwright cubre CRUD/configuración,
  segmentación, pausa, errores y visualización de una BCC fallida en historial.

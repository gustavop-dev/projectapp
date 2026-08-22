# Guion repetible — módulo contable responsivo

Este guion es el criterio de aceptación de PA-77. Se ejecuta completo después
de cualquier cambio en componentes base, tablas, filtros, navegación o modales
del panel. El resultado son **60 recorridos mínimos**: 12 secciones por los 5
anchos oficiales. No se reemplaza un ancho por “se ve parecido”.

## Preparación

1. Usar un superusuario con datos en los doce tabs.
2. Incluir, como mínimo:
   - un ingreso esperado parcial, uno líquido y uno perdido;
   - un ingreso sin cliente y otro sin proyecto;
   - un gasto de empresa, uno personal y una deducción;
   - un hosting vigente con ciclos y correo de facturación;
   - una cuenta de cobro emitida con notas;
   - pagos recurrentes en COP y USD, repartidos en dos categorías;
   - dos movimientos de Bolsillo, uno IN y uno OUT;
   - un extracto con transacciones, alias y PDF;
   - registros en Historial de cambios y de correos.
3. Abrir DevTools, desactivar zoom y fijarlo en 100 %.
4. Empezar cada recorrido arriba de la página (`scrollY = 0`) y sin un modal
   abierto. Probar en tema claro y repetir al menos Celular en tema oscuro.

## Anchos oficiales

| Perfil | Viewport | Navegación esperada |
|---|---:|---|
| Celular | 412 × 915 | selector de sección y selector de filtros guardados |
| Tableta vertical | 835 × 1195 | selector de sección y selector de filtros guardados |
| Tableta horizontal | 1195 × 835 | tira de 12 secciones y tira de filtros |
| Portátil | 1440 × 900 | tiras completas; columnas de escritorio según espacio |
| Monitor 27″ | 2560 × 1440 | contenido centrado, sin estirarse más allá del máximo |

## Comprobaciones comunes en cada recorrido

Marcar el recorrido como fallido si cualquiera de estas condiciones no se
cumple:

- No existe scroll horizontal en la página. En consola:
  `document.documentElement.scrollWidth <= document.documentElement.clientWidth`.
- La sección activa se reconoce y se puede cambiar con teclado y táctil.
- En Celular y Tableta vertical no aparecen las doce pastillas de navegación.
- En Tableta horizontal, Portátil y Monitor no aparece el selector móvil.
- La tira de filtros guardados no corta, pierde ni vuelve inalcanzable una
  opción; en angosto se usa un selector.
- Buscador, filtros, exportación y CTA principal no se solapan.
- Texto, montos, badges y acciones no se recortan. Una columna agrupada se lee
  bajo la identidad de su fila con su etiqueta de negocio.
- Toda acción alcanzable por hover también se alcanza con click/tap y teclado.
- Los controles táctiles tienen, como mínimo, 44 × 44 px.
- Al abrir un modal en Celular ocupa la pantalla completa; su título, contenido,
  errores y acciones finales siguen alcanzables. En los otros perfiles conserva
  el ancho semántico y no supera el alto visible.
- Al cerrar un modal, el foco vuelve a un control útil y la página recupera el
  scroll.
- En Monitor el contenido permanece relacionado y centrado: no debe repartirse
  por los 2560 px completos.

## Matriz de los 60 recorridos

Ejecutar cada fila en este orden para los cinco perfiles anteriores. Registrar
`OK`, `Falla` o `N/A` —este último exige una explicación— en una copia de las
cinco columnas de resultado.

| # | Sección | Decisión de negocio que debe comprobarse |
|---:|---|---|
| 1 | Resumen | La utilidad líquida sigue siendo el indicador principal. En angosto se ven, como máximo, los tres indicadores de decisión; “Ver todos los indicadores” revela el resto. La tabla mensual conserva Mes y Utilidad, y agrupa Esperado, Líquido y Gastos bajo Mes. Tarjetas conserva Tarjeta y Deuda. |
| 2 | Bolsillo | Concepto y Valor siguen visibles. Cada movimiento muestra inmediatamente **Saldo después**; con filtros muestra **Acumulado filtrado**. La columna independiente de saldo sólo aparece desde Tableta horizontal. El saldo general entra en la primera pantalla del Celular. |
| 3 | Ingresos | Concepto y Total permanecen. Cliente, tipo de ingreso, cobro, mes, origen y proyecto se agrupan según el perfil. Los siete indicadores muestran tres prioridades y un detalle desplegable en angosto. Alternar Lista/Agrupada no introduce scroll horizontal. |
| 4 | Gastos | Concepto y Total permanecen. Período, categoría, contabilidad y repartos se agrupan. Los indicadores prioritarios son total anual, mes actual y deducciones; el detalle revela gasto principal y reparto empresa/personal. |
| 5 | Hostings | Cliente, Valor/mes y Estado permanecen. Dominio y Vigencia vuelven como columnas desde Tableta horizontal; Proyecto, Modalidad, Ciclos y Total pagado se agrupan. En angosto hay una sola acción por fila y su menú ofrece ciclos, cobro, correos, editar y eliminar. |
| 6 | Cuentas de cobro | Número, Total y Estado permanecen. Cliente y Vence vuelven desde Tableta horizontal; origen, proyecto y emisión se agrupan. En angosto hay una sola acción por fila y ninguna acción del estado actual se pierde. |
| 7 | Recurrentes | Nombre y equivalente COP mensual permanecen. Los demás datos se agrupan. El encabezado de categoría pone el nombre en su propia línea en angosto y conserva subtotal y participación legibles. Lista y vista agrupada mantienen las mismas prioridades. |
| 8 | Ads | Plataforma y Valor permanecen. Fecha, tarjeta, participación y acumulado se agrupan. El indicador anual, buscador, filtros y CTA caben sin solaparse. |
| 9 | Tarjetas | Tarjeta y Deuda permanecen. Fecha, disponible, uso y notas se agrupan. Catálogo y formulario apilan sus campos y acciones en orden previsible. |
| 10 | Extractos | La cuadrícula mensual usa 2/3/4 columnas según perfil. En el detalle, Comercio y Valor encabezan cada transacción angosta; fecha, descripción, categoría y cuota quedan debajo. El menú móvil conserva editar encabezado, agregar, finalizar/reabrir y eliminar. Alias usa una fila compacta editable. |
| 11 | Historial | Los dos ámbitos —Cambios y Correos— siguen alcanzables junto con sus filtros guardados. Registro/Acción y Destinatario/Estado son las identidades; fecha, usuario, entidad, aviso y asunto se agrupan sin duplicar texto en el DOM. Expandir una fila conserva el contexto. |
| 12 | Configuración | Destinatarios, plantillas y tarjetas apilan sus formularios sin cortar campos. Agregar email, guardar y restablecer filtros son acciones de ancho completo en Celular y vuelven a su ancho natural desde Tableta vertical. |

## Recorrido de modales largos

Ejecutar los siguientes casos, como mínimo, en Celular, Tableta vertical y
Tableta horizontal. En Portátil y Monitor basta repetirlos cuando cambie el
componente base o el propio modal.

| Caso | Pasos y resultado esperado |
|---|---|
| Nueva cuenta de cobro | Completar cliente e ingreso, llegar a Previsualizar, alternar Correo/PDF en angosto, volver a editar y regresar al paso 2. Nunca aparecen dos paneles ilegibles lado a lado por debajo de 1024 px. Confirmar y enviar permanece alcanzable. |
| Liquidar ingreso | Abrir un esperado, registrar abono parcial, desplegar bloques condicionales y agregar un siguiente ingreso esperado. Fechas, valores, errores y CTA no se cortan. |
| Registrar abono múltiple | Seleccionar varios ingresos, repartir un valor, provocar una suma inválida y corregirla. El motivo de bloqueo y las acciones se leen sin scroll lateral. |
| Nuevo ingreso | Cambiar entre Esperado, Líquido y Perdido; alternar origen, cliente/proyecto, reparto de socios y registro en Bolsillo. Los campos aparecen en un orden estable y no desplazan las acciones fuera del modal. |
| Hosting | Crear/editar, crear cliente dentro del modal y recorrer los campos de vigencia, modalidad y cobro. Las acciones apilan en Celular. |
| Extracto | Crear un extracto, editar encabezado y agregar una transacción. El formulario, la carga de PDF y los botones se mantienen dentro del viewport. |

## Evidencia de ejecución

Guardar una fila por hallazgo en la ficha o PR:

| Fecha | Commit | Perfil | Sección/modal | Resultado | Evidencia o defecto |
|---|---|---|---|---|---|
| AAAA-MM-DD | SHA | 412 × 915 | Bolsillo | OK/Falla | captura, video o enlace al issue |

Una ejecución se considera completa cuando existen 60 resultados de sección y
los seis casos de modal en los tres perfiles obligatorios. Si se corrige una
falla, repetir la fila afectada y una fila vecina que use el mismo componente.

# Propuesta de Diagnóstico de Aplicación

## Índice

- [Propósito](#propósito)
- [Escala de Severidad](#escala-de-severidad)
- [Radiografía de la Aplicación](#radiografía-de-la-aplicación)
  - [¿Qué incluye esta radiografía?](#qué-incluye-esta-radiografía)
  - [Clasificación por Tamaño](#clasificación-por-tamaño)
- [Categorías que se evalúan en el diagnóstico](#categorías-que-se-evalúan-en-el-diagnóstico)
  - [1. Arquitectura y Estructura Interna](#1-arquitectura-y-estructura-interna)
  - [2. Calidad del Código](#2-calidad-del-código)
  - [3. Interfaz de Usuario y Experiencia](#3-interfaz-de-usuario-y-experiencia-lo-que-el-usuario-ve)
  - [4. Base de Datos y Gestión de la Información](#4-base-de-datos-y-gestión-de-la-información)
  - [5. Seguridad](#5-seguridad)
  - [6. Rendimiento](#6-rendimiento)
  - [7. Escalabilidad](#7-escalabilidad)
  - [8. Pruebas y Criterios de Calidad](#8-pruebas-y-criterios-de-calidad)
  - [9. Mantenibilidad y Evolución](#9-mantenibilidad-y-evolución)
  - [10. Confiabilidad y Tolerancia a Fallos](#10-confiabilidad-y-tolerancia-a-fallos)
  - [11. Integraciones y Comunicación entre Componentes](#11-integraciones-y-comunicación-entre-componentes)
  - [12. Vigencia Tecnológica](#12-vigencia-tecnológica)
  - [13. Documentación y Gestión del Conocimiento](#13-documentación-y-gestión-del-conocimiento)
  - [14. Capacidades Funcionales](#14-capacidades-funcionales-qué-necesidades-resuelve-y-cómo)
- [Estructura de la Entrega](#estructura-de-la-entrega)
  - [Lo que se encontró bien](#lo-que-se-encontró-bien)
  - [Hallazgos y oportunidades de mejora](#hallazgos-y-oportunidades-de-mejora)
  - [Recomendaciones](#recomendaciones)
- [Resumen Ejecutivo](#resumen-ejecutivo)
- [Costo y Formas de Pago](#costo-y-formas-de-pago)
- [Cronograma](#cronograma)
- [Alcance y Consideraciones](#alcance-y-consideraciones)

---

## Propósito

Esta propuesta presenta el alcance, las categorías de evaluación y la estructura de entrega de un diagnóstico integral para una aplicación web, realizado a partir de la revisión de sus repositorios de código (backend y frontend). El objetivo es evaluar el estado actual de la aplicación, identificar fortalezas, oportunidades de mejora y entregar recomendaciones priorizadas que sirvan como base para la toma de decisiones técnicas y de negocio.

> **Alcance:** Este diagnóstico se realiza exclusivamente sobre los repositorios de código fuente. No se evalúa la infraestructura del servidor, el proceso de despliegue ni los sistemas de monitoreo, ya que no se tiene acceso a esos entornos.

---

## Escala de Severidad

Los hallazgos, oportunidades de mejora y recomendaciones resultantes del diagnóstico se clasifican usando la siguiente escala:

| Nivel       | Significado                                                                                                                                          |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Crítico** | Representa un riesgo inmediato. Puede causar caídas, pérdida de datos, brechas de seguridad o bloqueo total del equipo. Debe atenderse con urgencia. |
| **Alto**    | Problema serio que impacta significativamente la calidad, el rendimiento o la capacidad de evolución. Debe planificarse a corto plazo.               |
| **Medio**   | Problema real pero manejable. Genera fricción, deuda técnica o ineficiencias. Se recomienda abordar a mediano plazo.                                 |
| **Bajo**    | Mejora deseable que aporta valor pero no representa un riesgo. Se puede abordar cuando haya espacio en la planificación.                             |

---

## Radiografía de la Aplicación

Como parte del diagnóstico, se levanta un inventario general de la aplicación para dimensionar su tamaño, complejidad y nivel de madurez técnica. Esta radiografía permite contextualizar los hallazgos y establecer expectativas realistas sobre el esfuerzo de mejora.

### ¿Qué incluye esta radiografía?

- **Tecnologías utilizadas:** Qué lenguajes, frameworks y herramientas principales se usan en el backend y en el frontend.
- **Cantidad de pantallas o vistas:** Cuántas pantallas tiene la aplicación del lado del usuario.
- **Cantidad de entidades o tablas:** Cuántas "cosas" maneja la aplicación (usuarios, productos, pedidos, etc.), reflejado en las tablas de la base de datos.
- **Cantidad de endpoints o rutas del backend:** Cuántos puntos de comunicación ofrece el backend (cada acción que el frontend le puede pedir al servidor).
- **Cantidad de componentes del frontend:** Cuántas piezas reutilizables tiene la interfaz.
- **Integraciones externas:** Con cuántos servicios de terceros se conecta la aplicación (pasarelas de pago, envío de correos, APIs externas, etc.).
- **Módulos o dominios funcionales:** Cuántas áreas de negocio distintas cubre la aplicación (autenticación, facturación, reportes, notificaciones, etc.).

### Clasificación por Tamaño

Con base en este inventario, la aplicación se clasifica en una de las siguientes categorías de tamaño:

| Dimensión                  | Pequeña       | Mediana        | Grande       |
|----------------------------|---------------|----------------|--------------|
| Entidades / tablas         | Menos de 15   | Entre 15 y 50  | Más de 50    |
| Endpoints / rutas backend  | Menos de 30   | Entre 30 y 100 | Más de 100   |
| Pantallas / vistas         | Menos de 15   | Entre 15 y 50  | Más de 50    |
| Componentes frontend       | Menos de 20   | Entre 20 y 80  | Más de 80    |
| Integraciones externas     | 0 a 2         | 3 a 7          | Más de 7     |
| Módulos funcionales        | 1 a 3         | 4 a 8          | Más de 8     |

**¿Cómo se lee la tabla?** No es necesario que todas las dimensiones caigan en la misma columna. Se evalúa el panorama general. Si la mayoría de los indicadores apuntan a "mediana", la aplicación se clasifica como mediana, incluso si una dimensión cae en otra columna.

**¿Para qué sirve esta clasificación?** Permite dimensionar el esfuerzo del diagnóstico, establecer expectativas realistas y servir como referencia para estructurar el alcance y valor del servicio.

---

## Categorías que se evalúan en el diagnóstico

---

### 1. Arquitectura y Estructura Interna

Cómo está organizada la aplicación por dentro. Si el código está ordenado y bien separado en capas lógicas, o si es un "plato de espagueti" donde todo está mezclado. Si los patrones de diseño que se usaron tienen sentido. Si un equipo nuevo podría entender cómo funciona sin depender de una sola persona.

---

### 2. Calidad del Código

Qué tan limpio, legible y consistente es lo que está escrito. Si se siguen convenciones, si hay código duplicado, si los nombres de las cosas tienen sentido, si hay complejidad innecesaria.

---

### 3. Interfaz de Usuario y Experiencia (Lo que el usuario ve)

Si la aplicación tiene partes construidas con tecnologías distintas (algunas más viejas que otras) y qué tan sostenible es esa mezcla. La velocidad de carga y la fluidez de la experiencia. Que funcione bien tanto en celular como en computador. La coherencia visual y de interacción entre las distintas partes de la aplicación.

---

### 4. Base de Datos y Gestión de la Información

Cómo se guardan, organizan y consultan los datos. Si la estructura tiene sentido, si hay datos duplicados o inconsistentes, si las consultas son eficientes, si se gestionan las migraciones correctamente.

---

### 5. Seguridad

Qué tan protegida está la aplicación contra accesos no autorizados, robo de datos, ataques o mal uso. Esto se evalúa desde lo que se puede observar en el código: cómo se manejan contraseñas, permisos, validaciones y datos sensibles.

---

### 6. Rendimiento

Qué tan rápida es la aplicación en sus operaciones. Los cuellos de botella que se pueden identificar desde el código: consultas lentas, procesos que bloquean al usuario, carga innecesaria de recursos.

---

### 7. Escalabilidad

No "¿qué tan rápida es hoy?" sino "¿está preparada para crecer?" Desde el código se evalúa si las decisiones de diseño permiten que la aplicación soporte más usuarios, más datos y más transacciones sin requerir reescribirla.

---

### 8. Pruebas y Criterios de Calidad

Qué tipos de pruebas existen y cuáles faltan. Cubre: pruebas unitarias, pruebas de contrato, pruebas de integración con base de datos real y permisos y efectos secundarios, pruebas con mocking y casos extremos, pruebas de extremo a extremo (E2E), pruebas de carga y rendimiento, y pruebas de seguridad y configuración. También evalúa qué tan automatizadas están y si se ejecutan como parte del proceso de desarrollo.

---

### 9. Mantenibilidad y Evolución

Qué tan fácil es hacerle cambios, corregir errores o agregar funcionalidades sin romper lo existente. Qué tan acopladas están las piezas entre sí.

---

### 10. Confiabilidad y Tolerancia a Fallos

Qué tan estable es en el día a día, evaluado desde el código. Qué pasa cuando algo sale mal: ¿el código maneja los errores correctamente o se desploma todo? ¿Las operaciones críticas protegen los datos ante fallos?

---

### 11. Integraciones y Comunicación entre Componentes

Cómo se conectan las partes internas entre sí (frontend y backend) y con sistemas o servicios externos. Si esas conexiones están bien organizadas y manejan errores adecuadamente.

---

### 12. Vigencia Tecnológica

Qué tan actualizadas están las herramientas, librerías y plataformas. Qué riesgo hay de obsolescencia. Si las tecnologías elegidas tienen futuro y si se puede encontrar talento capacitado.

---

### 13. Documentación y Gestión del Conocimiento

Qué tanto está explicado y registrado. Si cualquier equipo nuevo podría entender la aplicación sin depender de la tradición oral de una o dos personas.

---

### 14. Capacidades Funcionales (Qué necesidades resuelve y cómo)

Desde el código y la estructura, qué funcionalidades ofrece la aplicación, qué problemas resuelve y de qué manera lo hace. Si hay módulos incompletos, lógica de negocio dispersa, soluciones improvisadas o funcionalidades abandonadas.

---

## Estructura de la Entrega

Para cada categoría evaluada, la entrega del diagnóstico incluirá las siguientes secciones:

---

### Lo que se encontró bien

Se documentan las prácticas, decisiones o implementaciones que hoy están funcionando correctamente. Esto permite reconocer fortalezas reales de la aplicación y señalar qué vale la pena conservar.

> Ejemplo: "El modelo de datos está bien normalizado y las migraciones están versionadas con un historial limpio."

---

### Hallazgos y oportunidades de mejora

Se documentan los problemas, riesgos o debilidades encontradas. Cada hallazgo se presenta con su respectiva clasificación de severidad.

| Hallazgo | Nivel | Descripción |
|----------|-------|-------------|
| No existen pruebas unitarias en el módulo de pagos | **Crítico** | El módulo más sensible del sistema no tiene ninguna cobertura de pruebas. Cualquier cambio puede introducir errores en cobros reales. |
| Código duplicado en validaciones de formularios | **Medio** | La misma lógica de validación se repite en 5 controladores distintos. Genera inconsistencias y dificulta el mantenimiento. |
| No hay documentación de la API | **Alto** | Los endpoints no están documentados. Un equipo nuevo no puede integrarse sin hacer ingeniería inversa del código. |

---

### Recomendaciones

Se proponen acciones concretas para abordar los hallazgos identificados. Cada recomendación conserva el nivel de severidad del hallazgo que busca resolver.

| Sugerencia | Nivel | Relación |
|------------|-------|----------|
| Implementar pruebas unitarias para el módulo de pagos como prioridad inmediata | **Crítico** | Resuelve la falta de cobertura en el módulo más sensible |
| Crear un servicio centralizado de validación de formularios | **Medio** | Elimina la duplicación en los 5 controladores afectados |
| Generar documentación automática con Swagger/OpenAPI | **Alto** | Cubre la falta de documentación de la API |

---

## Resumen Ejecutivo

La entrega incluye un resumen ejecutivo con el conteo de hallazgos por nivel:

| Nivel   | Cantidad |
|---------|----------|
| Crítico | X        |
| Alto    | X        |
| Medio   | X        |
| Bajo    | X        |

Además, se incluye un párrafo que resume el estado general de la aplicación en lenguaje claro, sin tecnicismos innecesarios, orientado a que cualquier tomador de decisión pueda entender la situación.

---

## Costo y Formas de Pago

La inversión de referencia para este diagnóstico es de **{{investment_amount}} {{currency}}**.

La forma de pago propuesta es la siguiente:

- **{{payment_initial_pct}}% al inicio** del servicio, para dar apertura formal al diagnóstico y reservar la dedicación del equipo.
- **{{payment_final_pct}}% al final**, contra entrega del informe y la socialización de hallazgos.

> **Nota:** Este valor puede ajustarse si durante el levantamiento inicial se identifica un alcance significativamente mayor al estimado en esta propuesta.

---

## Cronograma

La duración estimada del diagnóstico es de **{{duration_label}}**.

### Distribución general

- **Día 1:** Levantamiento y lectura estructural de backend y frontend.
- **Días 2 a 4:** Evaluación por categorías, identificación de hallazgos y consolidación de evidencia.
- **Día 5:** Construcción del informe final, resumen ejecutivo y recomendaciones priorizadas.

---

## Alcance y Consideraciones

- El diagnóstico se realiza exclusivamente sobre los repositorios de código fuente (backend y frontend). No se evalúa infraestructura del servidor, procesos de despliegue ni sistemas de monitoreo.
- La escala de severidad es una herramienta de priorización, no un juicio sobre el equipo que construyó la aplicación.
- La clasificación de tamaño es orientativa y sirve como herramienta de dimensionamiento, no como un veredicto absoluto.
- Esta propuesta describe qué se evaluará, cómo se estructurará la entrega y qué tipo de valor puede esperar la empresa al contratar el diagnóstico.

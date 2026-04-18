# Propuesta de Diagnóstico Técnico — Aplicación Web

## Índice

- [Propósito](#propósito)
- [Escala de Severidad](#escala-de-severidad)
- [Radiografía de la Aplicación](#radiografía-de-la-aplicación)
  - [Métricas que se recopilan](#métricas-que-se-recopilan)
  - [Clasificación por Tamaño](#clasificación-por-tamaño)
- [Categorías que se evalúan en el diagnóstico](#categorías-que-se-evalúan-en-el-diagnóstico)
  - [1. Arquitectura y Estructura Interna](#1-arquitectura-y-estructura-interna)
  - [2. Calidad del Código](#2-calidad-del-código)
  - [3. Interfaz de Usuario y Experiencia](#3-interfaz-de-usuario-y-experiencia)
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
  - [14. Capacidades Funcionales](#14-capacidades-funcionales)
- [Estructura de los Hallazgos](#estructura-de-los-hallazgos)
- [Resumen Ejecutivo](#resumen-ejecutivo)
- [Estructura de la Entrega](#estructura-de-la-entrega)
  - [Radiografía en la entrega](#radiografía-en-la-entrega)
  - [Para cada categoría evaluada](#para-cada-categoría-evaluada)
    - [Lo que se encontró bien](#lo-que-se-encontró-bien)
    - [Hallazgos y oportunidades de mejora](#hallazgos-y-oportunidades-de-mejora)
    - [Recomendaciones](#recomendaciones)
  - [Roadmap sugerido](#roadmap-sugerido)
- [Alcance y Consideraciones](#alcance-y-consideraciones)

---

## Propósito

Esta propuesta presenta el alcance, el enfoque de evaluación y la estructura de entrega de un diagnóstico técnico integral para una aplicación web bajo arquitectura MVC, realizado a partir de la revisión de sus repositorios de código fuente (backend y frontend). El objetivo es identificar riesgos, fortalezas, oportunidades de mejora y recomendaciones priorizadas que sirvan como base para decisiones técnicas, operativas y de evolución del producto.

> **Alcance:** El diagnóstico se ejecuta exclusivamente sobre los repositorios de código. No se tiene acceso al servidor, al entorno de hosting, al pipeline de despliegue ni a los sistemas de monitoreo. Toda evaluación se basa en lo observable desde el código fuente, la configuración commiteada, las migraciones, las dependencias y la estructura de los repositorios.

---

## Escala de Severidad

| Nivel       | Criterio                                                                                                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Crítico** | Riesgo inmediato: vulnerabilidades explotables, pérdida de datos, fallos en producción, bloqueos al equipo. Requiere intervención urgente. |
| **Alto**    | Impacto significativo en calidad, rendimiento o capacidad de evolución. Debe planificarse a corto plazo (sprint actual o siguiente).       |
| **Medio**   | Genera deuda técnica, fricción o ineficiencias. Abordable a mediano plazo sin riesgo inmediato.                                            |
| **Bajo**    | Mejora deseable. Aporta valor incremental sin representar riesgo operativo.                                                                |

---

## Radiografía de la Aplicación

Como parte del diagnóstico, se levanta un inventario técnico que permite dimensionar la aplicación y entender su nivel de complejidad, madurez y alcance actual. Esta radiografía responde a la pregunta: **¿qué tenemos hoy?**

### Métricas que se recopilan

| Dimensión                           | Cómo se obtiene                                                                                          |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Stack tecnológico**               | Lenguaje(s), framework(s), versiones principales del backend y frontend                                  |
| **Entidades / modelos**             | Conteo de modelos del ORM o tablas definidas en migraciones                                              |
| **Migraciones**                     | Cantidad total de archivos de migración en el repositorio                                                |
| **Endpoints / rutas del backend**   | Conteo de rutas registradas (API + web) a partir del archivo de rutas                                    |
| **Pantallas / vistas del frontend** | Conteo de vistas o páginas principales definidas en el router del frontend                               |
| **Componentes del frontend**        | Conteo de componentes (archivos de componente en el directorio correspondiente)                          |
| **Integraciones externas**          | Servicios de terceros consumidos (pasarelas de pago, email, APIs externas, OAuth providers, etc.)        |
| **Módulos / dominios funcionales**  | Áreas de negocio identificables (autenticación, facturación, reportes, notificaciones, inventario, etc.) |
| **Líneas de código (aproximado)**   | Estimación general por repositorio, excluyendo dependencias y archivos generados                         |
| **Jobs / comandos en background**   | Conteo de jobs de cola, scheduled tasks, comandos artisan o scripts de procesamiento                     |
| **Archivos de configuración**       | Presencia de Dockerfiles, docker-compose, archivos de CI/CD, archivos de entorno (.env.example)          |

### Clasificación por Tamaño

| Dimensión                 | Pequeña | Mediana  | Grande |
| ------------------------- | ------- | -------- | ------ |
| Entidades / modelos       | < 15    | 15 – 50  | > 50   |
| Endpoints / rutas backend | < 30    | 30 – 100 | > 100  |
| Pantallas / vistas        | < 15    | 15 – 50  | > 50   |
| Componentes frontend      | < 20    | 20 – 80  | > 80   |
| Integraciones externas    | 0 – 2   | 3 – 7    | > 7    |
| Módulos funcionales       | 1 – 3   | 4 – 8    | > 8    |

> Los rangos coinciden con los de la propuesta comercial. El anexo de dimensionamiento presenta los valores medidos sobre el código y la clasificación resultante.

**Criterio de clasificación:** Se evalúa el panorama general. Si la mayoría de las dimensiones convergen en un rango, esa es la clasificación. Si hay dispersión (por ejemplo, pocas entidades pero muchos endpoints), se documenta la discrepancia y se clasifica por la tendencia dominante, dejando nota de la anomalía.

**Propósito de la clasificación:** Dimensionar el esfuerzo del diagnóstico, establecer expectativas realistas y servir como referencia para estructurar el alcance y valor del servicio.

---

## Categorías que se evalúan en el diagnóstico

---

### 1. Arquitectura y Estructura Interna

**Qué se evalúa:** La organización del código fuente, la separación de responsabilidades y la coherencia del diseño arquitectónico.

**Criterios de evaluación:**

- **Separación MVC real:** Verificar que el patrón Modelo-Vista-Controlador se respete en la práctica. Que los controladores no contengan lógica de negocio compleja, que los modelos no manejen presentación y que las vistas no ejecuten queries ni lógica de dominio.
- **Capas de servicio:** Evaluar si existe una capa de servicios o acciones que encapsule la lógica de negocio fuera de los controladores. Si no existe, identificar dónde está concentrada esa lógica.
- **Organización de módulos:** Revisar si la estructura de carpetas refleja dominios funcionales claros o si es un directorio plano donde todo convive sin criterio.
- **Acoplamiento entre componentes:** Medir qué tan dependientes son los módulos entre sí. ¿Se pueden modificar de forma independiente o un cambio en un módulo tiene efectos colaterales en otros?
- **Cohesión:** Verificar que cada clase, servicio o componente tenga una responsabilidad clara y única (Single Responsibility Principle).
- **Patrones de diseño:** Identificar qué patrones se utilizan (Repository, Observer, Strategy, Factory, etc.) y si su uso es consistente y justificado, o si hay mezcla arbitraria.
- **Separación frontend/backend:** Evaluar cómo se comunican la capa de presentación y el backend. ¿API REST bien definida? ¿Renderizado mixto server-side y client-side sin criterio claro?

---

### 2. Calidad del Código

**Qué se evalúa:** La legibilidad, consistencia y mantenibilidad del código fuente.

**Criterios de evaluación:**

- **Convenciones de nomenclatura:** Variables, funciones, clases, tablas y columnas siguen una convención consistente (camelCase, snake_case, PascalCase según el contexto).
- **Duplicación:** Identificar bloques de lógica repetida que deberían estar abstraídos en funciones, traits, mixins, composables o servicios compartidos.
- **Complejidad ciclomática:** Detectar funciones o métodos con excesivos niveles de anidación, condicionales encadenados o flujos difíciles de seguir.
- **Código muerto:** Archivos, funciones, rutas, componentes o migraciones que existen pero no se usan.
- **Manejo de errores:** Evaluar si los errores se capturan y manejan de forma consistente o si se silencian, se ignoran o se propagan sin control.
- **Herramientas de análisis estático:** Verificar si se usan linters, formatters o analizadores de código y si están integrados en el flujo de desarrollo.
- **Tamaño de archivos y métodos:** Identificar controladores, modelos, componentes o archivos de configuración excesivamente largos que concentran demasiada responsabilidad.
- **Consistencia de estilo:** Verificar si hay un estándar de codificación definido y si se aplica uniformemente en todo el proyecto.

---

### 3. Interfaz de Usuario y Experiencia

**Qué se evalúa:** La capa visual (capa de presentación), su coherencia, rendimiento percibido y sostenibilidad técnica.

**Criterios de evaluación:**

- **Coexistencia de tecnologías frontend:** Si la aplicación mezcla renderizado server-side (templates del backend) con componentes reactivos del frontend (SPA o híbrido), evaluar qué proporción existe de cada uno, si hay un plan de migración y qué tan sostenible es la convivencia.
- **Componentización:** Verificar si la interfaz está construida con componentes reutilizables o si las pantallas son bloques monolíticos con lógica, estilos y markup mezclados.
- **Gestión de estado:** Evaluar cómo se maneja el estado de la aplicación en el frontend. ¿Hay un store centralizado? ¿Se usa de forma consistente? ¿Hay estado duplicado entre componentes y store?
- **Rendimiento de carga (evaluable desde el código):** Peso estimado del bundle, uso de lazy loading, code splitting, carga dinámica de componentes. Presencia de assets sin optimizar (imágenes pesadas, librerías completas importadas cuando solo se usa una función).
- **Responsividad:** Verificar en el código que los layouts usen un sistema de grid o breakpoints consistente. Evaluar si los componentes contemplan adaptación a distintas resoluciones.
- **Accesibilidad básica:** Uso de atributos semánticos, roles ARIA, contraste de colores en las definiciones de estilos, navegación por teclado.
- **Manejo de estados de UI:** Cómo se representan los estados de carga (loading), error, vacío (empty state) y éxito en la interfaz. ¿Son consistentes?
- **Llamadas al backend desde el frontend:** Evaluar si las peticiones HTTP están centralizadas en un servicio/cliente o si cada componente hace fetch/axios de forma independiente y dispersa.

---

### 4. Base de Datos y Gestión de la Información

**Qué se evalúa:** El modelo de datos, la integridad, el rendimiento de consultas y las prácticas de gestión, desde lo observable en migraciones, modelos y queries del código.

**Criterios de evaluación:**

- **Modelo relacional:** Evaluar la normalización del esquema a partir de las migraciones. Identificar redundancias, tablas sin relaciones claras, campos que almacenan múltiples valores en texto plano (JSON embebido donde debería haber relaciones, CSV en campos de texto).
- **Integridad referencial:** Verificar que existan foreign keys, constraints (unique, not null, check) definidos en las migraciones.
- **Migraciones:** Evaluar si el historial de migraciones es limpio, si las migraciones son reversibles y si hay migraciones que modifican datos en lugar de solo estructura.
- **Seeders y datos de prueba:** Verificar si existen seeders funcionales para levantar ambientes de desarrollo y prueba con datos representativos.
- **Queries y rendimiento:** Identificar N+1 queries, consultas sin índices, full table scans, queries complejos embebidos en controladores o vistas.
- **Uso del ORM vs queries raw:** Evaluar el balance entre uso del ORM y queries crudos. ¿Se usa el ORM de forma eficiente (eager loading, scopes, relaciones)? ¿Los queries raw están justificados?
- **Soft deletes y auditoría:** Verificar si hay estrategia de borrado lógico, timestamps de creación/actualización y si se registra quién hizo qué cambio.
- **Volumen y crecimiento:** Identificar tablas que podrían crecer sin control (logs, eventos, historiales) según el diseño del esquema.

---

### 5. Seguridad

**Qué se evalúa:** La postura de seguridad de la aplicación desde lo observable en el código fuente.

**Criterios de evaluación:**

- **Autenticación:** Mecanismo implementado (session-based, token-based, OAuth). Fortaleza de las políticas de contraseña en el código. Soporte para MFA.
- **Autorización:** Verificar que exista un sistema de roles y permisos implementado en el backend (middleware, policies, gates) y no solo en el frontend (ocultar botones no es seguridad).
- **Protección de endpoints:** Verificar en las rutas que todas las rutas protegidas requieran autenticación y autorización. Buscar endpoints expuestos sin validación.
- **Validación de entradas:** Evaluar si toda la entrada del usuario se valida en el backend (no solo en frontend). Verificar protección contra SQL injection, XSS, mass assignment.
- **CSRF y CORS:** Verificar en la configuración que la protección CSRF esté activa y que la configuración CORS no use wildcards indiscriminados.
- **Gestión de secretos:** Evaluar si las credenciales, API keys y secretos están en variables de entorno o si hay valores hardcodeados en el código fuente o commiteados al repositorio.
- **Cifrado:** Verificar en la configuración si hay cifrado de campos sensibles y si se fuerza HTTPS.
- **Dependencias vulnerables:** Verificar si las dependencias (backend y frontend) tienen vulnerabilidades conocidas (CVEs) ejecutando auditoría sobre los lockfiles.
- **Headers de seguridad:** Verificar en la configuración la presencia de headers como Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security.
- **Rate limiting:** Evaluar si existe configuración de rate limiting en endpoints sensibles (login, reset password, APIs públicas).

---

### 6. Rendimiento

**Qué se evalúa:** Los posibles cuellos de botella y las oportunidades de optimización identificables desde el código fuente.

**Criterios de evaluación:**

- **Queries lentos (potenciales):** Identificar consultas que por su estructura serían lentas: sin índices, con joins innecesarios, sin paginación, con N+1, cargando relaciones completas cuando no se necesitan.
- **Caching:** Evaluar si se implementa caché a nivel de aplicación (query cache, response cache, fragment cache), caché de configuración y caché de rutas.
- **Carga de assets frontend:** Evaluar en la configuración del bundler: minificación, compresión, tree shaking, optimización de imágenes, code splitting.
- **Procesos en background:** Verificar si las operaciones pesadas (envío de emails, generación de reportes, procesamiento de archivos) se despachan a colas asíncronas o bloquean el request.
- **Paginación:** Evaluar si las listas y tablas paginan correctamente o si se cargan datasets completos en memoria.
- **Eager vs lazy loading:** Verificar si las relaciones del ORM se cargan de forma eficiente según el contexto.
- **Imports innecesarios:** Detectar librerías pesadas importadas completamente cuando solo se usa una fracción.

---

### 7. Escalabilidad

**Qué se evalúa:** Si las decisiones de diseño actuales permiten que la aplicación soporte crecimiento sin requerir reescritura.

**Criterios de evaluación:**

- **Estado en servidor:** Verificar en la configuración si las sesiones se almacenan en un store compartido (Redis, base de datos) o en el filesystem local. Si es filesystem local, la aplicación no puede escalar horizontalmente.
- **Almacenamiento de archivos:** Evaluar si los archivos subidos se guardan en disco local o si la configuración apunta a un servicio de almacenamiento distribuido.
- **Cola de trabajos:** Verificar si el sistema de colas está configurado para un driver escalable (Redis, base de datos, servicio de mensajería) o usa un driver local (sync).
- **Diseño del esquema de BD:** Evaluar si el esquema soportaría un crecimiento de 10x en volumen. Identificar tablas sin estrategia de archivado que crecerían sin límite.
- **Límites de terceros:** Identificar en el código las dependencias externas (APIs, servicios de email, pasarelas de pago) y si hay manejo de rate limits o quotas.
- **WebSockets y conexiones persistentes:** Si la app usa comunicación en tiempo real, evaluar la configuración del driver de broadcasting y su capacidad de escalar.
- **Hardcodes que limitan escala:** Identificar valores fijos en el código que asumen un solo servidor, un solo dominio, una sola instancia.

---

### 8. Pruebas y Criterios de Calidad

**Qué se evalúa:** La cobertura, los tipos y la madurez de las pruebas implementadas en los repositorios.

**Criterios de evaluación:**

- **Pruebas unitarias:** cobertura de funciones, métodos y clases de forma aislada; porcentaje de cobertura; cobertura de casos de éxito y de error; cobertura en modelos, servicios y utilidades.
- **Pruebas de contrato:** validación de la estructura de respuestas de la API (status codes, formato JSON, campos requeridos); contratos definidos entre frontend y backend; detección automática de cambios incompatibles en endpoints.
- **Pruebas de integración:** flujos que involucran base de datos real, permisos y side-effects (emails, registros relacionados); uso de base de datos de prueba vs. mocking total; validación de transacciones completas de negocio.
- **Pruebas con mocking y edge cases:** simulación de dependencias externas (APIs de terceros, pasarelas de pago, email); escenarios límite (entradas vacías, valores extremos, caracteres especiales, concurrencia); cobertura de caminos de error y no solo los caminos felices.
- **Pruebas de extremo a extremo (E2E):** flujos completos como los ejecutaría un usuario real; herramienta utilizada y estabilidad (flakiness); cobertura de los flujos críticos del negocio.
- **Pruebas de carga y rendimiento:** existencia de scripts o configuraciones de pruebas de carga; puntos de quiebre o benchmarks documentados.
- **Pruebas de seguridad y configuración:** escaneo de dependencias por vulnerabilidades conocidas (audit sobre lockfiles); configuraciones inseguras detectables (debug mode, credenciales expuestas, permisos excesivos).
- **Criterios transversales:** CI que ejecute las pruebas automáticamente (archivos de pipeline en el repo); política de cobertura mínima definida; estado de los tests existentes (mantenidos o rotos e ignorados).

---

### 9. Mantenibilidad y Evolución

**Qué se evalúa:** Qué tan preparada está la aplicación para recibir cambios, correcciones y nuevas funcionalidades de forma segura.

**Criterios de evaluación:**

- **Acoplamiento:** Medir qué tan dependientes son los módulos entre sí. ¿Se pueden modificar de forma independiente? ¿Un cambio en un módulo genera efectos en cascada en otros?
- **Principio Open/Closed:** ¿Se pueden agregar nuevas funcionalidades extendiendo el sistema sin modificar el código existente?
- **Configurabilidad:** ¿Los valores que pueden cambiar (umbrales, feature flags, parámetros de negocio) están externalizados o hardcodeados?
- **Deuda técnica documentada:** ¿Hay TODOs, FIXMEs o issues documentados en el código? ¿Se puede dimensionar la deuda técnica acumulada?
- **Facilidad de onboarding:** ¿Un desarrollador nuevo puede levantar el proyecto, entender la estructura y hacer su primer cambio en un tiempo razonable (horas, no semanas)?
- **Versionamiento:** ¿Se usa Git con una estrategia de branching clara? ¿Los commits son descriptivos? ¿Hay evidencia de code review (PRs)?
- **Migrations path:** ¿Las migraciones de base de datos se pueden ejecutar de forma incremental y reversible?

---

### 10. Confiabilidad y Tolerancia a Fallos

**Qué se evalúa:** La capacidad de la aplicación para manejar errores y mantener la consistencia de los datos.

**Criterios de evaluación:**

- **Transacciones y consistencia:** ¿Las operaciones críticas usan transacciones de base de datos? ¿Qué pasa si una operación falla a mitad de camino — el código deja datos en estado inconsistente?
- **Manejo global de excepciones:** ¿Existe un handler centralizado de excepciones? ¿Las excepciones se clasifican y responden de forma adecuada (4xx vs 5xx)?
- **Retry y circuit breakers:** ¿Las llamadas a servicios externos tienen mecanismos de reintento con backoff? ¿Hay circuit breakers configurados?
- **Manejo de fallos en colas:** ¿Los jobs fallidos se reintentan? ¿Hay configuración de máximo de intentos y dead letter queues?
- **Degradación elegante:** Cuando un componente no crítico falla (servicio de notificaciones, analytics), ¿el código permite que la aplicación siga funcionando o la excepción escala y rompe todo?
- **Validación defensiva:** ¿Se validan los datos en las capas correctas? ¿Hay null checks, type checks y validaciones de contrato donde son necesarias?

---

### 11. Integraciones y Comunicación entre Componentes

**Qué se evalúa:** Cómo se conectan las partes internas de la aplicación y las dependencias externas.

**Criterios de evaluación:**

- **Inventario de integraciones:** Documentar todas las APIs, servicios y sistemas externos con los que la aplicación se comunica, rastreados desde el código.
- **Abstracción:** ¿Las integraciones están encapsuladas detrás de interfaces/contratos o están acopladas directamente al código de negocio?
- **Manejo de fallos en integraciones:** ¿Qué pasa en el código cuando una API externa no responde? ¿Hay timeouts configurados? ¿Fallbacks?
- **Versionamiento de APIs:** Si la aplicación expone APIs, ¿hay versionamiento en las rutas? ¿Se manejan breaking changes?
- **Comunicación frontend-backend:** ¿API REST? ¿GraphQL? ¿Mixto? ¿Hay consistencia en los formatos de request/response? ¿Se validan las respuestas en el frontend?
- **Eventos y mensajería:** ¿Se usan eventos internos, broadcasting o mensajería asíncrona? ¿Los event listeners tienen efectos colaterales difíciles de rastrear?
- **Webhooks:** Si la app recibe webhooks, ¿se validan firmas en el código? ¿Se procesan de forma idempotente?

---

### 12. Vigencia Tecnológica

**Qué se evalúa:** El riesgo de obsolescencia y la salud del ecosistema tecnológico.

**Criterios de evaluación:**

- **Versión del lenguaje y framework:** ¿Se usa una versión con soporte activo (LTS)? ¿Cuánto tiempo queda de soporte? Verificar en los archivos de configuración y lockfiles.
- **Dependencias backend:** Evaluar el estado de los paquetes desde el lockfile. ¿Hay dependencias abandonadas, sin mantenimiento o con CVEs sin parchear?
- **Dependencias frontend:** Mismo análisis para las librerías del frontend. ¿Hay paquetes deprecados? ¿Conflictos de versiones?
- **Compatibilidad de upgrades:** ¿Qué tan complejo sería actualizar a la siguiente versión mayor del framework o del lenguaje? ¿Hay breaking changes identificados?
- **Ecosistema y comunidad:** ¿Las tecnologías elegidas tienen comunidad activa, documentación vigente y roadmap claro?
- **Talento disponible:** ¿Es factible encontrar desarrolladores con experiencia en el stack actual?

---

### 13. Documentación y Gestión del Conocimiento

**Qué se evalúa:** Qué tan transferible y accesible es el conocimiento sobre la aplicación.

**Criterios de evaluación:**

- **README y setup:** ¿El repositorio tiene instrucciones claras para levantar el proyecto desde cero? ¿Se indica qué dependencias se necesitan, cómo configurar el entorno y cómo ejecutar las pruebas?
- **Documentación de API:** ¿Los endpoints están documentados (OpenAPI/Swagger, Postman collections)? ¿La documentación se genera automáticamente o se mantiene manualmente?
- **Documentación arquitectónica:** ¿Existe algún documento que explique la estructura general del proyecto y sus decisiones de diseño?
- **Decisiones de diseño (ADRs):** ¿Se documentan las decisiones arquitectónicas importantes y sus razones?
- **Documentación de flujos de negocio:** ¿Los procesos críticos están documentados a nivel técnico?
- **Comentarios en código:** ¿Se documentan los "por qué" y no los "qué"? ¿Hay comentarios engañosos o desactualizados?
- **Concentración del conocimiento (bus factor):** A partir del historial de Git, ¿cuántas personas han contribuido activamente? ¿Hay áreas del código donde solo una persona ha hecho cambios?

---

### 14. Capacidades Funcionales

**Qué se evalúa:** Desde el código y la estructura, qué necesidades resuelve la aplicación y cómo lo hace.

**Criterios de evaluación:**

- **Mapa de módulos funcionales:** Identificar y catalogar los dominios funcionales que existen en la aplicación (autenticación, gestión de usuarios, pagos, reportes, notificaciones, etc.).
- **Delimitación de responsabilidades:** ¿Cada módulo tiene un propósito claro? ¿Hay módulos que mezclan dominios distintos?
- **Funcionalidad incompleta o abandonada:** Identificar features a medio construir, rutas definidas sin implementación, componentes sin uso, tablas sin datos.
- **Lógica de negocio dispersa:** ¿Las reglas de negocio están centralizadas en servicios o están repartidas entre controladores, modelos, middlewares, vistas y migraciones?
- **Workarounds y parches:** Identificar soluciones improvisadas — hardcodes, condicionales por cliente específico, bypasses de validación, flags manuales en base de datos.
- **Sobreingeniería vs subingeniería:** ¿Hay abstracciones excesivas para problemas simples? ¿O soluciones demasiado simples para problemas complejos que ya generan fricciones?
- **Flujos críticos identificables:** ¿Se pueden rastrear los flujos principales del negocio desde la ruta, pasando por el controlador, servicio, modelo y respuesta, de forma clara?

---

## Estructura de los Hallazgos

Cada hallazgo documentado dentro de la entrega sigue esta estructura:

```text
Categoría:       [Nombre de la categoría]
Hallazgo:        [Descripción concreta del problema o fortaleza]
Severidad:       [Crítico | Alto | Medio | Bajo]
Evidencia:       [Archivo, línea, query, endpoint, configuración concreta en el repositorio]
Impacto:         [Qué consecuencia tiene o podría tener]
Recomendación:   [Acción concreta sugerida]
```

---

## Resumen Ejecutivo

La entrega incluye un conteo de hallazgos por severidad, la clasificación de tamaño de la aplicación y un párrafo de síntesis sobre su estado general.

| Nivel   | Cantidad |
| ------- | -------- |
| Crítico | X        |
| Alto    | X        |
| Medio   | X        |
| Bajo    | X        |

---

## Estructura de la Entrega

### Radiografía en la entrega

Se presenta el inventario técnico recopilado y la clasificación de tamaño resultante, con el fin de contextualizar los hallazgos y recomendaciones. Es el mismo inventario descrito en la sección [Radiografía de la Aplicación](#radiografía-de-la-aplicación), materializado sobre los valores medidos para este proyecto.

### Para cada categoría evaluada

#### Lo que se encontró bien

Se destacan las prácticas, decisiones o implementaciones que funcionan correctamente y que vale la pena conservar.

#### Hallazgos y oportunidades de mejora

Cada hallazgo sigue la plantilla declarada en [Estructura de los Hallazgos](#estructura-de-los-hallazgos) (6 campos). La vista tabular para lectura rápida es:

| Categoría | Hallazgo | Severidad | Evidencia | Impacto | Recomendación |
| --------- | -------- | --------- | --------- | ------- | ------------- |
| ...       | ...      | ...       | ...       | ...     | ...           |

#### Recomendaciones

Cada recomendación se deriva del hallazgo que busca resolver y conserva su nivel de severidad. La recomendación ya aparece en la tabla anterior; esta sección recoge una vista consolidada cuando conviene separarla del detalle del hallazgo.

### Roadmap sugerido

Las recomendaciones se agrupan por prioridad en horizontes de acción para facilitar la toma de decisiones y la planeación técnica:

- **Inmediato (0-2 semanas):** Hallazgos críticos que representan riesgo activo.
- **Corto plazo (1-2 meses):** Hallazgos altos que impactan calidad y evolución.
- **Mediano plazo (3-6 meses):** Hallazgos medios que reducen deuda técnica.
- **Backlog:** Hallazgos bajos y mejoras incrementales.

---

## Alcance y Consideraciones

- Este documento es la **propuesta técnica (metodológica)** del diagnóstico. No incluye costo ni cronograma comercial — esos viven en la propuesta comercial. La medición previa que sustenta precio y cronograma vive en el anexo de dimensionamiento.
- El diagnóstico se ejecuta exclusivamente sobre los repositorios de código fuente (backend y frontend). No se evalúa infraestructura del servidor, procesos de despliegue en producción ni sistemas de monitoreo externos.
- Si en los repositorios existen archivos de configuración de CI/CD, Docker o monitoreo, se documentan como parte de la radiografía, pero no se valida su funcionamiento en un entorno real.
- Toda afirmación debe estar respaldada por evidencia concreta (archivos, líneas de código, configuraciones, lockfiles), no por opiniones generales.
- La escala de severidad es una herramienta de priorización, no un juicio sobre el equipo que construyó la aplicación.
- Esta propuesta describe qué se evaluará, cómo se estructurará la entrega y qué valor puede esperar la empresa al contratar el diagnóstico.

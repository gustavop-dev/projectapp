# Anexo — Dimensionamiento Preliminar para Definir Precio y Cronograma del Diagnóstico

## Índice

- [1. Propósito del anexo](#1-propósito-del-anexo)
- [2. Alcance de este dimensionamiento preliminar](#2-alcance-de-este-dimensionamiento-preliminar)
- [3. Qué se revisó en esta lectura preliminar](#3-qué-se-revisó-en-esta-lectura-preliminar)
- [4. Resumen ejecutivo](#4-resumen-ejecutivo)
- [5. Radiografía medida de la aplicación](#5-radiografía-medida-de-la-aplicación)
  - [5.1. Stack tecnológico](#51-stack-tecnológico)
  - [5.2. Inventario funcional y técnico](#52-inventario-funcional-y-técnico)
  - [5.3. Clasificación por tamaño](#53-clasificación-por-tamaño)
  - [5.4. Clasificación resultante](#54-clasificación-resultante)
- [6. Implicaciones sobre el cronograma del diagnóstico](#6-implicaciones-sobre-el-cronograma-del-diagnóstico)
- [7. Criterios usados para estimar el esfuerzo](#7-criterios-usados-para-estimar-el-esfuerzo)
- [8. Conclusión](#8-conclusión)
- [Fuente de la medición preliminar](#fuente-de-la-medición-preliminar)

---

## 1. Propósito del anexo

Este anexo tiene como propósito documentar el análisis preliminar realizado sobre la aplicación antes de ejecutar el diagnóstico formal. Su función es servir como base para dimensionar correctamente el servicio, estimar el nivel de esfuerzo requerido y sustentar decisiones relacionadas con el precio y el cronograma del diagnóstico.

En otras palabras, este documento no corresponde todavía al diagnóstico en sí mismo, sino a una evaluación previa de tamaño, complejidad y alcance, construida a partir de datos medidos directamente en el código fuente.

---

## 2. Alcance de este dimensionamiento preliminar

Este dimensionamiento preliminar se elaboró exclusivamente a partir de la revisión de los repositorios de código fuente disponibles, tanto de backend como de frontend. No contempla validaciones sobre infraestructura, servidores, despliegues, monitoreo, tráfico real, comportamiento en producción ni operación en entornos reales.

Su objetivo no es emitir hallazgos definitivos, sino entender qué tan grande, diversa y técnicamente exigente es la aplicación para estimar con mayor precisión el alcance del trabajo de diagnóstico posterior.

---

## 3. Qué se revisó en esta lectura preliminar

Para construir este dimensionamiento no se hizo una lectura superficial del proyecto, sino una revisión inicial orientada a identificar tamaño, alcance funcional y señales tempranas de complejidad técnica. En esta etapa se revisaron, entre otros, los siguientes elementos del proyecto:

| Elemento revisado          | Qué se observó                                                                  |
|----------------------------|---------------------------------------------------------------------------------|
| Stack tecnológico          | Composición tecnológica de backend y frontend                                   |
| Migraciones y modelos      | Estructura de datos disponible en el repositorio                                |
| Rutas del backend          | Distribución entre rutas públicas y protegidas                                  |
| Controladores              | Conexión real entre controladores y rutas definidas                             |
| Router del frontend        | Pantallas y secciones funcionales visibles                                      |
| Componentes de UI          | Estructura de componentes y herencia de plantilla                               |
| Módulos funcionales        | Dominios funcionales visibles desde rutas, controladores y vistas               |
| Madurez técnica            | Presencia de pruebas, CI/CD, Docker y otros elementos de soporte                |
| Señales de deuda técnica   | Código desconectado, piezas sin implementar y reutilización parcial de base previa |

Además de levantar métricas, esta lectura permite detectar observaciones concretas que evidencian que sí hubo revisión real del proyecto. Las observaciones identificadas se documentan en la sección de inventario más abajo.

---

## 4. Resumen ejecutivo

> Este resumen consolida el **dimensionamiento** de la aplicación, no los hallazgos del diagnóstico. El conteo de hallazgos por severidad aparece en la propuesta comercial, una vez ejecutado el diagnóstico.

Con base en la medición del código, la aplicación presenta una complejidad general **{{size_category_label}}**, con elementos que permiten dimensionar el esfuerzo esperado del diagnóstico de forma objetiva.

Desde la perspectiva de dimensionamiento, el resultado permite acotar el servicio en un tiempo razonable cuando se trabaja con una metodología clara.

---

## 5. Radiografía medida de la aplicación

### 5.1. Stack tecnológico

| Capa     | Tecnología               | Versión                  |
|----------|--------------------------|--------------------------|
| Backend  | {{stack_backend_name}}   | {{stack_backend_version}}|
| Frontend | {{stack_frontend_name}}  | {{stack_frontend_version}}|

### 5.2. Inventario funcional y técnico

#### Base de datos y modelos

| Métrica                | Valor                |
|------------------------|----------------------|
| Migraciones            | {{migrations_count}} |
| Entidades / modelos    | {{entities_count}}   |

#### Backend

| Métrica                                | Valor                       |
|----------------------------------------|-----------------------------|
| Rutas totales                          | {{routes_total}}            |
| Rutas públicas                         | {{routes_public}}           |
| Rutas protegidas                       | {{routes_protected}}        |
| Controladores                          | {{controllers_count}}       |
| Controladores no conectados a rutas    | {{controllers_disconnected}}|

#### Frontend

| Métrica                          | Valor                       |
|----------------------------------|-----------------------------|
| Rutas / vistas en el router      | {{frontend_routes_count}}   |
| Componentes                      | {{components_count}}        |

#### Módulos funcionales identificados

{{modules_list}}

#### Otros datos relevantes

| Métrica                          | Valor                       |
|----------------------------------|-----------------------------|
| Archivos de prueba               | {{test_files_count}}        |
| Cobertura de pruebas de negocio  | {{test_coverage_label}}     |
| Archivos de CI/CD                | {{ci_files_count}}          |
| Archivos Docker                  | {{docker_files_count}}      |
| Integraciones externas           | {{external_integrations}}   |

> La cobertura de pruebas de negocio refleja lo reportado por las herramientas configuradas en el repositorio; no implica que las pruebas se ejecuten de forma continua ni que validen comportamiento en entornos reales.

### 5.3. Clasificación por tamaño

Tabla de valores medidos contra los rangos de referencia. Los rangos varían por dimensión: consultar la tabla completa en la propuesta comercial o técnica.

| Dimensión                 | Valor medido               | Clasificación                  |
|---------------------------|----------------------------|--------------------------------|
| Entidades / modelos       | {{entities_count}}         | {{entities_size}}              |
| Endpoints / rutas backend | {{routes_total}}           | {{routes_size}}                |
| Pantallas / vistas        | {{frontend_routes_count}}  | {{frontend_routes_size}}       |
| Componentes frontend      | {{components_count}}       | {{components_size}}            |
| Integraciones externas    | {{external_integrations}}  | {{integrations_size}}          |
| Módulos funcionales       | {{modules_count}}          | {{modules_size}}               |

### 5.4. Clasificación resultante

La clasificación general resultante es **{{size_category_label}}**.

Esta conclusión se sustenta en que la mayoría de las dimensiones relevantes se concentran en ese rango. Cuando una dimensión cae en una categoría diferente, no necesariamente compensa o reduce el esfuerzo del análisis, ya que cada dimensión aporta una superficie distinta de revisión (arquitectura, calidad, seguridad, mantenibilidad, etc.).

---

## 6. Implicaciones sobre el cronograma del diagnóstico

El cronograma del diagnóstico debe contemplar no solo la lectura del código, sino también el tiempo necesario para interpretar correctamente la aplicación, distinguir funcionalidades reales de residuos técnicos, consolidar hallazgos y estructurar recomendaciones útiles para la empresa.

En esta aplicación, el tiempo del servicio estará influenciado por:

- La necesidad de revisar backend y frontend de forma correlacionada.
- La cantidad de módulos funcionales que requieren entendimiento contextual.
- La detección de piezas aparentemente inconclusas o no conectadas.
- La presencia o ausencia de pruebas automatizadas, que impacta la capacidad de confirmar rápidamente comportamientos esperados.
- La necesidad de convertir los hallazgos en una entrega ejecutiva, priorizada y comprensible para toma de decisiones.

---

## 7. Criterios usados para estimar el esfuerzo

Para estimar el nivel de esfuerzo del diagnóstico, en este anexo se consideraron los siguientes criterios:

- Cantidad de entidades y migraciones.
- Cantidad de rutas y endpoints del backend.
- Cantidad de pantallas y componentes del frontend.
- Diversidad de módulos funcionales.
- Presencia o ausencia de integraciones externas.
- Madurez de prácticas técnicas observables en el repositorio.
- Existencia de elementos abandonados, desconectados o heredados de implementaciones previas.
- Necesidad de revisar no solo volumen, sino complejidad funcional y riesgo implícito.

Estos criterios permiten construir una base objetiva para definir el precio y el cronograma del servicio, reduciendo la subjetividad comercial y dando trazabilidad a la propuesta económica.

---

## 8. Conclusión

Este anexo es un **documento de dimensionamiento previo** que justifica el precio y el cronograma del diagnóstico. Complementa a la propuesta comercial (alcance, costo y entregables) y a la propuesta técnica (metodología y criterios por categoría).

El análisis preliminar permite concluir que la aplicación requiere un diagnóstico formal con un alcance bien estructurado y una dedicación proporcional a su complejidad real. Este anexo cumple la función de justificar por qué el servicio debe valorarse y calendarizarse con criterios técnicos. No debe determinarse únicamente con base en una impresión general del sistema o en el número aparente de pantallas o tablas.

---

## Fuente de la medición preliminar

La información utilizada para construir este anexo proviene del levantamiento técnico medido directamente en el código y del inventario detallado de endpoints del backend.

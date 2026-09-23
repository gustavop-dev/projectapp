# Plantillas HTML de Linktree — Nivel 2

Especificación 1.0, implementada sobre la personalización básica del Linktree.

## Uso desde el panel

1. Abre **Linktrees → Editar → Apariencia → Plantilla HTML**. Guarda primero los datos del perfil.
2. Selecciona un ZIP, una carpeta o agrega archivos individuales. Son obligatorios `template.html` y `manifest.json`; `template.css` y `assets/` son opcionales.
3. **Subir y validar** crea una versión candidata. La publicación actual se conserva durante la validación.
4. Revisa errores/avisos, la vista previa aislada y las capturas a **320, 375 y 430 px**. Los errores impiden publicar.
5. En **Imágenes de la plantilla**, cambia o restablece las claves que el manifest declara editables; cada cambio se valida como una nueva versión.
6. **Publicar** activa el diseño en la misma URL pública. El historial conserva todas las publicaciones. Para recuperar una anterior, selecciónala y usa **Restaurar esta plantilla y validar**; luego publica.
7. **Restablecer tema básico** recupera los colores, logo y tipografía del editor. Conserva el historial.

La publicación es una instantánea de datos e imágenes: después de cambiar el perfil hay que **Validar con datos actuales → Publicar**. Así, un cambio de texto o imagen no elude las comprobaciones de accesibilidad de una versión aprobada. El panel lo indica junto a los controles.

La biblioteca se comparte **por cliente**, entre sus proyectos. El Linktree debe estar vinculado a un proyecto para compartir. Desactivar la compartición impide nuevas aplicaciones; las tarjetas que ya tienen una versión conservan esa publicación. Un proyecto de otro cliente nunca recibe esa plantilla en su biblioteca. El módulo mantiene el acceso de administración del panel (sesión + CSRF).

## Contrato para autores

- Mustache escapado: `name`, `role`, `bio`, `company`, `badge`, `footer_tagline`, `photo_url`, `logo_url`, `profile_url`, `initials`. Secciones normales/invertidas; sin HTML crudo, parciales, lambdas ni cambio de delimitadores.
- `primary_link`, `links` y `links.social`/`web`/`whatsapp`/`email`/`phone`/`file`. Cada enlace expone `label`, `url`, `icon`, `kind`, `index` (desde cero), `first`, `last`. Cuando se usa `primary_link`, `links` contiene los restantes; en otro caso incluye todos los enlaces activos con destino. Los botones de vCard/instalación se expresan mediante acciones.
- Enlaces: `<a data-link href="{{url}}">{{label}}</a>`. No se permiten destinos fijos. Las URLs del perfil se comprueban antes de renderizar.
- Acciones: `save-contact`, `install-pwa`, `share`, `whatsapp`, `email`, `copy`. `data-value` configura qué copiar. Un runtime exclusivo de la plataforma conecta las acciones y oculta las que no están disponibles.
- `data-icon` inserta un SVG Lucide local que hereda `currentColor`. Catálogo vendorizado 1.47.0 con licencia ISC; no se descarga JavaScript externo.
- Decorativas: `<img data-asset="clave">` y CSS `asset(clave)`. `alt: ""` produce imagen decorativa con `aria-hidden`. El servidor conserva alfa, limita los lados a 2000 px y entrega variantes 1x/2x/3x. Los SVG eliminan scripting, eventos, contenido extranjero y referencias externas.
- Fuentes de Google Fonts exclusivamente desde `fonts` (por ejemplo `Oswald:wght@600;700`). La plataforma genera el enlace CSS2; un fallo al cargar las fuentes bloquea la validación para no aprobar con métricas de otra tipografía.
- Slots `photo`/`logo`: presencia obligatoria si se declara, dimensiones mínimas, formatos y proporción aplicada mediante `aspect-ratio`/`object-fit`. El logo admite SVG sanitizado desde el panel.
- Límites: 4 MB de paquete descomprimido, 12 decorativas, 800 KB por decorativa, 200 KB por archivo de texto. ZIP sin cifrado, symlinks, rutas exteriores ni nombres duplicados.

El HTML/CSS prohibido **bloquea la carga** e informa archivo/línea. Resuelve la discrepancia de la especificación a favor de su tabla de errores bloqueantes; no se publica una plantilla mutilada silenciosamente. La sanitización de SVG sí conserva el dibujo permitido y muestra un aviso.

## Validación y seguridad

`html5lib` normaliza el árbol HTML; el dialecto Mustache escapa todos los valores y no evalúa código; `tinycss2` inspecciona tokens CSS, incluyendo escapes. Las reglas de CSS no permiten importaciones, fuentes externas, URLs externas, propiedades ejecutables ni animaciones de propiedades distintas de transform/opacity. Los paquetes originales y las capturas nunca se sirven desde MEDIA_URL.

Huey procesa una validación a la vez. Chromium usa un origen sintético sin sesión, intercepta todas las peticiones y sólo recibe los archivos ya normalizados desde almacenamiento privado y fuentes de los hosts exactos de Google. No puede consultar APIs internas ni URLs elegidas por la plantilla. Un fallo del motor deja la versión inválida; una candidata que lleva diez minutos pendiente puede reintentarse.

El navegador mide objetivos táctiles, overflow a 320 px, overlays fijos, cantidad y propiedades de animaciones, cambios por segundo, texto/botones animados continuamente y preferencia de movimiento reducido. Para contraste se muestrean fondos reales (incluidas texturas y degradados) detrás de las cajas de texto, con umbral 4.5:1 o 3:1 en encabezados ≥24 px. Texto con mezcla/filtros o colores no RGB que no pueda certificarse produce error, nunca un aprobado inventado. Se limitan el DOM y el alto de página a 2000 elementos y 12000 px.

La página publicada tiene CSP por respuesta con nonce exclusivo para el runtime de la plataforma, sin eventos inline, bases, formularios ni objetos. Las vistas previas tienen CSP `sandbox`, `script-src 'none'` y un iframe sin permisos. Las imágenes privadas de esas vistas llevan una firma de una hora limitada a su versión. Las capturas requieren sesión de administrador.

Los clics se agregan por versión/enlace/día sin IPs ni identificadores de visitante. Sólo se aceptan claves de enlaces publicados y se limita la tasa por origen. El envío comienza antes de navegar y usa `keepalive`; un fallo analítico no impide abrir el destino.

## Despliegue y operación

1. Instalar `backend/requirements.txt` en el entorno del backend.
2. Instalar Chromium **con el usuario del servicio Huey**: `python -m playwright install --with-deps chromium`. El binario y su caché deben quedar accesibles para ese usuario. Repetir tras actualizar Playwright. El CI instala el navegador sólo en el shard con las pruebas visuales.
3. Aplicar la migración aditiva `0253_linktree_html_templates` mediante el procedimiento de deploy. Nunca se ejecuta `migrate` desde un worktree conectado a producción.
4. Reiniciar Huey y el servidor mediante el despliegue normal. Mantener `PRIVATE_MEDIA_ROOT` en backups junto con la base de datos.
5. El worker de validación necesita memoria para Chromium; comprobar el presupuesto real del servicio antes de habilitar cargas en producción (el límite histórico de 350 MB debe contrastarse con una validación representativa). Las consultas públicas no arrancan Chromium.

No se cambian recursos del servidor ni se despliega desde esta sesión. Las plantillas, versiones y contadores quedan explícitamente excluidos del MCP: el Nivel 3 requiere un contrato separado. Los datos de demostración generan candidatas que exigen validación real antes de publicar, sin aprobaciones simuladas.

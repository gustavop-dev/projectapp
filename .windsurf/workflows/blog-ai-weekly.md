---
description: Weekly AI blog post creation — search news sources, summarize, and publish
---

# Blog AI Weekly — Crear artículo semanal de IA

Workflow para crear un artículo de blog cada ~7 días basado en noticias relevantes de inteligencia artificial.

---

## Paso 1 — Buscar noticias de IA en fuentes top

Usar la herramienta `search_web` para buscar noticias recientes y relevantes de IA en las siguientes **10 fuentes principales**:

| # | Fuente | Dominio |
|---|--------|---------|
| 1 | OpenAI Blog | `openai.com/blog` |
| 2 | Google AI Blog | `blog.google/technology/ai` |
| 3 | Meta AI Blog | `ai.meta.com/blog` |
| 4 | Microsoft AI Blog | `blogs.microsoft.com/ai` |
| 5 | Hugging Face Blog | `huggingface.co/blog` |
| 6 | TechCrunch AI | `techcrunch.com` (sección AI) |
| 7 | The Verge AI | `theverge.com` (sección AI) |
| 8 | arXiv Trending | `arxiv.org` (trending AI papers) |
| 9 | VentureBeat AI | `venturebeat.com/ai` |
| 10 | Ars Technica AI | `arstechnica.com` (sección AI) |

Ejecuta búsquedas como:
- `"latest AI news this week"` con dominio prioritario de cada fuente
- `"artificial intelligence breakthroughs 2025"` para captar tendencias

Recopila al menos **5-8 noticias relevantes** con título, resumen breve y URL fuente.

## Paso 2 — Seleccionar tema y presentar al usuario

De los resultados del paso 1:

1. Identificar el tema más relevante, trending o impactante de la semana.
2. Si hay varios temas fuertes, presentar un **top 3** al usuario con una línea de contexto cada uno.
3. Usar la herramienta `ask_user_question` para que el usuario elija el tema.
4. El usuario puede también proponer un tema diferente.

## Paso 3 — Redactar el artículo

Una vez seleccionado el tema, redactar el artículo en **español** con la siguiente estructura:

### Título
- Atractivo, SEO-friendly, máximo 80 caracteres.
- Ejemplo: "GPT-5 y el futuro de la IA generativa: lo que sabemos"

### Excerpt (resumen)
- 1-2 oraciones que resuman el artículo para las tarjetas del listado.
- Máximo 200 caracteres.

### Contenido (HTML)
Estructura del contenido con etiquetas HTML:
```html
<h2>Título principal del tema</h2>
<p>Introducción y contexto de la noticia...</p>

<h3>Subtema 1</h3>
<p>Desarrollo del punto...</p>

<h3>Subtema 2</h3>
<p>Análisis y por qué importa...</p>

<h3>Impacto y perspectiva</h3>
<p>Conclusión breve y visión a futuro...</p>
```

### Reglas de redacción
- Tono profesional pero accesible, dirigido a audiencia tech-savvy.
- No copiar/pegar texto de las fuentes — siempre resumir y aportar análisis.
- Extensión: 400-800 palabras.
- Usar `<ul>`, `<ol>`, `<strong>`, `<blockquote>` cuando sea apropiado.
- No incluir imágenes embebidas dentro del HTML del contenido.

### Sources (fuentes)
Preparar un array JSON con las fuentes consultadas:
```json
[
  {"name": "OpenAI Blog", "url": "https://openai.com/blog/..."},
  {"name": "TechCrunch", "url": "https://techcrunch.com/..."}
]
```
Incluir **todas** las fuentes que se usaron para investigar el tema.

## Paso 4 — Imagen de portada

Preguntar al usuario con `ask_user_question`:

- **Opción A**: "Proporcionar una URL de imagen" — El usuario pega una URL.
- **Opción B**: "Generar descripción para IA" — Cascade genera un prompt descriptivo que el usuario puede usar en un generador de imágenes (DALL-E, Midjourney, etc.).
- **Opción C**: "Sin imagen por ahora" — Se crea el post sin cover_image, se puede agregar después.

## Paso 5 — Crear el blog post

Presentar al usuario un resumen del artículo antes de crearlo:
- Título
- Excerpt
- Número de palabras del contenido
- Fuentes listadas
- Imagen (si la hay)

Si el usuario aprueba, crear el post ejecutando el siguiente comando contra el backend Django:

```bash
source /home/ryzepeck/webapps/projectapp/backend/venv/bin/activate && python /home/ryzepeck/webapps/projectapp/backend/manage.py shell -c "
from content.models import BlogPost
from django.utils import timezone

post = BlogPost.objects.create(
    title='TITULO_AQUI',
    excerpt='EXCERPT_AQUI',
    content='''CONTENIDO_HTML_AQUI''',
    sources=SOURCES_JSON_AQUI,
    cover_image='URL_IMAGEN_O_VACIO',
    is_published=True,
    published_at=timezone.now(),
)
print(f'Blog post created: {post.title} (slug: {post.slug}, id: {post.id})')
"
```

Alternativamente, si el servidor Django de desarrollo está corriendo, se puede usar `curl` contra la API:
```bash
curl -X POST http://127.0.0.1:8000/api/blog/admin/create/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=...; csrftoken=..." \
  -H "X-CSRFToken: ..." \
  -d '{"title": "...", "excerpt": "...", "content": "...", "sources": [...], "is_published": true}'
```

El método con `manage.py shell` es más confiable y no requiere sesión de admin activa.

// turbo
## Paso 6 — Verificar

Verificar que el post se creó correctamente:

```bash
source /home/ryzepeck/webapps/projectapp/backend/venv/bin/activate && python /home/ryzepeck/webapps/projectapp/backend/manage.py shell -c "
from content.models import BlogPost
post = BlogPost.objects.filter(is_published=True).first()
print(f'Latest post: {post.title}')
print(f'Slug: {post.slug}')
print(f'Published: {post.published_at}')
print(f'Sources: {len(post.sources)} fuentes')
print(f'URL: /blog/{post.slug}')
"
```

Si hay un servidor de desarrollo corriendo, abrir el browser preview para verificar visualmente.

---

## Notas

- Este workflow está diseñado para ejecutarse **manualmente** cada ~7 días.
- El usuario puede personalizar las fuentes editando la tabla del Paso 1.
- Si se necesitan fuentes adicionales, simplemente agrégalas a la tabla.
- El contenido siempre debe ser original (resumido y analizado), nunca copiado.
- Las fuentes se muestran al final de cada artículo en la vista pública del blog.
- Los posts se crean como `is_published=True` por defecto. Si el usuario quiere revisar antes, cambia a `False`.

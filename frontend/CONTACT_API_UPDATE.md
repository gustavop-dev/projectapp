# Actualización API de Contacto

## Nuevos Campos en el Modelo Contact

Se agregaron dos nuevos campos al modelo de contacto:

### 1. `phone_number` (opcional)
- **Tipo**: String
- **Máximo**: 20 caracteres
- **Requerido**: No (opcional)

### 2. `budget` (opcional)
- **Tipo**: String
- **Opciones disponibles**:
  - `500-5K`
  - `5-10K`
  - `10-20K`
  - `20-30K`
  - `>30K`
- **Requerido**: No (opcional)

## Endpoint

```
POST /api/contact/
```

## Request Body Actualizado

```json
{
  "email": "user@example.com",
  "phone_number": "+1234567890",
  "subject": "Consulta sobre desarrollo web",
  "message": "Necesito un sitio web corporativo...",
  "budget": "5-10K"
}
```

### Campos Requeridos
- `email` ✅
- `subject` ✅
- `message` ✅

### Campos Opcionales
- `phone_number` (puede omitirse o enviarse como `null`)
- `budget` (puede omitirse o enviarse como `null`)

## Ejemplo de Implementación (Vue 3)

```javascript
// En tu componente Contact.vue
const form = ref({
  fullName: '',      // Este campo no se envía al backend
  email: '',
  phone_number: '',  // Nuevo campo
  subject: '',       // Usar fullName como subject si aplica
  message: '',
  budget: ''         // Nuevo campo
})

const handleSubmit = async () => {
  try {
    const payload = {
      email: form.value.email,
      phone_number: form.value.phone_number || null,
      subject: form.value.subject || form.value.fullName,
      message: form.value.message,
      budget: form.value.budget || null
    }
    
    const response = await fetch('http://localhost:8000/api/contact/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
    
    if (response.ok) {
      console.log('Mensaje enviado exitosamente')
      // Limpiar formulario o mostrar mensaje de éxito
    }
  } catch (error) {
    console.error('Error al enviar mensaje:', error)
  }
}
```

## Validaciones Backend

El serializer acepta automáticamente todos los campos (usa `fields = '__all__'`).

- Los campos opcionales (`phone_number` y `budget`) pueden ser `null` o string vacío
- El campo `budget` solo acepta las opciones predefinidas
- Si envías un valor de `budget` que no está en las opciones, recibirás un error 400

## Response Example

### Success (201 Created)
```json
{
  "id": 1,
  "email": "user@example.com",
  "phone_number": "+1234567890",
  "subject": "Consulta sobre desarrollo web",
  "message": "Necesito un sitio web corporativo...",
  "budget": "5-10K"
}
```

### Error (400 Bad Request)
```json
{
  "budget": [
    "\"15K\" is not a valid choice."
  ]
}
```

## Notas Adicionales

- Se envía una notificación por WhatsApp cuando se recibe un nuevo contacto
- La notificación incluye los nuevos campos `phone_number` y `budget`
- Si `phone_number` o `budget` están vacíos, se muestra "No proporcionado" / "No especificado" en la notificación

<script setup>
/**
 * Branded email preview card — the exact markup the client receives.
 *
 * Shared verbatim by the Proposals and Diagnostics email composers. Styling is
 * intentionally inline (email clients require inline styles), so this is a pure
 * presentational render of the composed message.
 */
defineProps({
  greeting: { type: String, default: '' },
  // [{ id, text }]
  sections: { type: Array, default: () => [] },
  footer: { type: String, default: '' },
  // [{ name }]
  attachments: { type: Array, default: () => [] },
})
</script>

<template>
  <div style="background-color:#f3f4f6;border-radius:12px;padding:24px 16px;font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;">
    <div style="background-color:#ffffff;border-radius:16px;overflow:hidden;max-width:560px;margin:0 auto;">
      <!-- Header -->
      <div style="background-color:#059669;padding:28px 32px;text-align:center;">
        <div style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.02em;">
          Project App.
        </div>
        <div style="margin:6px 0 0;color:#d1fae5;font-size:13px;font-weight:400;">
          Transformación Digital
        </div>
      </div>
      <!-- Greeting -->
      <div style="padding:32px 32px 20px;">
        <div style="margin:0;color:#1f2937;font-size:20px;font-weight:600;white-space:pre-wrap;">{{ greeting || '(sin saludo)' }}</div>
      </div>
      <!-- Body sections -->
      <div v-for="section in sections" :key="section.id" style="padding:0 32px 14px;">
        <div style="margin:0;color:#4b5563;font-size:15px;line-height:1.6;white-space:pre-wrap;">{{ section.text || '(sección vacía)' }}</div>
      </div>
      <!-- Attachment names -->
      <div v-if="attachments.length" style="padding:8px 32px 20px;">
        <div style="background-color:#f0fdf4;border-radius:12px;border:1px solid #bbf7d0;padding:16px 20px;">
          <div style="margin:0 0 10px;color:#059669;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
            Archivos adjuntos
          </div>
          <div v-for="(file, idx) in attachments" :key="idx"
            :style="{ margin: idx === 0 ? '0' : '6px 0 0', color: '#1f2937', fontSize: '13px' }">
            &#128206; {{ file.name }}
          </div>
        </div>
      </div>
      <!-- Footer text -->
      <div v-if="footer" style="padding:0 32px 20px;">
        <div style="margin:0;color:#4b5563;font-size:14px;line-height:1.6;white-space:pre-wrap;">{{ footer }}</div>
      </div>
      <!-- Divider -->
      <div style="padding:0 32px;">
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:0;" />
      </div>
      <!-- Sign-off -->
      <div style="padding:20px 32px 28px;text-align:center;">
        <div style="margin:0 0 6px;color:#6b7280;font-size:13px;line-height:1.5;">
          ¿Dudas? Respondé este correo o escríbenos por
          <span style="color:#059669;font-weight:600;">WhatsApp</span>
        </div>
        <div style="margin:12px 0 0;color:#9ca3af;font-size:11px;">
          © 2026 ProjectApp.co | Bogotá, Colombia
        </div>
      </div>
    </div>
  </div>
</template>

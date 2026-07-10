<script setup>
/**
 * Branded email preview card — faithful replica of the HTML the client
 * actually receives (backend/content/templates/emails/branded_email.html).
 *
 * Shared by the Emails module and the Proposals/Diagnostics composers.
 * Styling is intentionally inline with the template's own hex values (email
 * clients require inline styles); keep this file in sync with
 * branded_email.html when the template design changes.
 */
defineProps({
  greeting: { type: String, default: '' },
  // [{ id, text }]
  sections: { type: Array, default: () => [] },
  footer: { type: String, default: '' },
  // [{ name }]
  attachments: { type: Array, default: () => [] },
  // Defaults mirror EMAIL_SIGNATURES[EMAIL_DEFAULT_SIGNER] in settings.py.
  signatureName: { type: String, default: 'Vanessa Rodríguez' },
  signatureRole: { type: String, default: 'Asistente Comercial · ProjectApp.' },
})
</script>

<template>
  <div style="background:#f4f1ea;border-radius:12px;padding:32px 16px 24px;font-family:Ubuntu,Helvetica,Arial,sans-serif;">
    <div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #ece8db;border-radius:20px;overflow:hidden;">
      <!-- Header: wordmark + eyebrow -->
      <div style="display:flex;align-items:center;justify-content:space-between;padding:28px 40px 24px;">
        <div style="font-weight:700;font-size:18px;line-height:20px;color:#001713;letter-spacing:-0.2px;">
          Project<br>App.
        </div>
        <div style="font-weight:500;font-size:11px;line-height:14px;letter-spacing:2px;color:#809490;text-transform:uppercase;">
          Equipo · Proyecto
        </div>
      </div>
      <div style="margin:0 40px;height:1px;background:#ece8db;" />

      <!-- Pill + greeting -->
      <div style="padding:40px 40px 8px;">
        <span style="display:inline-block;background:#F0FF3D;border-radius:999px;padding:8px 14px;font-weight:500;font-size:11px;line-height:14px;letter-spacing:1.8px;color:#001713;text-transform:uppercase;margin-bottom:24px;">
          ◆&nbsp;&nbsp;Mensaje del equipo
        </span>
        <div style="font-weight:300;font-size:42px;line-height:48px;letter-spacing:-0.8px;color:#001713;white-space:pre-wrap;">{{ greeting || 'Hola' }}<span style="color:#FF4D6A;">.</span></div>
      </div>

      <!-- Body sections -->
      <div style="padding:24px 40px 0;">
        <p
          v-for="section in sections"
          :key="section.id"
          style="margin:14px 0 0;font-weight:300;font-size:16px;line-height:26px;color:#001713;white-space:pre-wrap;"
        >{{ section.text || '(sección vacía)' }}</p>
      </div>

      <!-- Attachment names -->
      <div v-if="attachments.length" style="padding:32px 40px 0;">
        <div style="background:#faf7ee;border:1px solid #ece8db;border-radius:14px;padding:8px 24px;">
          <div
            v-for="(file, idx) in attachments"
            :key="idx"
            :style="{
              display: 'flex',
              gap: '12px',
              padding: '14px 0',
              borderBottom: idx < attachments.length - 1 ? '1px solid #ece8db' : 'none',
            }"
          >
            <span style="font-weight:500;font-size:14px;color:#001713;">▤</span>
            <span style="font-weight:500;font-size:14px;line-height:20px;color:#001713;">{{ file.name }}</span>
          </div>
        </div>
      </div>

      <!-- Footer text -->
      <div v-if="footer" style="padding:32px 40px 0;">
        <p style="margin:0;font-weight:300;font-size:13px;line-height:20px;color:#5a6b67;white-space:pre-wrap;">{{ footer }}</p>
      </div>

      <!-- Reply hint -->
      <div style="padding:32px 40px 12px;text-align:center;font-weight:300;font-size:12px;line-height:18px;color:#5a6b67;">
        Cualquier cosa, respóndenos directo a este correo.
      </div>

      <!-- Signature -->
      <div style="margin:0 40px 36px;padding-top:24px;border-top:1px solid #ece8db;">
        <div style="font-weight:500;font-size:14px;line-height:20px;color:#001713;">{{ signatureName }}</div>
        <div style="font-weight:300;font-size:13px;line-height:20px;color:#5a6b67;">{{ signatureRole }}</div>
      </div>

      <!-- Dark contact footer -->
      <div style="background:#001713;padding:28px 40px;display:flex;flex-wrap:wrap;gap:16px 8px;">
        <div style="flex:1;min-width:120px;">
          <div style="font-weight:500;font-size:10px;line-height:14px;letter-spacing:1.5px;color:#809490;text-transform:uppercase;margin-bottom:6px;">Web</div>
          <div style="font-weight:300;font-size:14px;line-height:20px;color:#e6efef;">projectapp.co</div>
        </div>
        <div style="flex:1;min-width:150px;">
          <div style="font-weight:500;font-size:10px;line-height:14px;letter-spacing:1.5px;color:#809490;text-transform:uppercase;margin-bottom:6px;">Email</div>
          <div style="font-weight:300;font-size:14px;line-height:20px;color:#e6efef;">team@projectapp.co</div>
        </div>
        <div style="flex:1;min-width:130px;">
          <div style="font-weight:500;font-size:10px;line-height:14px;letter-spacing:1.5px;color:#809490;text-transform:uppercase;margin-bottom:6px;">WhatsApp</div>
          <div style="font-weight:300;font-size:14px;line-height:20px;color:#e6efef;">+57 323 812 2373</div>
        </div>
      </div>
    </div>

    <!-- Below-card social + copyright -->
    <div style="max-width:600px;margin:0 auto;text-align:center;padding:28px 40px 0;font-weight:300;font-size:12px;color:#7a8e8a;">
      <span style="padding:0 10px;">Instagram</span>
      <span style="color:#d9d3c0;">·</span>
      <span style="padding:0 10px;">Facebook</span>
      <span style="color:#d9d3c0;">·</span>
      <span style="padding:0 10px;">WhatsApp</span>
    </div>
    <div style="max-width:600px;margin:0 auto;text-align:center;padding:8px 40px 0;font-weight:300;font-size:11px;line-height:18px;color:#7a8e8a;">
      © 2026 ProjectApp · Desarrollo de software a la medida · Bogotá, Colombia
    </div>
  </div>
</template>

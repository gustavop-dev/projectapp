function (data) {
  'use strict';
  const profile = data.profile;
  let installPrompt = null;
  const installButtons = [...document.querySelectorAll('[data-action="install-pwa"]')];
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt = event;
    if (profile.pwa_enabled) installButtons.forEach((button) => { button.hidden = false; });
  });
  const iosInstall = /iPad|iPhone|iPod/.test(navigator.userAgent) && !navigator.standalone && !matchMedia('(display-mode: standalone)').matches;
  if (profile.pwa_enabled && iosInstall) installButtons.forEach((button) => { button.hidden = false; });
  if (profile.pwa_enabled && 'serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js', { scope: '/', updateViaCache: 'none' }).catch(() => {});
  const status = document.createElement('p');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  document.body.append(status);
  const say = (text) => { status.textContent = text; };
  const copy = async (value) => {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      const field = document.createElement('textarea');
      field.value = value;
      document.body.append(field);
      field.select();
      const copied = document.execCommand('copy');
      field.remove();
      if (!copied) throw new Error('copy');
    }
    say('Enlace copiado.');
  };
  const escapeVcard = (value) => String(value || '').replace(/\\/g, '\\\\').replace(/\r?\n/g, '\\n').replace(/;/g, '\\;').replace(/,/g, '\\,');
  const download = () => {
    const c = profile.contact;
    const lines = ['BEGIN:VCARD', 'VERSION:3.0',
      `N:${escapeVcard(c.last_name)};${escapeVcard(c.first_name || profile.name)};;;`,
      `FN:${escapeVcard(profile.name)}`, `ORG:${escapeVcard(c.org)}`, `TITLE:${escapeVcard(profile.role)}`,
      `EMAIL;TYPE=WORK:${escapeVcard(c.email)}`, `TEL;TYPE=CELL:${escapeVcard(c.tel)}`,
      `URL:${escapeVcard(c.url || profile.profile_url)}`, 'END:VCARD'];
    const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/vcard;charset=utf-8' }));
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = 'contacto.vcf'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };
  const record = (link) => {
    const payload = JSON.stringify({ key: link.dataset.linkKey });
    // Start delivery before native navigation; keepalive survives leaving the page.
    fetch(data.click_url, { method: 'POST', body: payload, headers: { 'Content-Type': 'application/json' }, keepalive: true, credentials: 'omit' }).catch(() => {});
  };
  document.addEventListener('click', async (event) => {
    const element = event.target.closest('[data-action],a[data-link]');
    if (!element) return;
    if (element.matches('a[data-link]')) record(element);
    const action = element.dataset.action;
    if (!action) return;
    event.preventDefault();
    try {
      if (action === 'save-contact') download();
      if (action === 'whatsapp') window.top.location.href = `https://wa.me/${profile.contact.tel.replace(/\D/g, '')}`;
      if (action === 'email') window.top.location.href = `mailto:${encodeURIComponent(profile.contact.email)}`;
      if (action === 'copy') await copy(element.dataset.value || profile.profile_url);
      if (action === 'share') {
        if (navigator.share) await navigator.share({ title: profile.name, url: profile.profile_url });
        else await copy(profile.profile_url);
      }
      if (action === 'install-pwa' && iosInstall) say('Abre Compartir en Safari y elige Añadir a la pantalla de inicio.');
      if (action === 'install-pwa' && installPrompt) {
        await installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null;
        installButtons.forEach((button) => { button.hidden = true; });
      }
    } catch (error) {
      if (error.name !== 'AbortError') say('No se pudo completar la acción. Inténtalo de nuevo.');
    }
  });
  document.addEventListener('auxclick', (event) => {
    const link = event.target.closest('a[data-link]');
    if (event.button === 1 && link) record(link);
  });
}

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const runtimeSource = fs.readFileSync(
  path.resolve(__dirname, '../../../backend/content/services/linktree_templates/runtime.js'),
  'utf8',
);

const profile = (overrides = {}) => ({
  name: 'Ana López',
  role: 'Directora',
  profile_url: 'https://cards.example/ana',
  pwa_enabled: false,
  contact: {
    first_name: 'Ana',
    last_name: 'López',
    org: 'ProjectApp',
    email: 'ana@example.com',
    tel: '+57 300 123 4567',
    url: 'https://ana.example.com',
  },
  ...overrides,
});

const settle = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

const runtime = ({ html, profileData = profile(), clipboard = jest.fn().mockResolvedValue(undefined) } = {}) => {
  const runtimeDocument = document.implementation.createHTMLDocument('Linktree runtime');
  runtimeDocument.body.innerHTML = html || '';
  const windowListeners = {};
  const runtimeWindow = {
    addEventListener: (type, listener) => { windowListeners[type] = listener; },
    top: { location: { href: '' } },
  };
  const fetch = jest.fn().mockResolvedValue({ ok: true });
  const createObjectURL = jest.fn().mockReturnValue('blob:contact');
  const revokeObjectURL = jest.fn();
  let blob;
  class CapturedBlob {
    constructor(parts, options) {
      blob = { text: parts.join(''), type: options.type };
    }
  }
  const runtimeNavigator = { clipboard: { writeText: clipboard }, userAgent: '', standalone: false };
  jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  vm.runInNewContext(`(${runtimeSource})(data)`, {
    Blob: CapturedBlob,
    URL: { createObjectURL, revokeObjectURL },
    data: { profile: profileData, click_url: '/api/link-clicks/' },
    document: runtimeDocument,
    fetch,
    matchMedia: jest.fn().mockReturnValue({ matches: false }),
    navigator: runtimeNavigator,
    setTimeout: jest.fn(),
    window: runtimeWindow,
  }, { filename: 'linktree-template-runtime.js' });
  const click = (element) => element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  return { beforeInstallPrompt: (event) => windowListeners.beforeinstallprompt(event), blob: () => blob, clipboard, click, createObjectURL, document: runtimeDocument, fetch };
};

afterEach(() => {
  jest.restoreAllMocks();
});

test('shares through the clipboard and confirms the copied profile URL when Web Share is unavailable', async () => {
  // Falla si compartir deja de copiar el enlace en navegadores sin Web Share.
  const harness = runtime({ html: '<button data-action="share">Compartir</button>' });
  const button = harness.document.querySelector('[data-action="share"]');

  harness.click(button);
  await settle();

  expect(harness.clipboard).toHaveBeenCalledWith('https://cards.example/ana');
  expect(harness.document.querySelector('[role="status"]').textContent).toBe('Enlace copiado.');
});

test('reports a recoverable share error when the clipboard fails for a non-abort reason', async () => {
  // Falla si un rechazo del portapapeles distinto de AbortError queda silencioso para la persona visitante.
  const harness = runtime({
    html: '<button data-action="share">Compartir</button>',
    clipboard: jest.fn().mockRejectedValue(new Error('permission denied')),
  });
  const button = harness.document.querySelector('[data-action="share"]');

  harness.click(button);
  await settle();

  expect(harness.clipboard).toHaveBeenCalledWith('https://cards.example/ana');
  expect(harness.document.querySelector('[role="status"]').textContent).toBe('No se pudo completar la acción. Inténtalo de nuevo.');
});

test('downloads a vCard with escaped CRLF and semicolon contact fields', () => {
  // Falla si una nota de contacto rompe el formato vCard o altera los campos entregados al teléfono.
  const harness = runtime({
    html: '<button data-action="save-contact">Guardar contacto</button>',
    profileData: profile({
      name: 'Ana, López',
      role: 'Dirección; Comercial',
      contact: {
        first_name: 'Ana\r\nMarta',
        last_name: 'López; Soto',
        org: 'ProjectApp\r\nColombia',
        email: 'ana@example.com',
        tel: '+57 300 123 4567',
        url: 'https://ana.example.com',
      },
    }),
  });
  const button = harness.document.querySelector('[data-action="save-contact"]');

  harness.click(button);

  expect(harness.blob()).toEqual({
    text: 'BEGIN:VCARD\r\nVERSION:3.0\r\nN:López\\; Soto;Ana\\nMarta;;;\r\nFN:Ana\\, López\r\nORG:ProjectApp\\nColombia\r\nTITLE:Dirección\\; Comercial\r\nEMAIL;TYPE=WORK:ana@example.com\r\nTEL;TYPE=CELL:+57 300 123 4567\r\nURL:https://ana.example.com\r\nEND:VCARD',
    type: 'text/vcard;charset=utf-8',
  });
  expect(harness.createObjectURL).toHaveBeenCalledTimes(1);
});

test('starts a keepalive analytics request for a data-link before native navigation can proceed', () => {
  // Falla si salir por un enlace deja de registrar la visita con su clave concreta.
  const harness = runtime({ html: '<a data-link data-link-key="portfolio" href="https://example.com">Portafolio</a>' });
  const link = harness.document.querySelector('[data-link]');
  link.addEventListener('click', (event) => event.preventDefault());

  harness.click(link);

  expect(harness.fetch).toHaveBeenCalledWith('/api/link-clicks/', {
    method: 'POST',
    body: '{"key":"portfolio"}',
    headers: { 'Content-Type': 'application/json' },
    keepalive: true,
    credentials: 'omit',
  });
});

test('only exposes PWA installation after its prompt and hides it after the user choice', async () => {
  // Falla si el instalador aparece sin permiso, queda visible tras usarlo, o se muestra para perfiles sin PWA.
  const enabled = runtime({ html: '<button data-action="install-pwa" hidden>Instalar</button>', profileData: profile({ pwa_enabled: true }) });
  const install = enabled.document.querySelector('[data-action="install-pwa"]');
  const prompt = jest.fn().mockResolvedValue(undefined);
  let resolveChoice;
  const userChoice = new Promise((resolve) => { resolveChoice = resolve; });
  const event = { preventDefault: jest.fn(), prompt, userChoice };

  expect(install.hidden).toBe(true);
  enabled.beforeInstallPrompt(event);
  expect(install.hidden).toBe(false);
  enabled.click(install);
  await settle();
  expect(prompt).toHaveBeenCalledTimes(1);
  resolveChoice({ outcome: 'accepted' });
  await userChoice;
  await settle();
  expect(install.hidden).toBe(true);

  const disabled = runtime({ html: '<button data-action="install-pwa" hidden>Instalar</button>' });
  const unavailable = disabled.document.querySelector('[data-action="install-pwa"]');
  disabled.beforeInstallPrompt({ preventDefault: jest.fn() });

  expect(unavailable.hidden).toBe(true);
});

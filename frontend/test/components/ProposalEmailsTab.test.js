/**
 * Tests for ProposalEmailsTab logic.
 *
 * Covers: basePath computation, canSend validation, section management,
 * file validation, status labels, date formatting, and title selection.
 *
 * Following project convention: extract and test component logic directly
 * rather than mounting Vue components.
 */

// ── basePath logic (mirrors computed in component, driven by activeMode) ────

function basePath(activeMode) {
  return activeMode === 'proposal' ? 'proposal-email' : 'branded-email';
}

describe('basePath', () => {
  it('returns proposal-email when activeMode is proposal', () => {
    expect(basePath('proposal')).toBe('proposal-email');
  });

  it('returns branded-email when activeMode is branded', () => {
    expect(basePath('branded')).toBe('branded-email');
  });

  it('returns branded-email for unknown activeMode', () => {
    expect(basePath('something')).toBe('branded-email');
  });
});


// ── canSend validation (mirrors computed in component) ──────────────────────

function canSend(recipient, subject, sections) {
  if (!recipient.trim()) return false;
  if (!subject.trim()) return false;
  if (!sections.some(s => s.text.trim())) return false;
  return true;
}

describe('canSend', () => {
  it('returns true when all fields are filled', () => {
    expect(canSend('test@example.com', 'Subject', [{ text: 'content' }])).toBe(true);
  });

  it('returns false when recipient is empty', () => {
    expect(canSend('', 'Subject', [{ text: 'content' }])).toBe(false);
  });

  it('returns false when recipient is whitespace only', () => {
    expect(canSend('   ', 'Subject', [{ text: 'content' }])).toBe(false);
  });

  it('returns false when subject is empty', () => {
    expect(canSend('test@example.com', '', [{ text: 'content' }])).toBe(false);
  });

  it('returns false when all sections are empty', () => {
    expect(canSend('test@example.com', 'Subject', [{ text: '' }, { text: '  ' }])).toBe(false);
  });

  it('returns true when at least one section has content', () => {
    expect(canSend('test@example.com', 'Subject', [{ text: '' }, { text: 'valid' }])).toBe(true);
  });
});


// ── Section management ──────────────────────────────────────────────────────

describe('section management', () => {
  let sectionIdSeq;
  const nextSectionId = () => ++sectionIdSeq;

  function addSection(sections) {
    sections.push({ id: nextSectionId(), text: '' });
  }

  function removeSection(sections, idx) {
    if (sections.length > 1) {
      sections.splice(idx, 1);
    }
  }

  beforeEach(() => {
    sectionIdSeq = 0;
  });

  it('adds a new empty section with incremental id', () => {
    const sections = [{ id: nextSectionId(), text: 'first' }];
    addSection(sections);

    expect(sections).toHaveLength(2);
    expect(sections[1].text).toBe('');
    expect(sections[1].id).toBe(2);
  });

  it('removes section at given index', () => {
    const sections = [
      { id: 1, text: 'first' },
      { id: 2, text: 'second' },
    ];
    removeSection(sections, 0);

    expect(sections).toHaveLength(1);
    expect(sections[0].text).toBe('second');
  });

  it('does not remove the last remaining section', () => {
    const sections = [{ id: 1, text: 'only' }];
    removeSection(sections, 0);

    expect(sections).toHaveLength(1);
    expect(sections[0].text).toBe('only');
  });
});


// ── File validation ─────────────────────────────────────────────────────────

const ALLOWED_EXTENSIONS = new Set(['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg']);
const MAX_FILE_SIZE = 15 * 1024 * 1024;

function validateFile(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    return `${file.name}: tipo no permitido`;
  }
  if (file.size > MAX_FILE_SIZE) {
    return `${file.name}: excede 15 MB`;
  }
  return null;
}

describe('file validation', () => {
  it('accepts a valid PDF file', () => {
    expect(validateFile({ name: 'contract.pdf', size: 1024 })).toBeNull();
  });

  it('accepts a valid DOCX file', () => {
    expect(validateFile({ name: 'report.docx', size: 1024 })).toBeNull();
  });

  it('accepts a valid image file', () => {
    expect(validateFile({ name: 'photo.jpg', size: 1024 })).toBeNull();
  });

  it('rejects a disallowed extension', () => {
    const error = validateFile({ name: 'malware.exe', size: 1024 });
    expect(error).toContain('tipo no permitido');
  });

  it('rejects a file exceeding 15 MB', () => {
    const error = validateFile({ name: 'large.pdf', size: 16 * 1024 * 1024 });
    expect(error).toContain('excede 15 MB');
  });

  it('handles uppercase extensions correctly', () => {
    expect(validateFile({ name: 'photo.PNG', size: 1024 })).toBeNull();
  });
});


// ── Status labels ───────────────────────────────────────────────────────────

const STATUS_LABELS = { sent: 'Enviado', delivered: 'Entregado', bounced: 'Rebotado', failed: 'Fallido' };

function statusLabel(s) {
  return STATUS_LABELS[s] || s;
}

describe('statusLabel', () => {
  it('returns Enviado for sent status', () => {
    expect(statusLabel('sent')).toBe('Enviado');
  });

  it('returns Fallido for failed status', () => {
    expect(statusLabel('failed')).toBe('Fallido');
  });

  it('returns raw value for unknown status', () => {
    expect(statusLabel('pending')).toBe('pending');
  });
});


// ── Date formatting ─────────────────────────────────────────────────────────

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

describe('formatDate', () => {
  it('formats an ISO date string to Colombian locale', () => {
    const result = formatDate('2026-03-15T10:30:00Z');
    expect(result).toContain('2026');
    expect(result).toContain('15');
  });

  it('returns empty string for null', () => {
    expect(formatDate(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(formatDate(undefined)).toBe('');
  });

  it('returns empty string for empty string', () => {
    expect(formatDate('')).toBe('');
  });
});


// ── Title selection by mode ─────────────────────────────────────────────────

function composerTitle(mode) {
  return mode === 'proposal' ? 'Enviar correo de propuesta' : 'Enviar correo con branding';
}

describe('composerTitle', () => {
  it('returns proposal title for proposal mode', () => {
    expect(composerTitle('proposal')).toBe('Enviar correo de propuesta');
  });

  it('returns branded title for branded mode', () => {
    expect(composerTitle('branded')).toBe('Enviar correo con branding');
  });
});


// ── Default greeting logic ──────────────────────────────────────────────────

function defaultGreeting(clientName) {
  return clientName ? `Hola ${clientName}` : 'Hola';
}

describe('defaultGreeting', () => {
  it('includes client name when provided', () => {
    expect(defaultGreeting('Carlos')).toBe('Hola Carlos');
  });

  it('returns plain Hola when client name is empty', () => {
    expect(defaultGreeting('')).toBe('Hola');
  });

  it('returns plain Hola when client name is null', () => {
    expect(defaultGreeting(null)).toBe('Hola');
  });
});

/**
 * Given a diagnostic, return the descriptor for the single "next logical
 * action" to show on the right side of the admin editor's sticky action bar.
 * Returns null when no next action is appropriate (terminal states, or draft
 * without a client email).
 *
 * Descriptor shape: { key, label, colorClass }
 *   - key: 'send' | 'analyze' | 'send-final' | 'approve' | 'finish'
 *   - label: button label (Spanish)
 *   - colorClass: Tailwind classes for the button background / hover
 */
export function getDiagnosticNextAction(diagnostic) {
  if (!diagnostic) return null;

  const status = diagnostic.status;
  const transitions = diagnostic.available_transitions || [];
  const hasEmail = Boolean(diagnostic.client?.email);

  if (status === 'draft') {
    if (!hasEmail) return null;
    return {
      key: 'send',
      label: 'Enviar envío inicial',
      colorClass: 'bg-info-strong text-white hover:bg-info-strong/90',
    };
  }

  if (status === 'sent' || status === 'viewed') {
    if (transitions.includes('negotiating')) {
      return {
        key: 'analyze',
        label: 'Marcar en análisis',
        colorClass: 'bg-warning-strong text-white hover:bg-warning-strong/90',
      };
    }
    return null;
  }

  if (status === 'negotiating' && !diagnostic.final_sent_at) {
    return {
      key: 'send-final',
      label: 'Enviar diagnóstico final',
      colorClass: 'bg-primary text-white hover:bg-primary-strong',
    };
  }

  return null;
}

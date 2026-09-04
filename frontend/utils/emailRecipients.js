export const EMAIL_RECIPIENT_LIMIT = 10;

export function emailRecipient(email, { name = '', clientId = null } = {}) {
  return {
    email: String(email || '').trim().toLowerCase(),
    name,
    clientId,
  };
}

export function recipientEmails(recipients) {
  return (recipients || []).map((recipient) => (
    typeof recipient === 'string' ? recipient : recipient.email
  )).filter(Boolean);
}

export function appendEmailRecipients(formData, toRecipients, ccRecipients) {
  formData.append('recipient_emails', JSON.stringify(recipientEmails(toRecipients)));
  formData.append('cc_emails', JSON.stringify(recipientEmails(ccRecipients)));
}

export function recipientSummary(recipients) {
  return recipientEmails(recipients).join(', ');
}

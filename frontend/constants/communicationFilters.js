/**
 * Factory quick filters for /panel/communications.
 *
 * Definitions stay in code while SavedFilterTab placeholder rows carry each
 * user's order and visibility. This keeps the same builtins/own-tabs contract
 * used by Accounting and Clients without freezing derived criteria in JSON.
 */
export const COMMUNICATION_BUILTIN_TABS = Object.freeze([
  {
    id: 'draft-pending',
    name: 'Borradores pendientes',
    filters: { message_status: ['draft'] },
  },
  {
    id: 'sent-unanswered',
    name: 'Enviados sin respuesta',
    filters: {
      status: ['open'],
      direction: ['outgoing'],
      message_status: ['sent'],
      reply_status: ['unanswered'],
    },
  },
  {
    id: 'open',
    name: 'Abiertos',
    filters: { status: ['open'] },
  },
  {
    id: 'closed',
    name: 'Cerrados',
    filters: { status: ['closed'] },
  },
  {
    id: 'channel-email',
    name: 'Correo',
    filters: { channel: ['email'] },
  },
  {
    id: 'channel-whatsapp',
    name: 'WhatsApp',
    filters: { channel: ['whatsapp'] },
  },
]);

export const COMMUNICATION_BUILTIN_BY_ID = new Map(
  COMMUNICATION_BUILTIN_TABS.map((tab) => [String(tab.id), tab]),
);

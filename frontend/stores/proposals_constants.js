export const PROPOSAL_STATUS = Object.freeze({
  DRAFT: 'draft',
  SENT: 'sent',
  VIEWED: 'viewed',
  NEGOTIATING: 'negotiating',
  ACCEPTED: 'accepted',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
  FINISHED: 'finished',
});

export const CONTRACT_LOCKED_STATUSES = Object.freeze([
  PROPOSAL_STATUS.SENT,
  PROPOSAL_STATUS.VIEWED,
]);

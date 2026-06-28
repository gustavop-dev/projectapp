// Default percentage of the total investment charged for annual hosting.
// Single source of truth for the frontend; mirrors the backend model default
// (BusinessProposal.hosting_percent / ProposalDefaultConfig.hosting_percent).
export const DEFAULT_HOSTING_PERCENT = 80;

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

// Statuses where the client's decision is already settled. Time-sensitive /
// urgency notices on the public view (expiration countdown, limited-time
// discount banner, hosting tier discount badges) must be hidden for these.
// `expired` is handled separately via the expired-state logic.
export const RESOLVED_PROPOSAL_STATUSES = Object.freeze([
  PROPOSAL_STATUS.ACCEPTED,
  PROPOSAL_STATUS.REJECTED,
  PROPOSAL_STATUS.FINISHED,
]);

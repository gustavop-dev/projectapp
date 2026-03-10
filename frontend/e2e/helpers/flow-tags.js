/**
 * Flow tag constants for consistent E2E test tagging.
 *
 * Usage:
 *   import { ADMIN_LOGIN } from '../helpers/flow-tags.js';
 *   test('...', { tag: [...ADMIN_LOGIN, '@role:admin'] }, async ({ page }) => { ... });
 */

// ── Layout ──
export const LAYOUT_NAVBAR_NAVIGATION = ['@flow:layout-navbar-navigation', '@module:layout', '@priority:P2'];
export const LAYOUT_LOCALE_SWITCH = ['@flow:layout-locale-switch', '@module:layout', '@priority:P2'];
export const LAYOUT_FOOTER_NAVIGATION = ['@flow:layout-footer-navigation', '@module:layout', '@priority:P3'];

// ── Public ──
export const PUBLIC_HOME = ['@flow:public-home', '@module:public', '@priority:P1'];
export const PUBLIC_PORTFOLIO = ['@flow:public-portfolio', '@module:public', '@priority:P2'];
export const PUBLIC_PORTFOLIO_DETAIL = ['@flow:public-portfolio-detail', '@module:public', '@priority:P2'];
export const PUBLIC_ABOUT_US = ['@flow:public-about-us', '@module:public', '@priority:P3'];
export const PUBLIC_LANDING_WEB_DESIGN = ['@flow:public-landing-web-design', '@module:public', '@priority:P2'];
export const PUBLIC_CONTACT_SUBMIT = ['@flow:public-contact-submit', '@module:public', '@priority:P1'];

// ── Blog ──
export const BLOG_LIST = ['@flow:blog-list', '@module:blog', '@priority:P2'];
export const BLOG_DETAIL = ['@flow:blog-detail', '@module:blog', '@priority:P2'];

// ── Proposal ──
export const PROPOSAL_VIEW = ['@flow:proposal-view', '@module:proposal', '@priority:P1'];
export const PROPOSAL_VIEW_NAVIGATION = ['@flow:proposal-view-navigation', '@module:proposal', '@priority:P1'];
export const PROPOSAL_VIEW_ONBOARDING = ['@flow:proposal-view-onboarding', '@module:proposal', '@priority:P3'];
export const PROPOSAL_RESPOND = ['@flow:proposal-respond', '@module:proposal', '@priority:P1'];
export const PROPOSAL_DOWNLOAD_PDF = ['@flow:proposal-download-pdf', '@module:proposal', '@priority:P2'];

// ── Auth ──
export const ADMIN_LOGIN = ['@flow:admin-login', '@module:auth', '@priority:P1'];

// ── Admin ──
export const ADMIN_DASHBOARD = ['@flow:admin-dashboard', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_LIST = ['@flow:admin-proposal-list', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_CREATE = ['@flow:admin-proposal-create', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_CREATE_FROM_JSON = ['@flow:admin-proposal-create-from-json', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_EDIT = ['@flow:admin-proposal-edit', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_DELETE = ['@flow:admin-proposal-delete', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_SEND = ['@flow:admin-proposal-send', '@module:admin', '@priority:P1'];
export const ADMIN_BLOG_LIST = ['@flow:admin-blog-list', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_SECTION_EDIT_FORM = ['@flow:admin-proposal-section-edit-form', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_SECTION_EDIT_PASTE = ['@flow:admin-proposal-section-edit-paste', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_SECTION_REORDER = ['@flow:admin-proposal-section-reorder', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_FORM = ['@flow:admin-proposal-functional-requirements-form', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_FUNCTIONAL_REQUIREMENTS_PASTE = ['@flow:admin-proposal-functional-requirements-paste', '@module:admin', '@priority:P1'];
export const ADMIN_BLOG_CREATE = ['@flow:admin-blog-create', '@module:admin', '@priority:P2'];
export const ADMIN_BLOG_CREATE_FROM_JSON = ['@flow:admin-blog-create-from-json', '@module:admin', '@priority:P2'];
export const ADMIN_BLOG_EDIT = ['@flow:admin-blog-edit', '@module:admin', '@priority:P2'];
export const ADMIN_BLOG_DELETE = ['@flow:admin-blog-delete', '@module:admin', '@priority:P3'];

// ── Proposal (new) ──
export const PROPOSAL_SHARE = ['@flow:proposal-share', '@module:proposal', '@priority:P2'];
export const PROPOSAL_ENGAGEMENT_TRACKING = ['@flow:proposal-engagement-tracking', '@module:proposal', '@priority:P2'];

// ── Admin (new) ──
export const ADMIN_PROPOSAL_DUPLICATE = ['@flow:admin-proposal-duplicate', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_COMMENT = ['@flow:admin-proposal-comment', '@module:admin', '@priority:P3'];
export const ADMIN_PROPOSAL_ANALYTICS = ['@flow:admin-proposal-analytics', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_DASHBOARD = ['@flow:admin-proposal-dashboard', '@module:admin', '@priority:P2'];
export const ADMIN_MINI_CRM_CLIENTS = ['@flow:admin-mini-crm-clients', '@module:admin', '@priority:P2'];

// ── Admin (latest features) ──
export const ADMIN_BLOG_CALENDAR = ['@flow:admin-blog-calendar', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_MANUAL_ALERTS = ['@flow:admin-proposal-manual-alerts', '@module:admin', '@priority:P2'];

// ── Admin Portfolio ──
export const ADMIN_PORTFOLIO_LIST = ['@flow:admin-portfolio-list', '@module:admin', '@priority:P2'];
export const ADMIN_PORTFOLIO_CREATE = ['@flow:admin-portfolio-create', '@module:admin', '@priority:P2'];
export const ADMIN_PORTFOLIO_EDIT = ['@flow:admin-portfolio-edit', '@module:admin', '@priority:P2'];
export const ADMIN_PORTFOLIO_DELETE = ['@flow:admin-portfolio-delete', '@module:admin', '@priority:P2'];

// ── v1.6.0 features ──
export const ADMIN_PROPOSAL_WIN_RATE_DASHBOARD = ['@flow:admin-proposal-win-rate-dashboard', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_ENGAGEMENT_SCORE = ['@flow:admin-proposal-engagement-score', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_METRICS_MANUAL = ['@flow:admin-proposal-metrics-manual', '@module:admin', '@priority:P3'];
export const PROPOSAL_WELCOME_BACK = ['@flow:proposal-welcome-back', '@module:proposal', '@priority:P2'];
export const PROPOSAL_PROCESS_METHODOLOGY = ['@flow:proposal-process-methodology', '@module:proposal', '@priority:P2'];
export const ADMIN_PROPOSAL_ZOMBIE_SEGMENT = ['@flow:admin-proposal-zombie-segment', '@module:admin', '@priority:P2'];
export const PROPOSAL_SHARE_HINT = ['@flow:proposal-share-hint', '@module:proposal', '@priority:P3'];
export const PROPOSAL_COUNTDOWN_REALTIME = ['@flow:proposal-countdown-realtime', '@module:proposal', '@priority:P3'];
export const ADMIN_PROPOSAL_CREATE_AND_SEND = ['@flow:admin-proposal-create-and-send', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_CREATE_PREVIEW = ['@flow:admin-proposal-create-preview', '@module:admin', '@priority:P2'];
export const ADMIN_DASHBOARD_PIPELINE_VALUE = ['@flow:admin-dashboard-pipeline-value', '@module:admin', '@priority:P2'];
export const PROPOSAL_REJECTION_OPTIONAL_REASON = ['@flow:proposal-rejection-optional-reason', '@module:proposal', '@priority:P2'];
export const PROPOSAL_CALCULATOR_TIMELINE = ['@flow:proposal-calculator-timeline', '@module:proposal', '@priority:P1'];
export const ADMIN_DISCOUNT_ANALYSIS_ENHANCED = ['@flow:admin-discount-analysis-enhanced', '@module:admin', '@priority:P3'];

// ── Phase 2+ new flows ──
export const PROPOSAL_NEGOTIATE = ['@flow:proposal-negotiate', '@module:proposal', '@priority:P1'];
export const PROPOSAL_INVESTMENT_CALCULATOR = ['@flow:proposal-investment-calculator', '@module:proposal', '@priority:P1'];
export const ADMIN_PROPOSAL_ACTIONS_MODAL = ['@flow:admin-proposal-actions-modal', '@module:admin', '@priority:P1'];
export const PROPOSAL_COMMENT_FROM_CLOSING = ['@flow:proposal-comment-from-closing', '@module:proposal', '@priority:P2'];
export const PROPOSAL_REJECTION_SMART_RECOVERY = ['@flow:proposal-rejection-smart-recovery', '@module:proposal', '@priority:P2'];
export const PROPOSAL_FUNCTIONAL_REQUIREMENTS_MODAL = ['@flow:proposal-functional-requirements-modal', '@module:proposal', '@priority:P2'];
export const ADMIN_PROPOSAL_SEND_FROM_LISTING = ['@flow:admin-proposal-send-from-listing', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_ACTIVITY_LOG = ['@flow:admin-proposal-activity-log', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_AUTOMATIONS_TOGGLE = ['@flow:admin-proposal-automations-toggle', '@module:admin', '@priority:P2'];

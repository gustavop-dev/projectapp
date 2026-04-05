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
export const PROPOSAL_VIEW_PASTE_RENDERING = ['@flow:proposal-view-paste-rendering', '@module:proposal', '@priority:P2'];
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
export const ADMIN_PROPOSAL_ACTIVITY_LOG = ['@flow:admin-proposal-log-activity', '@module:admin', '@priority:P2'];

// ── Calculator modules (PWA, AI, Reports & Alerts) ──
export const PROPOSAL_CALCULATOR_MODULES = ['@flow:proposal-calculator-modules', '@module:proposal', '@priority:P1'];

// ── v1.7.0 new flows ──
export const PROPOSAL_EXPIRED_GRACEFUL = ['@flow:proposal-expired-graceful', '@module:proposal', '@priority:P1'];
export const ADMIN_PROPOSAL_BATCH_ACTIONS = ['@flow:admin-proposal-batch-actions', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_QUICK_SEND = ['@flow:admin-proposal-quick-send', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_QUICK_LOG = ['@flow:admin-proposal-quick-log', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_JSON_IMPORT_WARNINGS = ['@flow:admin-proposal-json-import-warnings', '@module:admin', '@priority:P2'];
export const PROPOSAL_SUMMARY_KPIS = ['@flow:proposal-summary-kpis', '@module:proposal', '@priority:P2'];
export const PROPOSAL_CALCULATOR_NEW_MODULES = ['@flow:proposal-calculator-new-modules', '@module:proposal', '@priority:P2'];
export const PROPOSAL_CALCULATOR_INTEGRATIONS = ['@flow:proposal-calculator-integrations', '@module:proposal', '@priority:P2'];
export const PROPOSAL_DISCOUNT_MULTI_SECTION = ['@flow:proposal-discount-multi-section', '@module:proposal', '@priority:P2'];

// ── v1.8.0 audit flows ──
export const PROPOSAL_CALCULATOR_SELECTED_FIRST = ['@flow:proposal-calculator-selected-first', '@module:proposal', '@priority:P2'];
export const PROPOSAL_CALCULATOR_MICRO_FEEDBACK = ['@flow:proposal-calculator-micro-feedback', '@module:proposal', '@priority:P2'];
export const PROPOSAL_PAYMENT_PLAN_CLOSING = ['@flow:proposal-payment-plan-closing', '@module:proposal', '@priority:P2'];
export const PROPOSAL_POST_ACCEPTANCE_WELCOME = ['@flow:proposal-post-acceptance-welcome', '@module:proposal', '@priority:P1'];
export const PROPOSAL_STRUCTURED_NEGOTIATION = ['@flow:proposal-structured-negotiation', '@module:proposal', '@priority:P2'];
export const PROPOSAL_CONDITIONAL_ACCEPTANCE = ['@flow:proposal-conditional-acceptance', '@module:proposal', '@priority:P2'];
export const ADMIN_PROPOSAL_INLINE_STATUS_CHANGE = ['@flow:admin-proposal-inline-status-change', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_SCORECARD = ['@flow:admin-proposal-scorecard', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_SECTION_COMPLETENESS = ['@flow:admin-proposal-section-completeness', '@module:admin', '@priority:P3'];
export const ADMIN_PROPOSAL_DEFAULTS_CONFIG = ['@flow:admin-proposal-defaults-config', '@module:admin', '@priority:P2'];
export const ADMIN_EMAIL_TEMPLATES_CONFIG = ['@flow:admin-email-templates-config', '@module:admin', '@priority:P2'];
// PROPOSAL_STICKY_BAR_ACCEPT removed — feature deleted (ProposalResponseButtons removed)
export const PROPOSAL_EXECUTIVE_TO_DETAILED = ['@flow:proposal-executive-to-detailed', '@module:proposal', '@priority:P2'];
export const PROPOSAL_TECHNICAL_VIEW = ['@flow:proposal-technical-view', '@module:proposal', '@priority:P2'];
export const PROPOSAL_SECTION_ONBOARDING = ['@flow:proposal-section-onboarding', '@module:proposal', '@priority:P3'];

// ── Platform ──
export const PLATFORM_LOGIN = ['@flow:platform-login', '@module:platform', '@priority:P1'];
export const PLATFORM_VERIFY_ONBOARDING = ['@flow:platform-verify-onboarding', '@module:platform', '@priority:P1'];
export const PLATFORM_COMPLETE_PROFILE = ['@flow:platform-complete-profile', '@module:platform', '@priority:P1'];
export const PLATFORM_KANBAN_BOARD = ['@flow:platform-kanban-board', '@module:platform', '@priority:P1'];
export const PLATFORM_DASHBOARD = ['@flow:platform-dashboard', '@module:platform', '@priority:P2'];
export const PLATFORM_SIDEBAR_NAVIGATION = ['@flow:platform-sidebar-navigation', '@module:platform', '@priority:P2'];
export const PLATFORM_PROJECT_LIST = ['@flow:platform-project-list', '@module:platform', '@priority:P2'];
export const PLATFORM_PROJECT_DETAIL = ['@flow:platform-project-detail', '@module:platform', '@priority:P2'];
export const PLATFORM_UNIFIED_BOARD = ['@flow:platform-unified-board', '@module:platform', '@priority:P2'];
export const PLATFORM_ADMIN_CLIENT_LIST = ['@flow:platform-admin-client-list', '@module:platform', '@priority:P2'];
export const PLATFORM_ADMIN_CLIENT_DETAIL = ['@flow:platform-admin-client-detail', '@module:platform', '@priority:P2'];
export const PLATFORM_PROFILE_EDIT = ['@flow:platform-profile-edit', '@module:platform', '@priority:P2'];
export const PLATFORM_ADMIN_PROJECT_CREATE = ['@flow:platform-admin-project-create', '@module:platform', '@priority:P3'];
export const PLATFORM_KANBAN_CARD_COMMENTS = ['@flow:platform-kanban-card-comments', '@module:platform', '@priority:P3'];

// ── Platform new flows (proposal integration + modules) ──
export const PLATFORM_CHANGE_REQUESTS = ['@flow:platform-change-requests', '@module:platform', '@priority:P2'];
export const PLATFORM_BUG_REPORTS = ['@flow:platform-bug-reports', '@module:platform', '@priority:P2'];
export const PLATFORM_DELIVERABLES = ['@flow:platform-deliverables', '@module:platform', '@priority:P2'];
export const PLATFORM_HOSTING_SUBSCRIPTION = ['@flow:platform-hosting-subscription', '@module:platform', '@priority:P1'];
export const PLATFORM_NOTIFICATIONS = ['@flow:platform-notifications', '@module:platform', '@priority:P2'];
export const PLATFORM_KANBAN_JSON_UPLOAD = ['@flow:platform-kanban-json-upload', '@module:platform', '@priority:P2'];
export const PLATFORM_REQUIREMENT_CLIENT_REVIEW = ['@flow:platform-requirement-client-review', '@module:platform', '@priority:P2'];
export const PLATFORM_COLLECTION_ACCOUNTS_LIST = ['@flow:platform-collection-accounts-list', '@module:platform', '@priority:P2'];
export const PLATFORM_COLLECTION_ACCOUNT_DETAIL = ['@flow:platform-collection-account-detail', '@module:platform', '@priority:P2'];
export const PLATFORM_PROJECT_COLLECTION_ACCOUNTS = ['@flow:platform-project-collection-accounts', '@module:platform', '@priority:P2'];
export const PLATFORM_DELIVERABLE_DETAIL = ['@flow:platform-deliverable-detail', '@module:platform', '@priority:P2'];

// ── v2.7.0 new flows ──
export const ADMIN_DOCUMENT_LIST = ['@flow:admin-document-list', '@module:admin', '@priority:P2'];
export const ADMIN_DOCUMENT_CREATE = ['@flow:admin-document-create', '@module:admin', '@priority:P2'];
export const ADMIN_DOCUMENT_EDIT = ['@flow:admin-document-edit', '@module:admin', '@priority:P2'];
export const ADMIN_ADMIN_MANAGEMENT = ['@flow:admin-admin-management', '@module:admin', '@priority:P3'];
export const ADMIN_EMAIL_DELIVERABILITY = ['@flow:admin-email-deliverability', '@module:admin', '@priority:P3'];
export const PUBLIC_LANDING_SOFTWARE = ['@flow:public-landing-software', '@module:public', '@priority:P3'];
export const PUBLIC_LANDING_APPS = ['@flow:public-landing-apps', '@module:public', '@priority:P3'];

// ── v2.10.0 new flows ──
export const PLATFORM_PROJECT_DATA_MODEL = ['@flow:platform-project-data-model', '@module:platform', '@priority:P2'];

// ── v2.9.0 contract & documents flows ──
export const ADMIN_PROPOSAL_CONTRACT_GENERATE = ['@flow:admin-proposal-contract-generate', '@module:admin', '@priority:P1'];
export const ADMIN_PROPOSAL_CONTRACT_EDIT = ['@flow:admin-proposal-contract-edit', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_CONTRACT_DOWNLOAD = ['@flow:admin-proposal-contract-download', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_DOCUMENTS_MANAGE = ['@flow:admin-proposal-documents-manage', '@module:admin', '@priority:P2'];
export const ADMIN_PROPOSAL_DOCUMENTS_SEND = ['@flow:admin-proposal-documents-send', '@module:admin', '@priority:P1'];

// ── Composed email flows ──
export const ADMIN_SEND_BRANDED_EMAIL = ['@flow:admin-send-branded-email', '@module:admin', '@priority:P2'];
export const ADMIN_SEND_PROPOSAL_EMAIL = ['@flow:admin-send-proposal-email', '@module:admin', '@priority:P2'];

// ── v2.12.0 LinkedIn flows ──
export const ADMIN_BLOG_LINKEDIN_CONNECT = ['@flow:admin-blog-linkedin-connect', '@module:admin', '@priority:P2'];
export const ADMIN_BLOG_LINKEDIN_PUBLISH = ['@flow:admin-blog-linkedin-publish', '@module:admin', '@priority:P2'];

// ── v2.13.0 Legal pages ──
export const PUBLIC_PRIVACY_POLICY = ['@flow:public-privacy-policy', '@module:public', '@priority:P4'];
export const PUBLIC_TERMS_CONDITIONS = ['@flow:public-terms-conditions', '@module:public', '@priority:P4'];

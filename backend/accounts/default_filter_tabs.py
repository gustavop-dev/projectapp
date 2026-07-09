"""
Code-level defaults for ``SavedFilterTab``, keyed by view.

Each entry is ``{'name': str, 'filters': dict}``. The ``filters`` dict must
match the frontend ``DEFAULT_FILTERS`` shape for its view:

- ``client``   -> ``frontend/composables/useClientFilters.js`` (lastStatuses,
  projectTypes, marketTypes, totalProposalsMin/Max, acceptedMin/Max,
  lastActivityAfter/Before)
- ``proposal`` -> ``frontend/composables/useProposalFilters.js`` (statuses,
  projectTypes, marketTypes, currencies, languages, investmentMin/Max,
  heatScoreMin/Max, viewCountMin/Max, createdAfter/Before,
  lastActivityAfter/Before, isActive, technicalViewed)

Partial dicts are fine: the frontend merges stored filters over its own
fresh defaults, so only the keys that differ need to be listed here.

Values captured from the production DB on 2026-07-09 (one tab per proposal
status, mirrored across the client and proposal views). Re-seed with
``python manage.py seed_filter_tabs``.
"""

DEFAULT_FILTER_TABS = {
    'client': [
        {'name': 'Draft', 'filters': {'lastStatuses': ['draft']}},
        {'name': 'Sent/Viewed', 'filters': {'lastStatuses': ['sent', 'viewed']}},
        {'name': 'Negociación', 'filters': {'lastStatuses': ['negotiating']}},
        {'name': 'Accepted', 'filters': {'lastStatuses': ['accepted']}},
        {'name': 'Expired', 'filters': {'lastStatuses': ['expired']}},
        {'name': 'Rejected', 'filters': {'lastStatuses': ['rejected']}},
        {'name': 'Finished', 'filters': {'lastStatuses': ['finished']}},
    ],
    'proposal': [
        {'name': 'Draft', 'filters': {'statuses': ['draft']}},
        {'name': 'Sent/Viewed', 'filters': {'statuses': ['sent', 'viewed']}},
        {'name': 'Negociación', 'filters': {'statuses': ['negotiating']}},
        {'name': 'Accepted', 'filters': {'statuses': ['accepted']}},
        {'name': 'Expired', 'filters': {'statuses': ['expired']}},
        {'name': 'Rejected', 'filters': {'statuses': ['rejected']}},
        {'name': 'Finished', 'filters': {'statuses': ['finished']}},
    ],
}

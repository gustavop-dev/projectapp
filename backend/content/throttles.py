"""Custom DRF throttle classes for ProjectApp public endpoints."""

from rest_framework.throttling import AnonRateThrottle


class TrackingAnonThrottle(AnonRateThrottle):
    """Rate-limit public tracking pings (proposal + diagnostic) at 60/min per IP.

    Public `track/`, `track-section/`, `track-calculator/`,
    `track-requirement-click/` endpoints run under `AllowAny` so anyone can POST.
    Without a throttle, a script could inflate `view_count`, skew heat scores,
    or spam stakeholder emails. 60/min leaves plenty of headroom for genuine
    user activity (30s batch flushes + section nav) while capping abuse.

    The rate is hardcoded in `get_rate()` so no settings edits are needed.
    """

    scope = 'tracking-anon'

    def get_rate(self):
        return '60/min'

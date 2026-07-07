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


class PublicProposalActionThrottle(AnonRateThrottle):
    """Rate-limit anonymous proposal actions (respond/comment/share/followup).

    These endpoints are reachable with just a proposal UUID/slug and write
    to the database and/or send email. 10/min per IP is far above genuine
    client behavior while stopping scripted spam. Authenticated staff are
    exempt (AnonRateThrottle only counts anonymous requests).
    """

    scope = 'proposal-public-action'

    def get_rate(self):
        return '10/min'


class ProposalPdfThrottle(AnonRateThrottle):
    """Rate-limit anonymous PDF downloads — ReportLab renders are CPU-bound."""

    scope = 'proposal-pdf'

    def get_rate(self):
        return '6/min'


class MagicLinkRequestThrottle(AnonRateThrottle):
    """IP-level cap for magic-link requests.

    The endpoint already rate-limits per destination email (EmailLog,
    5-minute window); this adds a per-IP layer so one client cannot spray
    many addresses.
    """

    scope = 'proposal-magic-link'

    def get_rate(self):
        return '5/min'

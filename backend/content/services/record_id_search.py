"""Recognize existing numeric record IDs without changing textual searches."""
import re

from django.db.models import Q


def id_search_predicate(query):
    exact = bool(re.fullmatch(r'#[0-9]+', query))
    token = query[1:] if exact else query
    valid = bool(re.fullmatch(r'[0-9]{1,19}', token))
    record_id = int(token) if valid else 0
    predicate = Q(pk=record_id) if 0 < record_id < 2**63 else Q(pk__in=[])
    return exact, predicate

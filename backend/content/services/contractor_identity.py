"""Resolve which identification document stands for EL CONTRATISTA.

A contractor may be registered with a NIT, with a cédula, or — while the
company settings are still being filled in — with neither. The document has to
name the right one: printing "NIT" above a cédula (or the reverse) is a defect
in a signed contract, not a cosmetic detail.

The same NIT-over-cédula preference already drives the collection-account flow
(``collection_account_create_service.customer_snapshot_defaults``), which keeps
the value and its label in two separate fields for exactly this reason.
"""

NIT_LABEL = 'NIT'
CEDULA_LABEL = 'C.C.'
# Neither on file: the document is meant to be printed and completed by hand,
# so it keeps the dual label rather than claiming one of the two.
UNKNOWN_LABEL = 'NIT/C.C.'


def resolve_contractor_identity(nit, cedula, blank=''):
    """Return ``(id_type, id_number)`` for the contractor, NIT taking priority.

    ``blank`` is the placeholder to use as the number when neither document is
    on file — callers pass the same filler they use for every other missing
    param, so a half-filled contract stays visually consistent.
    """
    nit = (nit or '').strip()
    if nit:
        return NIT_LABEL, nit

    cedula = (cedula or '').strip()
    if cedula:
        return CEDULA_LABEL, cedula

    return UNKNOWN_LABEL, blank

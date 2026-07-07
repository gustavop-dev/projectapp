"""Effective-total investment helpers for business proposals.

Single home for the "base investment + selected calculator modules" math
shared by the admin metrics, the public serializer, the PDF renderer and
the email service. Moved verbatim from ``content/views/proposal.py`` so
services and serializers no longer import from the view module.
"""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from content.models import ProposalChangeLog, ProposalSection
from content.services.proposal_service import (
    CALC_MODULE_PREFIX,
    REGULAR_GROUP_PREFIX,
)


def safe_decimal(value, default=Decimal('0')):
    """Safely coerce unknown numeric input to Decimal."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def selected_group_ids_from_modules(selected_modules):
    """Normalize selected module ids to bare group ids."""
    if not isinstance(selected_modules, list):
        return set()

    group_ids = set()
    for raw in selected_modules:
        if raw in (None, ''):
            continue
        mod_id = str(raw).strip()
        if not mod_id:
            continue
        if mod_id.startswith(CALC_MODULE_PREFIX):
            group_ids.add(mod_id[len(CALC_MODULE_PREFIX):])
        elif mod_id.startswith(REGULAR_GROUP_PREFIX):
            group_ids.add(mod_id[len(REGULAR_GROUP_PREFIX):])
        else:
            group_ids.add(mod_id)
    return group_ids


def calculator_price_percent_by_group_id(fr_content_json):
    """
    Extract calculator-module price percentages from functional requirements JSON.
    """
    if not isinstance(fr_content_json, dict):
        return {}

    groups = list(fr_content_json.get('groups') or [])
    additional = list(fr_content_json.get('additionalModules') or [])
    price_by_group = {}

    for group in groups + additional:
        if not isinstance(group, dict):
            continue
        if not group.get('is_calculator_module'):
            continue
        group_id = str(group.get('id') or '').strip()
        if not group_id:
            continue
        pct = safe_decimal(group.get('price_percent'), default=None)
        if pct is None or pct <= 0:
            continue
        price_by_group[group_id] = pct

    return price_by_group


def calculate_effective_total_investment(
    base_total,
    selected_modules,
    fr_content_json,
    has_confirmed,
):
    """
    Compute effective investment shown in panel metrics:
    base investment + selected additional calculator modules.

    The ``has_confirmed`` flag determines whether ``selected_modules`` is the
    source of truth. When ``True``, the persisted list is used — unioned with
    the calculator modules the admin explicitly pinned (``selected is True``),
    which always win even over an empty confirmation, mirroring the client
    view. When ``False``, the persisted list is ignored and the admin's
    ``selected`` flags in the FR content JSON drive the initial scope
    (``default_selected`` only as a fallback when ``selected`` is absent).
    """
    base = safe_decimal(base_total).quantize(Decimal('0.01'))

    if has_confirmed:
        from content.services.proposal_service import (
            admin_pinned_calculator_group_ids,
        )
        selected_group_ids = (
            selected_group_ids_from_modules(selected_modules)
            | admin_pinned_calculator_group_ids(fr_content_json)
        )
    else:
        from content.services.proposal_service import (
            admin_default_calculator_group_ids,
        )
        selected_group_ids = admin_default_calculator_group_ids(fr_content_json)

    if not selected_group_ids:
        return base

    price_by_group = calculator_price_percent_by_group_id(fr_content_json)
    if not price_by_group:
        return base

    extras = Decimal('0')
    for group_id in selected_group_ids:
        pct = price_by_group.get(group_id)
        if pct is None:
            continue
        extras += (base * pct / Decimal('100')).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP,
        )

    return (base + extras).quantize(Decimal('0.01'))


def effective_total_for_proposal(proposal):
    """Single-proposal version of :func:`build_effective_totals_map`."""
    fr_section = proposal.sections.filter(
        section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
    ).only('content_json').first()
    fr_content = fr_section.content_json if fr_section else None
    return calculate_effective_total_investment(
        proposal.total_investment,
        proposal.selected_modules,
        fr_content,
        has_confirmed=proposal.has_confirmed_module_selection,
    )


def build_effective_totals_map(proposals):
    """Return {proposal_id: effective_total_decimal} for a proposal iterable."""
    proposal_list = list(proposals)
    if not proposal_list:
        return {}

    proposal_ids = [p.id for p in proposal_list]
    fr_content_by_proposal = dict(
        ProposalSection.objects
        .filter(
            proposal_id__in=proposal_ids,
            section_type='functional_requirements',
        )
        .values_list('proposal_id', 'content_json')
    )
    # Batch the confirmed-selection check so the per-proposal property
    # access below does not issue one EXISTS query per row.
    confirmed_ids = set(
        ProposalChangeLog.objects
        .filter(proposal_id__in=proposal_ids, change_type='calc_confirmed')
        .values_list('proposal_id', flat=True)
        .distinct()
    )

    return {
        p.id: calculate_effective_total_investment(
            p.total_investment,
            p.selected_modules,
            fr_content_by_proposal.get(p.id),
            has_confirmed=p.id in confirmed_ids,
        )
        for p in proposal_list
    }


def resync_investment_from_modules(proposal, fr_content_json):
    """Keep the investment section in sync with ``proposal.total_investment``.

    ``content_json.totalInvestment`` must always reflect the BASE investment
    (the number the admin typed in the General tab). It is used downstream
    as the basis for hosting calculations and other percent-derived values,
    so it must never be overwritten with the client's personalized total.

    ``paymentOptions`` descriptions *do* scale on the effective total,
    because those strings represent the actual amounts the client will pay
    after customizing their module selection.
    """
    effective = calculate_effective_total_investment(
        proposal.total_investment,
        proposal.selected_modules,
        fr_content_json,
        has_confirmed=proposal.has_confirmed_module_selection,
    )
    inv_section = proposal.sections.filter(section_type=ProposalSection.SectionType.INVESTMENT).first()
    if not inv_section or not inv_section.content_json:
        return
    base_total = int(safe_decimal(proposal.total_investment))
    base_formatted = f'${base_total:,}'.replace(',', '.')
    cj = dict(inv_section.content_json)
    currency_changed = cj.get('currency') != proposal.currency
    total_changed = cj.get('totalInvestment') != base_formatted

    # paymentOptions descriptions depend on the effective total; rebuild
    # unconditionally when paymentOptions exist so outdated amounts from a
    # prior selection do not leak through.
    payment_changed = False
    if cj.get('paymentOptions'):
        for opt in cj['paymentOptions']:
            pct_match = re.search(r'(\d+)%', opt.get('label', ''))
            if not pct_match:
                continue
            pct = Decimal(pct_match.group(1)) / Decimal(100)
            amount = int(effective * pct)
            new_desc = f'${amount:,}'.replace(',', '.') + f' {proposal.currency}'
            if opt.get('description') != new_desc:
                opt['description'] = new_desc
                payment_changed = True

    if not currency_changed and not total_changed and not payment_changed:
        return
    cj['totalInvestment'] = base_formatted
    cj['currency'] = proposal.currency
    inv_section.content_json = cj
    inv_section.save(update_fields=['content_json'])

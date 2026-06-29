"""Rewrite the legacy hosting renewal note on existing proposals.

Older proposals (and the previous default-config snapshot) stored a renewal note
with the OLD additive formula: ``Costo anterior + (6% × SMLMV)``. The offered
terms are now the multiplicative ``× (1 + (Δ%SMLMV + 8%))`` formula. This data
migration replaces the stored note ONLY when it clearly matches the old default
(mentions ``6%`` and ``SMLMV`` but not ``8%``), so genuinely customized notes are
left untouched. New proposals already get the new note from the refreshed config.
"""
from django.db import migrations


RENEWAL_ES = (
    'Renovaciones para cada año de renovación (a partir del segundo año): '
    'el costo se ajusta una vez al año tomando como referencia el porcentaje '
    'en que aumentó el SMLMV (Salario Mínimo Legal Mensual Vigente en Colombia) '
    'ese año, más un 8% fijo, aplicado sobre el costo del año anterior:\n\n'
    'Costo de renovación = Costo del año anterior × '
    '(1 + (% de aumento del SMLMV + 8%))\n\n'
    'Por ejemplo, si el SMLMV aumentó 5%, el incremento total sería '
    '5% + 8% = 13%. Si venías pagando $100.000 COP, el nuevo costo sería '
    '$113.000 COP (un aumento de $13.000).'
)

RENEWAL_EN = (
    'Renewals for each renewal year (from the second year onward): the cost '
    'is adjusted once a year based on the percentage by which the SMLMV '
    "(Colombia's monthly legal minimum wage) increased that year, plus a "
    "fixed 8%, applied to the previous year's cost:\n\n"
    'Renewal cost = Previous year cost × (1 + (SMLMV increase % + 8%))\n\n'
    'For example, if the SMLMV increased 5%, the total increase would be '
    '5% + 8% = 13%. If you were paying $100,000 COP, the new cost would be '
    '$113,000 COP (a $13,000 increase).'
)


def _is_legacy(note):
    if not isinstance(note, str) or not note:
        return False
    low = note.lower()
    return ('6%' in note and '8%' not in note
            and ('smlmv' in low or 'minimum wage' in low))


def fix_renewal_notes(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    qs = ProposalSection.objects.filter(section_type='investment')
    for section in qs.iterator():
        cj = section.content_json
        if not isinstance(cj, dict):
            continue
        hp = cj.get('hostingPlan')
        if not isinstance(hp, dict):
            continue
        if not _is_legacy(hp.get('renewalNote')):
            continue
        lang = getattr(getattr(section, 'proposal', None), 'language', 'es') or 'es'
        hp['renewalNote'] = RENEWAL_EN if lang == 'en' else RENEWAL_ES
        section.content_json = cj
        section.save(update_fields=['content_json'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0125_businessproposal_hosting_discount_annual'),
    ]

    operations = [
        migrations.RunPython(fix_renewal_notes, noop_reverse),
    ]

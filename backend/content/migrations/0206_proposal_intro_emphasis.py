from django.db import migrations


TARGET_SLUG = 'ramon-emiliani'

FIELD_REPLACEMENTS = {
    'executive_summary': {
        'paragraphs': (
            (
                'ProjectApp propone diseñar, desarrollar e implementar para <b>Airavata</b>, con <b>Aerocivil</b> como entidad beneficiaria, un <b>visor meteorológico aeronáutico de acceso público</b> que convierta información técnica en una experiencia cartográfica clara, fluida y verificable.',
                'ProjectApp propone diseñar, desarrollar e implementar para <b>Airavata, con Aerocivil como entidad beneficiaria</b>, un <b>visor meteorológico aeronáutico de acceso público</b> que convierta información técnica en una experiencia cartográfica clara, fluida y verificable.',
            ),
            (
                'El resultado será un producto web responsive, sin registro, inicio de sesión, roles ni administración. La inversión cubre levantamiento, diseño, construcción, hasta ocho cupos de integración delimitados, QA, UAT, dos despliegues y transferencia técnica.',
                'El resultado será un <b>producto web responsive, sin registro, inicio de sesión, roles ni administración</b>. La inversión cubre <b>levantamiento, diseño, construcción, hasta ocho cupos de integración delimitados, QA, UAT, dos despliegues y transferencia técnica</b>.',
            ),
        ),
    },
    'roi_projection': {
        'subtitle': (
            (
                'Indicadores verificables del producto, sin atribuir retornos financieros no sustentados.',
                '<b>Indicadores verificables del producto</b>, sin atribuir retornos financieros no sustentados.',
            ),
        ),
    },
    'design_ux': {
        'paragraphs': (
            (
                'El mapa ocupará el área útil y los controles aparecerán mediante overlays compactos. La propuesta no incluye un dashboard administrativo, perfiles, sesiones ni gestores de contenido.',
                'El <b>mapa ocupará el área útil</b> y los controles aparecerán mediante overlays compactos. La propuesta <b>no incluye un dashboard administrativo, perfiles, sesiones ni gestores de contenido</b>.',
            ),
            (
                'La referencia de Windy se limita a principios de interacción. La identidad, los componentes y el conjunto funcional serán los descritos en los requerimientos de esta propuesta.',
                'La referencia de Windy se limita a <b>principios de interacción</b>. La identidad, los componentes y el conjunto funcional serán <b>los descritos en los requerimientos de esta propuesta</b>.',
            ),
            (
                'Cada estado tendrá tratamiento explícito: carga, ausencia de cobertura, dato vencido, fuente no disponible, WebGL degradado y recuperación localizada.',
                'Cada estado tendrá <b>tratamiento explícito</b>: carga, ausencia de cobertura, dato vencido, fuente no disponible, WebGL degradado y recuperación localizada.',
            ),
        ),
    },
    'creative_support': {
        'paragraphs': (
            (
                'El acompañamiento cubre la traducción de necesidades meteorológicas y aeronáuticas a flujos digitales, no la validación científica de los datos ni la certificación operacional de la plataforma.',
                'El acompañamiento cubre la <b>traducción de necesidades meteorológicas y aeronáuticas a flujos digitales</b>, no la validación científica de los datos ni la certificación operacional de la plataforma.',
            ),
        ),
    },
    'development_stages': {
        'intro': (
            (
                'El proyecto avanza mediante hitos verificables y aprobaciones consolidadas:',
                'El proyecto avanza mediante <b>hitos verificables y aprobaciones consolidadas</b>:',
            ),
        ),
    },
}


def _replace_exact(value, replacements, *, reverse=False):
    pairs = ((after, before) for before, after in replacements) if reverse else replacements
    replacements_by_value = dict(pairs)
    if isinstance(value, list):
        return [replacements_by_value.get(item, item) for item in value]
    return replacements_by_value.get(value, value)


def _update_ramon_intro_emphasis(apps, *, reverse=False):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    proposal = BusinessProposal.objects.filter(slug=TARGET_SLUG).first()
    if proposal is None:
        return

    sections = ProposalSection.objects.filter(
        proposal_id=proposal.pk,
        section_type__in=FIELD_REPLACEMENTS,
    )
    for section in sections.iterator():
        content = dict(section.content_json or {})
        updated_content = dict(content)
        for field_name, replacements in FIELD_REPLACEMENTS[section.section_type].items():
            if field_name not in content:
                continue
            updated_content[field_name] = _replace_exact(
                content.get(field_name), replacements, reverse=reverse,
            )
        if updated_content != content:
            section.content_json = updated_content
            section.save(update_fields=['content_json'])


def add_ramon_intro_emphasis(apps, schema_editor):
    _update_ramon_intro_emphasis(apps)


def remove_ramon_intro_emphasis(apps, schema_editor):
    _update_ramon_intro_emphasis(apps, reverse=True)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0205_merge_contract_terms_and_client_communication'),
    ]

    operations = [
        migrations.RunPython(
            add_ramon_intro_emphasis,
            remove_ramon_intro_emphasis,
        ),
    ]

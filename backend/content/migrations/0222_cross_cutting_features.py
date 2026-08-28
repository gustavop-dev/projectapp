from copy import deepcopy

from django.db import migrations


GROUP_ID = 'cross_cutting_features'
LEGACY_RESPONSIVE_IDS = {
    'item-features-diseno-responsive',
    'item-features-responsive-design',
}
LEGACY_RESPONSIVE_NAMES = {
    'diseño responsive',
    'responsive design',
}


GROUPS = {
    'es': {
        'id': GROUP_ID,
        'icon': '🔗',
        'title': 'Funcionalidades Transversales',
        'is_visible': True,
        'selected': True,
        'price_percent': 0,
        'description': (
            'Capacidades de calidad que atraviesan varias vistas, componentes y flujos. '
            'Este catálogo es un punto de partida: debe adaptarse al negocio, la etapa '
            'del producto y el alcance real de cada propuesta.'
        ),
        'items': [
            {
                'id': 'item-cross_cutting_features-diseno-responsive',
                'icon': '📱',
                'name': 'Diseño Responsive',
                'description': (
                    'La experiencia se adapta a los tamaños de pantalla y formas de '
                    'interacción definidos para el proyecto, priorizando los dispositivos '
                    'relevantes para sus usuarios.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-accesibilidad',
                'icon': '♿',
                'name': 'Accesibilidad',
                'description': (
                    'La interfaz contempla navegación, contraste, etiquetas y estados '
                    'comprensibles según el público y el nivel de accesibilidad acordado.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-usabilidad-consistente',
                'icon': '🧭',
                'name': 'Usabilidad Consistente',
                'description': (
                    'Los patrones de interacción y retroalimentación se mantienen coherentes '
                    'entre las vistas y los flujos incluidos en el alcance.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-rendimiento',
                'icon': '⚡',
                'name': 'Rendimiento',
                'description': (
                    'Las pantallas y los recursos se optimizan para ofrecer tiempos de '
                    'respuesta adecuados al contenido, tráfico y dispositivos esperados.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-seguridad',
                'icon': '🛡️',
                'name': 'Seguridad',
                'description': (
                    'Los accesos, formularios y operaciones sensibles aplican controles '
                    'proporcionales a los riesgos y roles definidos para el proyecto.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-privacidad-de-datos',
                'icon': '🔒',
                'name': 'Privacidad de Datos',
                'description': (
                    'La captura, el uso y la conservación de datos se limitan a lo necesario '
                    'y se ajustan a las obligaciones aplicables al negocio.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-compatibilidad-entre-navegadores',
                'icon': '🌐',
                'name': 'Compatibilidad entre Navegadores',
                'description': (
                    'La experiencia se valida en los navegadores y versiones acordados según '
                    'la audiencia y las condiciones reales de uso.'
                ),
            },
        ],
    },
    'en': {
        'id': GROUP_ID,
        'icon': '🔗',
        'title': 'Cross-cutting Features',
        'is_visible': True,
        'selected': True,
        'price_percent': 0,
        'description': (
            'Quality capabilities that span multiple views, components, and flows. '
            'This catalog is a starting point and must be adapted to the business, '
            'product stage, and actual scope of each proposal.'
        ),
        'items': [
            {
                'id': 'item-cross_cutting_features-responsive-design',
                'icon': '📱',
                'name': 'Responsive Design',
                'description': (
                    'The experience adapts to the screen sizes and interaction modes defined '
                    'for the project, prioritizing the devices relevant to its users.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-accessibility',
                'icon': '♿',
                'name': 'Accessibility',
                'description': (
                    'The interface considers navigation, contrast, labels, and understandable '
                    'states according to the audience and agreed accessibility level.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-consistent-usability',
                'icon': '🧭',
                'name': 'Consistent Usability',
                'description': (
                    'Interaction and feedback patterns remain coherent across the views and '
                    'flows included in scope.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-performance',
                'icon': '⚡',
                'name': 'Performance',
                'description': (
                    'Screens and resources are optimized for response times appropriate to '
                    'the expected content, traffic, and devices.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-security',
                'icon': '🛡️',
                'name': 'Security',
                'description': (
                    'Access, forms, and sensitive operations apply controls proportional to '
                    'the risks and roles defined for the project.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-data-privacy',
                'icon': '🔒',
                'name': 'Data Privacy',
                'description': (
                    'Data collection, use, and retention are limited to what is necessary and '
                    'aligned with the obligations applicable to the business.'
                ),
            },
            {
                'id': 'item-cross_cutting_features-cross-browser-compatibility',
                'icon': '🌐',
                'name': 'Cross-browser Compatibility',
                'description': (
                    'The experience is validated in the browsers and versions agreed according '
                    'to the audience and real usage conditions.'
                ),
            },
        ],
    },
}


def _find_functional_requirements(sections):
    for section in sections or []:
        if (
            isinstance(section, dict)
            and section.get('section_type') == 'functional_requirements'
        ):
            return section.get('content_json')
    return None


def _is_legacy_responsive(item):
    if not isinstance(item, dict):
        return False
    item_id = str(item.get('id') or '').strip()
    name = str(item.get('name') or '').strip().casefold()
    return item_id in LEGACY_RESPONSIVE_IDS or name in LEGACY_RESPONSIVE_NAMES


def add_cross_cutting_group(content_json, language):
    """Insert the new group once and move the legacy responsive item into it."""
    if not isinstance(content_json, dict):
        return False
    groups = content_json.get('groups')
    if not isinstance(groups, list):
        return False
    if any(isinstance(group, dict) and group.get('id') == GROUP_ID for group in groups):
        return False

    template = deepcopy(GROUPS['en' if language == 'en' else 'es'])
    insert_at = len(groups)

    for index, group in enumerate(groups):
        if not isinstance(group, dict) or group.get('id') != 'features':
            continue
        insert_at = index + 1
        items = group.get('items')
        if not isinstance(items, list):
            break
        responsive_index = next(
            (item_index for item_index, item in enumerate(items) if _is_legacy_responsive(item)),
            None,
        )
        if responsive_index is not None:
            responsive = deepcopy(items.pop(responsive_index))
            if not str(responsive.get('id') or '').strip():
                responsive['id'] = template['items'][0]['id']
            template['items'][0] = responsive
        break

    groups.insert(insert_at, template)
    return True


def add_cross_cutting_features(apps, schema_editor):
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    for config in ProposalDefaultConfig.objects.all().iterator():
        sections = deepcopy(config.sections_json)
        content_json = _find_functional_requirements(sections)
        if add_cross_cutting_group(content_json, config.language):
            config.sections_json = sections
            config.save(update_fields=['sections_json'])

    draft_sections = ProposalSection.objects.filter(
        proposal__status='draft',
        proposal__is_active=True,
        section_type='functional_requirements',
    ).select_related('proposal')
    for section in draft_sections.iterator():
        content_json = deepcopy(section.content_json)
        if add_cross_cutting_group(content_json, section.proposal.language):
            section.content_json = content_json
            section.save(update_fields=['content_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0221_merge_dependency_updates_recurring_lifecycle'),
    ]

    operations = [
        migrations.RunPython(
            add_cross_cutting_features,
            migrations.RunPython.noop,
        ),
    ]

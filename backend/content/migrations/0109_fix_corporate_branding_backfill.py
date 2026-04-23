from django.db import migrations


MODULE_ID = 'corporate_branding_module'
AI_MODULE_ID = 'ai_module'
FR_SECTION_TYPE = 'functional_requirements'


CORPORATE_BRANDING_ES = {
    'id': 'corporate_branding_module',
    'icon': '🎨',
    'title': 'Identidad Visual e Imagen Corporativa',
    'is_visible': True,
    'description': (
        'Aplicamos tu identidad visual de forma consistente en cada punto de contacto del '
        'sistema — correos, documentos, redes sociales y pantallas internas — para que tu '
        'marca se perciba profesional y coherente en todo lugar donde tus clientes interactúan.'
    ),
    'is_calculator_module': True,
    'default_selected': False,
    'selected': False,
    'price_percent': 35,
    'items': [
        {'icon': '✉️', 'name': 'Correos transaccionales con identidad corporativa', 'description': 'Plantillas HTML con logo, colores, tipografía y firma de marca aplicadas en todos los correos del sistema — bienvenida, confirmaciones, alertas, recuperación de contraseña y notificaciones — en lugar de correos en texto plano o genéricos.'},
        {'icon': '📄', 'name': 'PDFs y exportables con branding', 'description': 'Facturas, reportes, certificados, recibos y descargas Excel/CSV generados desde el sistema con encabezado con logo, paleta corporativa y pie de marca. Cada documento que sale de la plataforma refuerza la imagen profesional del negocio.'},
        {'icon': '🔗', 'name': 'Tarjetas de previsualización en redes (Open Graph)', 'description': 'Cuando alguien comparte un link del sitio o una propuesta en WhatsApp, Facebook, LinkedIn o X, aparece una tarjeta con logo, imagen y colores de marca — no un link plano. Impacto directo en percepción y CTR.'},
        {'icon': '🖥️', 'name': 'Pantallas del sistema con identidad de marca', 'description': 'Páginas de error (404, 500), mantenimiento, login y estados de carga (loading, skeletons) con identidad visual y mensajes en la voz de la marca, en vez de las pantallas genéricas del framework.'},
        {'icon': '🔎', 'name': 'Metadatos estructurados para buscadores e IA', 'description': 'JSON-LD Organization con logo, colores, redes sociales y datos de contacto — para que Google, Bing y asistentes como ChatGPT o Perplexity muestren correctamente la marca en panel de conocimiento, resultados enriquecidos y citaciones.'},
    ],
}


CORPORATE_BRANDING_EN = {
    'id': 'corporate_branding_module',
    'icon': '🎨',
    'title': 'Visual Identity & Corporate Branding',
    'is_visible': True,
    'description': (
        'We apply your visual identity consistently across every system touchpoint — emails, '
        'documents, social previews and internal screens — so your brand feels professional and '
        'coherent everywhere your customers interact with it.'
    ),
    'is_calculator_module': True,
    'default_selected': False,
    'selected': False,
    'price_percent': 35,
    'items': [
        {'icon': '✉️', 'name': 'Branded Transactional Emails', 'description': 'HTML templates with logo, colors, typography and brand signature applied across all system emails — welcome, confirmations, alerts, password recovery and notifications — instead of plain-text or generic messages.'},
        {'icon': '📄', 'name': 'PDFs & Exports with Branding', 'description': 'Invoices, reports, certificates, receipts and Excel/CSV downloads generated from the system with branded headers, corporate color palette and brand footers. Every document that leaves the platform reinforces the business\'s professional image.'},
        {'icon': '🔗', 'name': 'Social Link Preview Cards (Open Graph)', 'description': 'When someone shares a link to the site or a proposal on WhatsApp, Facebook, LinkedIn or X, a card with logo, image and brand colors appears — not a plain link. Direct impact on perception and CTR.'},
        {'icon': '🖥️', 'name': 'System Screens with Brand Identity', 'description': 'Error pages (404, 500), maintenance, login and loading states (skeletons, spinners) with visual identity and messaging in the brand\'s voice, instead of the framework\'s generic screens.'},
        {'icon': '🔎', 'name': 'Structured Metadata for Search & AI', 'description': 'JSON-LD Organization with logo, colors, social profiles and contact data — so Google, Bing and assistants like ChatGPT or Perplexity correctly display the brand in knowledge panels, enriched results and citations.'},
    ],
}


def _module_for(language):
    return CORPORATE_BRANDING_EN if language == 'en' else CORPORATE_BRANDING_ES


def _insert_before_ai_module(modules, new_module):
    if any(m.get('id') == MODULE_ID for m in modules):
        return modules, False
    ai_idx = next(
        (i for i, m in enumerate(modules) if m.get('id') == AI_MODULE_ID),
        None,
    )
    if ai_idx is None:
        modules.append(new_module)
    else:
        modules.insert(ai_idx, new_module)
    return modules, True


def add_branding_to_functional_requirements(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')

    fr_sections = list(
        ProposalSection.objects.filter(section_type=FR_SECTION_TYPE)
    )
    if fr_sections:
        proposal_ids = {s.proposal_id for s in fr_sections}
        proposal_lang = {
            p.pk: (getattr(p, 'language', 'es') or 'es')
            for p in BusinessProposal.objects.filter(pk__in=proposal_ids).only('id', 'language')
        }

        to_update = []
        for section in fr_sections:
            content = section.content_json or {}
            additional = list(content.get('additionalModules') or [])
            lang = proposal_lang.get(section.proposal_id, 'es')
            module = _module_for(lang)
            additional, changed = _insert_before_ai_module(additional, module)
            if changed:
                content['additionalModules'] = additional
                section.content_json = content
                to_update.append(section)

        if to_update:
            ProposalSection.objects.bulk_update(to_update, ['content_json'], batch_size=100)

    for cfg in ProposalDefaultConfig.objects.all():
        sections = cfg.sections_json or []
        if not sections:
            continue
        language = getattr(cfg, 'language', 'es') or 'es'
        changed = False
        for section in sections:
            if section.get('section_type') != FR_SECTION_TYPE:
                continue
            content = section.get('content_json') or {}
            additional = list(content.get('additionalModules') or [])
            module = _module_for(language)
            additional, modified = _insert_before_ai_module(additional, module)
            if modified:
                content['additionalModules'] = additional
                section['content_json'] = content
                changed = True
        if changed:
            cfg.sections_json = sections
            cfg.save(update_fields=['sections_json'])


def remove_branding_from_functional_requirements(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')

    to_update = []
    for section in ProposalSection.objects.filter(section_type=FR_SECTION_TYPE):
        content = section.content_json or {}
        additional = content.get('additionalModules') or []
        filtered = [m for m in additional if m.get('id') != MODULE_ID]
        if len(filtered) != len(additional):
            content['additionalModules'] = filtered
            section.content_json = content
            to_update.append(section)
    if to_update:
        ProposalSection.objects.bulk_update(to_update, ['content_json'], batch_size=100)

    for cfg in ProposalDefaultConfig.objects.all():
        sections = cfg.sections_json or []
        changed = False
        for section in sections:
            if section.get('section_type') != FR_SECTION_TYPE:
                continue
            content = section.get('content_json') or {}
            additional = content.get('additionalModules') or []
            filtered = [m for m in additional if m.get('id') != MODULE_ID]
            if len(filtered) != len(additional):
                content['additionalModules'] = filtered
                section['content_json'] = content
                changed = True
        if changed:
            cfg.sections_json = sections
            cfg.save(update_fields=['sections_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0108_corporate_branding_module'),
    ]

    operations = [
        migrations.RunPython(
            add_branding_to_functional_requirements,
            remove_branding_from_functional_requirements,
        ),
    ]

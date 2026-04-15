import copy

from django.db import migrations


def _string_id(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return value.strip()


def _unique_strings(values):
    seen = set()
    out = []
    for raw in values:
        value = _string_id(raw)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _build_proposal_module_link_catalog(sections):
    options = []
    alias_map = {}

    if not isinstance(sections, list):
        return {'options': options, 'alias_map': alias_map}

    def add_option(option):
        options.append(option)
        for alias in option.get('aliases', []):
            alias_map[alias] = option['id']

    fr = next(
        (section for section in sections if section.get('section_type') == 'functional_requirements'),
        None,
    )
    inv = next(
        (section for section in sections if section.get('section_type') == 'investment'),
        None,
    )
    content_json = fr.get('content_json') if isinstance(fr, dict) else {}
    groups = []
    if isinstance(content_json, dict):
        groups.extend(content_json.get('groups') or [])
        groups.extend(content_json.get('additionalModules') or [])

    for group in groups:
        if not isinstance(group, dict) or group.get('is_visible') is False:
            continue
        raw_id = _string_id(group.get('id'))
        if not raw_id:
            continue
        if not group.get('title') and not (group.get('items') or []):
            continue
        is_calc = group.get('is_calculator_module') is True
        canonical_id = f'module-{raw_id}' if is_calc else f'group-{raw_id}'
        add_option({
            'id': canonical_id,
            'aliases': _unique_strings([canonical_id, raw_id]),
        })

    inv_content = inv.get('content_json') if isinstance(inv, dict) else {}
    modules = inv_content.get('modules') if isinstance(inv_content, dict) else []
    for module in modules or []:
        if not isinstance(module, dict):
            continue
        module_id = _string_id(module.get('id'))
        if not module_id:
            continue
        add_option({
            'id': module_id,
            'aliases': [module_id],
        })

    return {'options': options, 'alias_map': alias_map}


def _normalize_linked_module_ids(raw, alias_map=None):
    alias_map = alias_map or {}
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = raw
    else:
        values = []
    return _unique_strings([
        alias_map.get(_string_id(value), _string_id(value))
        for value in values
    ])


def _normalize_technical_document_module_links(content_json, sections):
    if not isinstance(content_json, dict):
        return {}

    catalog = _build_proposal_module_link_catalog(sections)
    alias_map = catalog['alias_map']
    out = copy.deepcopy(content_json)
    epics = out.get('epics')
    if not isinstance(epics, list):
        return out

    normalized_epics = []
    for epic in epics:
        if not isinstance(epic, dict):
            continue
        normalized_epic = copy.deepcopy(epic)
        normalized_epic.pop('linkedModuleIds', None)
        normalized_epic['linked_module_ids'] = _normalize_linked_module_ids(
            epic.get('linked_module_ids') or epic.get('linkedModuleIds'),
            alias_map,
        )
        requirements = epic.get('requirements')
        if isinstance(requirements, list):
            normalized_requirements = []
            for requirement in requirements:
                if not isinstance(requirement, dict):
                    continue
                normalized_requirement = copy.deepcopy(requirement)
                normalized_requirement.pop('linkedModuleIds', None)
                normalized_requirement['linked_module_ids'] = _normalize_linked_module_ids(
                    requirement.get('linked_module_ids') or requirement.get('linkedModuleIds'),
                    alias_map,
                )
                normalized_requirements.append(normalized_requirement)
            normalized_epic['requirements'] = normalized_requirements
        normalized_epics.append(normalized_epic)

    out['epics'] = normalized_epics
    return out


def _process_proposal_sections(section_rows, ProposalSection, db_alias):
    if not section_rows:
        return 0

    section_payloads = [
        {
            'section_type': section.section_type,
            'content_json': (
                copy.deepcopy(section.content_json)
                if isinstance(section.content_json, dict)
                else {}
            ),
        }
        for section in section_rows
    ]
    updated = 0

    for index, section in enumerate(section_rows):
        if section.section_type != 'technical_document':
            continue

        current_content = section_payloads[index]['content_json']
        normalized = _normalize_technical_document_module_links(
            current_content,
            section_payloads,
        )
        if normalized == current_content:
            continue

        ProposalSection.objects.using(db_alias).filter(pk=section.pk).update(
            content_json=normalized,
        )
        section_payloads[index]['content_json'] = copy.deepcopy(normalized)
        updated += 1

    return updated


def forwards(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    db_alias = schema_editor.connection.alias

    current_proposal_id = None
    buffered_sections = []

    queryset = ProposalSection.objects.using(db_alias).order_by(
        'proposal_id', 'order', 'id',
    ).iterator(chunk_size=200)

    for section in queryset:
        if current_proposal_id is None:
            current_proposal_id = section.proposal_id

        if section.proposal_id != current_proposal_id:
            _process_proposal_sections(buffered_sections, ProposalSection, db_alias)
            buffered_sections = []
            current_proposal_id = section.proposal_id

        buffered_sections.append(section)

    _process_proposal_sections(buffered_sections, ProposalSection, db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0084_fix_shared_email_client_profiles'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]

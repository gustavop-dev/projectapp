"""Markdown blocks derived exclusively from the curated formal PDF inputs."""
from content.services.formalization_content import formal_document_title, rows, text


def formal_document_blocks(content, kind):
    formal_document_title(content, kind)
    blocks = _commercial_blocks(content) if kind == 'commercial' else _technical_blocks(content)
    return [block for block in blocks if block['paragraphs'] or block['rows']]


def _commercial_blocks(content):
    """Retain saved section order without rereading raw proposal fields."""
    label = content.label
    blocks = []
    for section in content.commercial():
        data = section.content_json
        title = section.title
        kind = section.section_type
        if kind == 'functional_requirements':
            scope = [
                {**item, 'module': group['title']}
                for group in data['groups'] for item in group['items']
            ]
            blocks.append(content.table(title, scope, [
                ('module', label('Módulo', 'Module')), ('id', 'ID'),
                ('name', label('Entregable', 'Deliverable')),
                ('description', label('Descripción', 'Description')),
            ], [data['intro']]))
        elif kind == 'design_ux':
            blocks.append(content.block(title, data['focusItems']))
        elif kind == 'creative_support':
            blocks.append(content.block(title, data['includes']))
        elif kind == 'timeline':
            blocks.append(content.table(title, data['phases'], [
                ('title', label('Fase', 'Phase')), ('duration', label('Duración', 'Duration')),
                ('description', label('Actividades', 'Activities')),
                ('tasks', label('Tareas', 'Tasks')), ('milestone', label('Hito', 'Milestone')),
            ], [data['totalDuration']]))
        elif kind == 'process_methodology':
            blocks.append(content.table(title, data['steps'], [
                ('title', label('Etapa', 'Stage')), ('description', label('Actividad', 'Activity')),
                ('clientAction', label('Aporte del cliente', 'Client input')),
            ]))
        elif kind == 'development_stages':
            blocks.append(content.table(title, data['stages'], [
                ('title', label('Etapa', 'Stage')), ('description', label('Actividad', 'Activity')),
            ]))
        elif kind == 'investment':
            resolved = data['resolved']
            blocks.append(content.block(title, [resolved['total'] + resolved['tax']]))
            blocks.append(content.table(label('Hitos de pago', 'Payment milestones'), resolved['payments'], [
                ('milestone', label('Hito', 'Milestone')), ('amount', label('Importe', 'Amount')),
            ], [resolved['paymentMethods'], resolved['paymentNote']]))
            blocks.extend(resolved['hosting'])
        elif kind == 'value_added_modules':
            blocks.extend({**block, 'title': f"{title} · {block['title']}"} for block in data['terms'])
        elif kind == 'commercial_conditions':
            blocks.append(content.block(title, [*data['scopeParagraphs'], data['contractNote']]))
    return blocks


def _technical_blocks(content):
    d = content.technical()
    l = content.label
    blocks = [content.block(l('Propósito', 'Purpose'), [d.get('purpose')])]
    def add(es, en, source, fields, paragraphs=()):
        blocks.append(content.table(l(es, en), source, [(key, l(eslabel, enlabel)) for key, eslabel, enlabel in fields], paragraphs))
    add('Stack tecnológico', 'Technology stack', d.get('stack'), [('layer', 'Capa', 'Layer'), ('technology', 'Tecnología', 'Technology'), ('rationale', 'Justificación', 'Rationale')])
    arch = d.get('architecture') or {}
    add('Arquitectura', 'Architecture', arch.get('patterns'), [('component', 'Componente', 'Component'), ('pattern', 'Patrón', 'Pattern'), ('description', 'Descripción', 'Description')], [arch.get('summary'), arch.get('diagramNote')])
    model = d.get('dataModel') or {}
    add('Modelo de datos', 'Data model', model.get('entities'), [('name', 'Entidad', 'Entity'), ('description', 'Descripción', 'Description'), ('keyFields', 'Campos clave', 'Key fields')], [model.get('summary'), model.get('relationships')])
    growth = d.get('growthReadiness') or {}
    add('Preparación técnica incluida', 'Included technical preparation', growth.get('strategies'), [('dimension', 'Dimensión', 'Dimension'), ('preparation', 'Implementación actual', 'Current implementation')])
    for epic in rows(d.get('epics')):
        title = ' · '.join(filter(None, [text(epic.get('epicKey')), text(epic.get('title'))]))
        add(title, title, epic.get('requirements'), [('flowKey', 'ID', 'ID'), ('title', 'Requerimiento', 'Requirement'), ('description', 'Descripción', 'Description'), ('configuration', 'Configuración', 'Configuration'), ('usageFlow', 'Flujo', 'Flow'), ('linked_item_ids', 'Referencia comercial', 'Commercial reference')], [epic.get('description')])
    add('API', 'API', d.get('apiDomains'), [('domain', 'Dominio', 'Domain'), ('summary', 'Responsabilidad', 'Responsibility')], [d.get('apiSummary')])
    integ = d.get('integrations') or {}
    add('Integraciones incluidas', 'Included integrations', integ.get('included'), [('service', 'Servicio', 'Service'), ('provider', 'Proveedor', 'Provider'), ('connection', 'Conexión', 'Connection'), ('dataExchange', 'Datos', 'Data'), ('accountOwner', 'Titular', 'Account owner')], [integ.get('notes')])
    add('Integraciones excluidas', 'Excluded integrations', integ.get('excluded'), [('service', 'Servicio', 'Service'), ('reason', 'Motivo', 'Reason')])
    # URLs/database names and arbitrary credentials are deliberately not projected.
    add('Ambientes', 'Environments', d.get('environments'), [('name', 'Nombre', 'Name'), ('purpose', 'Propósito', 'Purpose'), ('whoAccesses', 'Roles con acceso', 'Access roles')])
    add('Seguridad', 'Security', d.get('security'), [('aspect', 'Aspecto', 'Aspect'), ('implementation', 'Implementación', 'Implementation')])
    perf = d.get('performanceQuality') or {}
    add('Rendimiento', 'Performance', perf.get('metrics'), [('metric', 'Métrica', 'Metric'), ('target', 'Objetivo', 'Target'), ('howMeasured', 'Medición', 'Measurement')])
    add('Prácticas de rendimiento', 'Performance practices', perf.get('practices'), [('strategy', 'Estrategia', 'Strategy'), ('description', 'Descripción', 'Description')])
    blocks.append(content.block(l('Respaldos', 'Backups'), [d.get('backupsNote')]))
    quality = d.get('quality') or {}
    add('Calidad y aceptación', 'Quality and acceptance', quality.get('dimensions'), [('dimension', 'Dimensión', 'Dimension'), ('evaluates', 'Evaluación', 'Evaluation'), ('standard', 'Estándar', 'Standard')], [quality.get('criticalFlowsNote')])
    add('Pruebas', 'Tests', quality.get('testTypes'), [('type', 'Tipo', 'Type'), ('validates', 'Valida', 'Validates'), ('tool', 'Herramienta', 'Tool'), ('whenRun', 'Momento', 'When')])
    add('Decisiones técnicas', 'Technical decisions', d.get('decisions'), [('decision', 'Decisión', 'Decision'), ('alternative', 'Alternativa evaluada', 'Considered alternative'), ('reason', 'Justificación', 'Rationale')])
    return blocks

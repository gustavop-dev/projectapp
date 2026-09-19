"""Explicit, deterministic projection of proposal data into formal annexes.

No public renderer or catalog refresh runs here. Unknown fields and sales
sections cannot enter the documents through a generic raw-text fallback.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import re

from content.services.proposal_pdf_service import default_selected_modules_from_content
from content.services.proposal_module_links import ensure_functional_requirements_item_ids
from content.services.proposal_totals_service import effective_total_for_proposal, safe_decimal
from content.services.technical_document_filter import get_filtered_technical_document


class FormalizationError(ValueError):
    def __init__(self, message, code='invalid_formalization', status=400):
        super().__init__(message)
        self.code = code
        self.status = status


def rows(value):
    return [item for item in value or [] if isinstance(item, dict)]


def text(value):
    if isinstance(value, list):
        return '\n'.join(text(item) for item in value)
    return str(value or '').strip()


class FormalContent:
    """One captured proposal supplies scope and money to both documents."""

    def __init__(self, proposal):
        self.proposal = proposal
        self.sections = [
            {'section_type': sec.section_type, 'content_json': deepcopy(sec.content_json or {})}
            for sec in proposal.sections.all() if sec.is_enabled
        ]
        for section in self.sections:
            if section['section_type'] == 'functional_requirements':
                section['content_json'] = ensure_functional_requirements_item_ids(section['content_json'])
        self.data = {sec['section_type']: sec['content_json'] for sec in self.sections}
        self.selected = default_selected_modules_from_content(proposal)
        self.total = effective_total_for_proposal(proposal)
        # Legacy priced items are subtractive; calculator modules are additive.
        for module in rows(self.data.get('investment', {}).get('modules')):
            if module.get('id') not in self.selected:
                self.total -= safe_decimal(module.get('price'))
        fr = self.data.get('functional_requirements', {})
        for group in rows(fr.get('groups')) + rows(fr.get('additionalModules')):
            gid = group.get('id') or group.get('title') or ''
            for item in rows(group.get('items')):
                fid = re.sub(r'\s+', '-', f"fr-{gid}-{item.get('name', '')}").lower()
                if item.get('is_required') is not True and fid not in self.selected:
                    self.total -= safe_decimal(item.get('price'))
        self.currency = proposal.currency or 'COP'
        self.english = proposal.language == 'en'

    def label(self, es, en):
        return en if self.english else es

    def money(self, value):
        amount = safe_decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        formatted = f'{amount:,.2f}'
        if not self.english:
            formatted = formatted.translate(str.maketrans(',.', '.,'))
        return f'{formatted} {self.currency}'

    def structured(self, key):
        data = self.data.get(key, {})
        if data.get('_editMode') == 'paste' and data.get('rawText'):
            raise FormalizationError(
                f'Completa los campos estructurados de {key}; el texto pegado no se incluye en la formalización.',
                'unstructured_content',
            )
        return data

    def table(self, title, source, columns, paragraphs=()):
        return {
            'title': title,
            'paragraphs': [text(p) for p in paragraphs if text(p)],
            'headers': [label for _, label in columns],
            'rows': [[text(item.get(key)) for key, _ in columns] for item in rows(source)],
        }

    def block(self, title, paragraphs):
        return self.table(title, [], [], paragraphs)

    def technical_data(self):
        data = self.structured('technical_document')
        if not data:
            raise FormalizationError('Completa y habilita el detalle técnico.', 'technical_missing')
        filtered = get_filtered_technical_document(data, self.sections, self.selected)
        if not any(epic.get('requirements') for epic in rows(filtered.get('epics'))):
            raise FormalizationError('El detalle técnico necesita requerimientos del alcance seleccionado.', 'technical_scope_missing')
        return filtered

    def scope(self):
        data = self.structured('functional_requirements')
        included = []
        for group in rows(data.get('groups')) + rows(data.get('additionalModules')):
            gid = text(group.get('id') or group.get('title'))
            if group.get('is_visible') is False:
                continue
            if group.get('is_calculator_module') and f'module-{gid}' not in self.selected:
                continue
            if group in rows(data.get('additionalModules')) and not group.get('is_calculator_module'):
                if f'group-{gid}' not in self.selected and f'module-{gid}' not in self.selected:
                    continue
            if group.get('_editMode') == 'paste' and group.get('rawText'):
                raise FormalizationError(f'Completa los items estructurados de {gid}.', 'unstructured_content')
            for item in rows(group.get('items')):
                configurable = item.get('price') or item.get('is_required') is False
                fid = re.sub(r'\s+', '-', f"fr-{gid}-{item.get('name', '')}").lower()
                if item.get('is_required') is not True and configurable and fid not in self.selected:
                    continue
                included.append({
                    'module': group.get('title') or gid,
                    'id': item.get('id') or fid,
                    'name': item.get('name'),
                    'description': item.get('description'),
                })
        if not included:
            raise FormalizationError('Completa y habilita el alcance funcional de la propuesta.', 'commercial_scope_missing')
        return included

    def commercial(self):
        inv = self.structured('investment')
        if not inv or self.total <= 0:
            raise FormalizationError('Completa la inversión de la propuesta.', 'investment_missing')
        payments = rows(inv.get('paymentOptions'))
        if not payments:
            raise FormalizationError('Completa los hitos de pago.', 'payments_missing')
        schedule = []
        for payment in payments:
            match = re.search(r'(\d+(?:[.,]\d+)?)\s*%', text(payment.get('label')))
            schedule.append({
                'milestone': payment.get('label'),
                'amount': self.money(self.total * Decimal(match[1].replace(',', '.')) / 100) if match else payment.get('description'),
            })
        blocks = [self.table(self.label('Alcance y entregables', 'Scope and deliverables'), self.scope(), [
            ('module', self.label('Módulo', 'Module')), ('id', 'ID'),
            ('name', self.label('Entregable', 'Deliverable')), ('description', self.label('Descripción', 'Description')),
        ], [self.label('Las especificaciones y criterios verificables se detallan en el anexo técnico de esta propuesta.', 'Specifications and verifiable criteria are detailed in the technical annex to this proposal.')])]
        design = self.structured('design_ux')
        creative = self.structured('creative_support')
        provisions = []
        for entry in design.get('focusItems') or []:
            provisions.append(text(entry.get('description') or entry.get('title')) if isinstance(entry, dict) else text(entry))
        for entry in creative.get('includes') or []:
            provisions.append(text(entry.get('description') or entry.get('title')) if isinstance(entry, dict) else text(entry))
        blocks.append(self.block(self.label('Diseño y acompañamiento incluidos', 'Included design and support'), provisions))
        timeline = self.structured('timeline')
        blocks.append(self.table(self.label('Cronograma', 'Schedule'), timeline.get('phases'), [
            ('title', self.label('Fase', 'Phase')), ('duration', self.label('Duración', 'Duration')),
            ('description', self.label('Actividades', 'Activities')), ('tasks', self.label('Tareas', 'Tasks')),
            ('milestone', self.label('Hito', 'Milestone')),
        ], [timeline.get('totalDuration')]))
        method = self.structured('process_methodology')
        blocks.append(self.table(self.label('Ejecución y aportes del cliente', 'Execution and client inputs'), method.get('steps'), [
            ('title', self.label('Etapa', 'Stage')), ('description', self.label('Actividad', 'Activity')),
            ('clientAction', self.label('Aporte del cliente', 'Client input')),
        ]))
        stages = self.structured('development_stages')
        if not method.get('steps'):
            blocks.append(self.table(self.label('Etapas de desarrollo', 'Development stages'), stages.get('stages'), [
                ('title', self.label('Etapa', 'Stage')), ('description', self.label('Actividad', 'Activity')),
            ]))
        tax = ' + IVA' if self.currency == 'COP' else ''
        blocks.append(self.block(self.label('Inversión', 'Investment'), [self.money(self.total) + tax]))
        blocks.append(self.table(self.label('Hitos de pago', 'Payment milestones'), schedule, [
            ('milestone', self.label('Hito', 'Milestone')), ('amount', self.label('Importe', 'Amount')),
        ], [text(inv.get('paymentMethods')), self.label('Los importes conservan el tratamiento tributario de la inversión.', 'Amounts follow the tax treatment of the investment.')]))
        blocks.extend(self.hosting(inv))
        blocks.extend(self.included_terms())
        conditions = self.structured('commercial_conditions')
        blocks.append(self.block(self.label('Límites y cambios de alcance', 'Scope limits and changes'), conditions.get('scopeParagraphs') or []))
        blocks.append(self.block(self.label('Condiciones contractuales', 'Contractual conditions'), [self.label('Las garantías y obligaciones se rigen por el contrato de desarrollo de software asociado a esta propuesta.', 'Warranties and obligations are governed by the software development contract associated with this proposal.')]))
        return blocks

    def included_terms(self):
        data = self.structured('value_added_modules')
        fr = self.structured('functional_requirements')
        catalog = {g.get('id'): g for g in rows(fr.get('groups')) + rows(fr.get('additionalModules'))}
        result = []
        for mid in data.get('module_ids') or []:
            module = catalog.get(mid)
            if not module or module.get('is_visible') is False:
                continue
            cond = (data.get('conditions') or {}).get(mid) or {}
            minimum = safe_decimal(cond.get('min_price_cop' if self.currency == 'COP' else 'min_price_usd'))
            if self.total < minimum:
                continue
            if module.get('is_calculator_module') and f'module-{mid}' not in self.selected:
                continue
            clauses = [text(c.get('label')) + ': ' + text(c.get('text')) for c in rows(cond.get('terms_clauses'))]
            if not clauses and cond.get('terms'):
                clauses = [text(cond['terms'])]
            if cond.get('duration_months'):
                clauses.insert(0, self.label('Meses de vigencia: ', 'Term in months: ') + text(cond['duration_months']))
            if cond.get('discretionary_note'):
                clauses.append(text(cond['discretionary_note']))
            result.append(self.block(self.label('Condiciones de ', 'Terms for ') + text(module.get('title') or mid), clauses))
        general = data.get('general_terms') or {}
        if result:
            result.append(self.block(self.label('Condiciones generales de los módulos incluidos', 'General terms for included modules'), [text(c.get('label')) + ': ' + text(c.get('text')) for c in rows(general.get('clauses'))]))
        return result

    def hosting(self, inv):
        hosting = inv.get('hostingPlan') or {}
        if not hosting.get('title'):
            return []
        # Freeze existing proposal terms; never reseed tiers or packages from catalogs.
        percent = self.proposal.hosting_percent
        if percent is None:
            percent = hosting.get('hostingPercent', 0)
        reference = self.total * safe_decimal(percent) / 100
        monthly = (reference / 12).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        tariffs = []
        for tier in rows(hosting.get('billingTiers')):
            months = safe_decimal(tier.get('months'))
            price = (monthly * (100 - safe_decimal(tier.get('discountPercent'))) / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if months > 0:
                tariffs.append({'period': tier.get('label') or str(months), 'amount': self.money(price * months)})
        if not tariffs:
            tariffs = [{'period': key, 'amount': hosting[key]} for key in ('monthlyPrice', 'annualPrice') if hosting.get(key)]
        paragraphs = [hosting.get('coverageNote'), hosting.get('renewalNote')]
        if hosting.get('freeMonthsVisible', bool(hosting.get('freeMonths'))) and hosting.get('freeMonths'):
            paragraphs.append(self.label('Meses incluidos sin costo: ', 'Included months at no charge: ') + text(hosting['freeMonths']))
        if len(tariffs) > 1:
            paragraphs.append(self.label('Modalidades disponibles; esta tabla no registra una elección de periodicidad.', 'Available billing options; this table does not record a selected billing period.'))
        return [self.table(self.label('Hosting, mantenimiento y soporte', 'Hosting, maintenance and support'), tariffs, [
            ('period', self.label('Periodicidad', 'Billing period')), ('amount', self.label('Importe por período', 'Amount per period')),
        ], paragraphs), self.table(self.label('Infraestructura incluida', 'Included infrastructure'), hosting.get('specs'), [
            ('label', self.label('Recurso', 'Resource')), ('value', self.label('Especificación', 'Specification')),
        ])]

    def technical(self):
        d = self.technical_data()
        l = self.label
        blocks = [self.block(l('Propósito', 'Purpose'), [d.get('purpose')])]
        def add(es, en, source, fields, paragraphs=()):
            blocks.append(self.table(l(es, en), source, [(key, l(eslabel, enlabel)) for key, eslabel, enlabel in fields], paragraphs))
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
        blocks.append(self.block(l('Respaldos', 'Backups'), [d.get('backupsNote')]))
        quality = d.get('quality') or {}
        add('Calidad y aceptación', 'Quality and acceptance', quality.get('dimensions'), [('dimension', 'Dimensión', 'Dimension'), ('evaluates', 'Evaluación', 'Evaluation'), ('standard', 'Estándar', 'Standard')], [quality.get('criticalFlowsNote')])
        add('Pruebas', 'Tests', quality.get('testTypes'), [('type', 'Tipo', 'Type'), ('validates', 'Valida', 'Validates'), ('tool', 'Herramienta', 'Tool'), ('whenRun', 'Momento', 'When')])
        add('Decisiones técnicas', 'Technical decisions', d.get('decisions'), [('decision', 'Decisión', 'Decision'), ('alternative', 'Alternativa evaluada', 'Considered alternative'), ('reason', 'Justificación', 'Rationale')])
        return blocks

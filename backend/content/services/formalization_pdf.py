"""Formal annex adapter: curated inputs, public proposal layout and assets."""
from dataclasses import dataclass, replace
from datetime import datetime

from content.services.formalization_content import FormalizationError, PdfSection, formal_document_title
from content.services.proposal_pdf_service import ProposalPdfService
from content.services.technical_document_pdf import generate_technical_document_pdf


@dataclass(frozen=True)
class FormalPdfContext:
    title: str
    reference: str
    issued_at: datetime
    project_title: str
    language: str
    content_start: int = 3
    sections: tuple = ()
    technical_data: dict | None = None

    def with_content_start(self, page):
        return replace(self, content_start=page)

    def label(self, value):
        return ENGLISH_LABELS.get(value, value) if self.language == 'en' else value

    @property
    def identity_lines(self):
        english = self.language == 'en'
        return (
            self.project_title,
            ('Reference: ' if english else 'Referencia: ') + self.reference,
            ('Issued: ' if english else 'Emisión: ') + self.issued_at.strftime('%Y-%m-%d %H:%M UTC'),
        )


def generate_formal_pdf(content, kind, issued_at, reference):
    title = formal_document_title(content, kind)
    sections = ()
    technical_data = None
    if kind == 'commercial':
        sections = (PdfSection('greeting', title, -1, {'clientName': content.proposal.client_name}), *content.commercial())
    else:
        technical_data = content.technical()
    context = FormalPdfContext(title, reference, issued_at, content.proposal.title, content.proposal.language, sections=sections, technical_data=technical_data)
    if kind == 'commercial':
        result = ProposalPdfService.generate(content.proposal, formal=context)
    else:
        result = generate_technical_document_pdf(content.proposal, formal=context)
    if not result:
        raise FormalizationError('No se pudo generar el documento formal. Intenta nuevamente.', 'pdf_generation_failed', 500)
    return result


# Only renderer-owned labels pass through this map; proposal prose stays intact.
ENGLISH_LABELS = {
    'ÍNDICE': 'CONTENTS', 'Contenido del documento': 'Document contents',
    'Propósito': 'Purpose', 'Stack tecnológico': 'Technology stack',
    'Capa': 'Layer', 'Tecnología': 'Technology', 'Justificación': 'Rationale',
    'Arquitectura': 'Architecture', 'Componente': 'Component', 'Patrón': 'Pattern',
    'Descripción': 'Description', 'Modelo de datos': 'Data model', 'Entidad': 'Entity',
    'Campos clave': 'Key fields', 'Relaciones': 'Relationships',
    'Preparación técnica incluida': 'Included technical preparation',
    'Dimensión': 'Dimension', 'Preparación': 'Preparation',
    'Módulos del producto': 'Product modules', 'Módulos': 'Modules',
    'Requerimientos': 'Requirements', 'Módulo': 'Module', 'Ítems': 'Items',
    'Dominio': 'Domain', 'Integraciones': 'Integrations', 'Incluidas': 'Included',
    'Excluidas': 'Excluded', 'Servicio': 'Service', 'Proveedor': 'Provider',
    'Conexión': 'Connection', 'Datos': 'Data', 'Razón': 'Reason',
    'Ambientes': 'Environments', 'Nombre': 'Name', 'Acceso': 'Access',
    'Seguridad': 'Security', 'Aspecto': 'Aspect', 'Implementación': 'Implementation',
    'Rendimiento': 'Performance', 'Métrica': 'Metric', 'Objetivo': 'Target',
    'Medición': 'Measurement', 'Prácticas': 'Practices', 'Estrategia': 'Strategy',
    'Calidad': 'Quality', 'Evalúa': 'Evaluates', 'Estándar': 'Standard',
    'Tipos de prueba': 'Test types', 'Tipo': 'Type', 'Valida': 'Validates',
    'Herramienta': 'Tool', 'Cuándo': 'When', 'Flujos críticos': 'Critical flows',
    'Decisiones': 'Decisions', 'Decisión': 'Decision', 'Alternativa': 'Alternative',
    'Enfoque': 'Focus', 'Incluye': 'Includes', 'Duración total': 'Total duration',
    'Fases': 'Phases', 'Hitos': 'Milestones',
}

"""
Default structure for ProposalSection technical_document content_json.

Used by migrations (backfill), ProposalService defaults, panel editor,
public technical mode, and technical PDF.
"""

EMPTY_TECHNICAL_DOCUMENT_JSON = {
    'purpose': '',
    'stack': [],
    'architecture': {
        'summary': '',
        'patterns': [],
        'diagramNote': '',
    },
    'dataModel': {
        'summary': '',
        'relationships': '',
        'entities': [],
    },
    'growthReadiness': {
        'summary': '',
        'strategies': [],
    },
    'epics': [],
    'apiSummary': '',
    'apiDomains': [],
    'integrations': {
        'included': [],
        'excluded': [],
        'notes': '',
    },
    'environments': [],
    'environmentsNote': '',
    'security': [],
    'performanceQuality': {'metrics': [], 'practices': []},
    'backupsNote': '',
    'quality': {
        'dimensions': [],
        'testTypes': [],
        'criticalFlowsNote': '',
    },
    'decisions': [],
}

# Copy hints for admin when inserting optional-module stubs (editor uses JS template;
# kept here for backend/docs parity).
OPTIONAL_MODULE_TECHNICAL_STUB_HINT_ES = (
    'Bloque técnico genérico ligado a un módulo opcional (linked_module_ids). '
    'Visible en modo técnico y PDF técnico solo si el cliente incluye ese módulo en la propuesta.'
)

import pytest

from content.models import ContractTemplate
from content.services.contract_terms_service import build_contract_terms_payload

pytestmark = pytest.mark.django_db


def create_template(markdown):
    return ContractTemplate.objects.create(
        name='Contrato global',
        content_markdown=markdown,
        is_default=True,
    )


def test_build_contract_terms_payload_splits_h2_clauses():
    create_template(
        '# Contrato\n\nIntroducción.\n\n'
        '## CLÁUSULA PRIMERA — OBJETO\n\nContenido uno.\n\n'
        '## CLÁUSULA SEGUNDA — PAGO\n\nContenido dos.'
    )

    payload = build_contract_terms_payload()

    assert [clause['id'] for clause in payload['clauses']] == [
        'clause-01',
        'clause-02',
    ]
    assert payload['clauses'][1]['title'] == 'CLÁUSULA SEGUNDA — PAGO'


def test_build_contract_terms_payload_masks_template_placeholders():
    create_template(
        'Entre {client_full_name} y {contractor_full_name}.\n\n'
        '## CLÁUSULA PRIMERA — OBJETO\n\nC.C. {client_cedula}.'
    )

    payload = build_contract_terms_payload()

    serialized = str(payload)
    assert 'XXX-XXX-XXX' in serialized
    assert '{client_full_name}' not in serialized


def test_build_contract_terms_payload_keeps_preamble_separate():
    create_template(
        '# Contrato\n\nTexto introductorio.\n\n'
        '## CLÁUSULA PRIMERA — OBJETO\n\nContenido.'
    )

    payload = build_contract_terms_payload()

    assert 'Texto introductorio.' in payload['preamble_markdown']
    assert 'CLÁUSULA PRIMERA' not in payload['preamble_markdown']


def test_build_contract_terms_payload_returns_none_without_default_template(db):
    ContractTemplate.objects.all().update(is_default=False)

    assert build_contract_terms_payload() is None

from io import BytesIO

import pytest
from pypdf import PdfReader
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ('language', 'included', 'excluded', 'scope'),
    [
        (
            'es',
            'Exclusividad conceptual a cargo de Project App. durante los cinco años.',
            'Sin el compromiso adicional de exclusividad conceptual',
            'mismo sector y nicho',
        ),
        (
            'en',
            'Conceptual exclusivity by Project App. throughout the five-year term.',
            'Excludes the additional conceptual exclusivity commitment',
            'same sector and niche',
        ),
    ],
)
def test_public_program_limits_conceptual_exclusivity_to_five_years(
    language, included, excluded, scope,
):
    """The published comparison must reserve the extra commitment for five years."""
    response = APIClient().get(f'/api/financing/public/?lang={language}')

    assert response.status_code == 200
    five_year, three_year = response.data['options']
    assert included in five_year['highlights']
    assert included not in three_year['highlights']
    assert excluded in ' '.join(three_year['highlights'])
    condition = response.data['conditions'][-1]
    assert condition['id'] == 'conceptual-exclusivity'
    assert scope in condition['summary']
    assert [item['number'] for item in response.data['conditions']] == [
        '01', '02', '03', '04', '05', '06', '07', '08',
    ]


@pytest.mark.parametrize(
    ('language', 'condition', 'scope', 'term', 'general_obligations'),
    [
        (
            'es',
            'Exclusividad conceptual — sólo a 5 años',
            'mismo sector y nicho',
            'un segundo ciclo no reinicia ni extiende este plazo',
            'se respetan en ambas modalidades',
        ),
        (
            'en',
            'Conceptual exclusivity — five-year option only',
            'same sector and niche',
            'a second cycle does not restart or extend this period',
            'are respected under both options',
        ),
    ],
)
def test_public_pdf_preserves_conceptual_exclusivity_limits(
    language, condition, scope, term, general_obligations,
):
    """The downloadable program must retain the commitment's scope in both languages."""
    response = APIClient().get(f'/api/financing/public/pdf/?lang={language}')
    reader = PdfReader(BytesIO(response.content))
    text = ' '.join(' '.join(page.extract_text().split()) for page in reader.pages)

    assert response.status_code == 200
    assert condition in text
    assert scope in text
    assert term in text
    assert general_obligations in text

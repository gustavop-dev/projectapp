"""Author contracts rejected before templates or assets are persisted."""
import pytest

from content.services.linktree_templates.package import validate_manifest
from content.services.linktree_templates.syntax import TemplateError


INVALID_MANIFEST_CASES = [
    ({'spec': '2.0'}, 'spec: "1.0"'),
    ({'script': 'app.js'}, 'campos desconocidos'),
    ({'name': ' '}, 'name debe ser texto'),
    ({'min_width': True}, 'Anchos inválidos'),
    ({'max_width': 319}, 'Anchos inválidos'),
    ({'motion': 'false'}, 'motion debe ser booleano'),
    ({'fonts': ['https://fonts.example/font']}, 'familias válidas'),
    ({'slots': {'banner': {}}}, 'photo y logo'),
    ({'slots': {'photo': {'required': 'yes'}}}, 'Declaración de slot inválida'),
    ({'slots': {'photo': {'aspect': '0:5'}}}, 'aspect debe ser una proporción'),
    ({'slots': {'photo': {'min_px': 0}}}, 'min_px debe estar entre'),
    ({'slots': {'photo': {'format': ['gif']}}}, 'Formato de slot inválido'),
    ({'assets': {}}, 'hasta 12 imágenes'),
    ({'assets': [{'key': 'hero'}]}, 'Cada asset necesita'),
    ({'assets': [{'key': 'slot-photo', 'file': 'assets/photo.png', 'alt': ''}]}, 'clave del asset'),
    ({'assets': [{'key': 'hero', 'file': 'hero.png', 'alt': ''}]}, 'rutas únicas dentro de assets/'),
    ({'editable_assets': ['missing']}, 'claves declaradas sin repetir'),
]


@pytest.mark.parametrize(('fields', 'message'), INVALID_MANIFEST_CASES)
def test_invalid_manifest_reports_author_contract(fields, message):
    """Fails if malformed author declarations reach template creation."""
    manifest = {'spec': '1.0', 'name': 'Editorial', **fields}

    with pytest.raises(TemplateError, match=message) as caught:
        validate_manifest(manifest)

    assert caught.value.issue['file'] == 'manifest.json'
    assert caught.value.issue['code'] == 'invalid_template'


def test_manifest_preserves_image_slot_contract():
    """Fails if valid photo requirements or editable assets are discarded."""
    slot = {'required': True, 'aspect': '4:5', 'min_px': 320, 'format': ['jpeg', 'png']}
    asset = {'key': 'hero', 'file': 'assets/hero.png', 'alt': 'Banner'}

    result = validate_manifest({
        'spec': '1.0', 'name': 'Editorial', 'slots': {'photo': slot},
        'assets': [asset], 'editable_assets': ['hero'], 'fonts': ['Oswald:wght@600;700'],
    })

    assert result['slots'] == {'photo': slot}
    assert result['assets'] == [asset]
    assert result['editable_assets'] == ['hero']
    assert result['max_width'] == 480

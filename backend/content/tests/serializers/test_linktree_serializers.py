"""Tests for linktree serializers — handle normalization and the design
system's button cardinality rules."""
import pytest

from content.models import Linktree, LinktreeButton
from content.serializers.linktree import (
    LinktreeCreateUpdateSerializer,
    PublicLinktreeSerializer,
    normalize_handle,
)

pytestmark = pytest.mark.django_db


def _button(tier, label='Botón', **extra):
    return {'tier': tier, 'action': 'web', 'label': label, 'href': 'https://x.co', **extra}


VALID_BUTTONS = [
    _button('primary', 'Conectemos en LinkedIn'),
    _button('pair', 'Guardar'),
    _button('pair', 'WhatsApp'),
    _button('row', 'Conoce ProjectApp'),
]


class TestNormalizeHandle:
    def test_strips_decorative_at_prefix(self):
        assert normalize_handle('@Gustavo') == 'gustavo'

    def test_lowercases_and_trims(self):
        assert normalize_handle('  MiHandle ') == 'mihandle'


class TestHandleValidation:
    def test_rejects_reserved_handle(self):
        serializer = LinktreeCreateUpdateSerializer(data={'handle': 'panel', 'name': 'X'})
        assert not serializer.is_valid()
        assert 'handle' in serializer.errors

    def test_rejects_invalid_characters(self):
        serializer = LinktreeCreateUpdateSerializer(data={'handle': 'gus tavo!', 'name': 'X'})
        assert not serializer.is_valid()
        assert 'handle' in serializer.errors

    def test_rejects_duplicate_handle_case_insensitive(self):
        Linktree.objects.create(handle='gustavo', name='Existente')
        serializer = LinktreeCreateUpdateSerializer(data={'handle': '@Gustavo', 'name': 'X'})
        assert not serializer.is_valid()
        assert 'handle' in serializer.errors

    def test_accepts_own_handle_on_update(self):
        tree = Linktree.objects.create(handle='gustavo', name='Existente')
        serializer = LinktreeCreateUpdateSerializer(
            tree, data={'handle': 'gustavo'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors


class TestButtonCardinalityRules:
    def _errors_for(self, buttons):
        serializer = LinktreeCreateUpdateSerializer(
            data={'handle': 'nuevo', 'name': 'X', 'buttons': buttons}
        )
        serializer.is_valid()
        return serializer.errors

    def test_requires_exactly_one_primary(self):
        errors = self._errors_for([_button('row')])
        assert 'buttons' in errors

    def test_rejects_two_primaries(self):
        errors = self._errors_for([_button('primary'), _button('primary')])
        assert 'buttons' in errors

    def test_rejects_two_featured(self):
        errors = self._errors_for(
            [_button('primary'), _button('featured'), _button('featured')]
        )
        assert 'buttons' in errors

    def test_rejects_single_pair_button(self):
        errors = self._errors_for([_button('primary'), _button('pair')])
        assert 'buttons' in errors

    def test_rejects_seven_row_buttons(self):
        buttons = [_button('primary')] + [_button('row') for _ in range(7)]
        assert 'buttons' in self._errors_for(buttons)

    def test_accepts_the_design_composition(self):
        serializer = LinktreeCreateUpdateSerializer(
            data={'handle': 'nuevo', 'name': 'X', 'buttons': VALID_BUTTONS}
        )
        assert serializer.is_valid(), serializer.errors

    def test_ignores_inactive_buttons_in_cardinality(self):
        buttons = VALID_BUTTONS + [_button('primary', is_active=False)]
        serializer = LinktreeCreateUpdateSerializer(
            data={'handle': 'nuevo', 'name': 'X', 'buttons': buttons}
        )
        assert serializer.is_valid(), serializer.errors


class TestButtonsReplaceSemantics:
    def test_create_persists_nested_buttons_in_order(self):
        serializer = LinktreeCreateUpdateSerializer(
            data={'handle': 'nuevo', 'name': 'X', 'buttons': VALID_BUTTONS}
        )
        assert serializer.is_valid(), serializer.errors
        tree = serializer.save()
        assert list(tree.buttons.values_list('label', flat=True)) == [
            'Conectemos en LinkedIn', 'Guardar', 'WhatsApp', 'Conoce ProjectApp',
        ]

    def test_update_replaces_previous_buttons(self):
        tree = Linktree.objects.create(handle='gustavo', name='X')
        LinktreeButton.objects.create(linktree=tree, label='Viejo', tier='primary')
        serializer = LinktreeCreateUpdateSerializer(
            tree, data={'buttons': VALID_BUTTONS}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert tree.buttons.count() == 4
        assert not tree.buttons.filter(label='Viejo').exists()

    def test_update_without_buttons_key_keeps_existing(self):
        tree = Linktree.objects.create(handle='gustavo', name='X')
        LinktreeButton.objects.create(linktree=tree, label='Intacto', tier='primary')
        serializer = LinktreeCreateUpdateSerializer(
            tree, data={'name': 'Renombrado'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert tree.buttons.filter(label='Intacto').exists()


class TestPublicSerializer:
    def test_excludes_inactive_buttons(self):
        tree = Linktree.objects.create(handle='gustavo', name='X')
        LinktreeButton.objects.create(linktree=tree, label='Visible', tier='primary')
        LinktreeButton.objects.create(linktree=tree, label='Oculto', is_active=False)
        data = PublicLinktreeSerializer(tree).data
        assert [b['label'] for b in data['buttons']] == ['Visible']

    def test_does_not_expose_internal_fields(self):
        tree = Linktree.objects.create(handle='gustavo', name='Interno')
        data = PublicLinktreeSerializer(tree).data
        assert 'name' not in data
        assert 'is_active' not in data

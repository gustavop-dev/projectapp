"""Tests for the Linktree + LinktreeButton models."""
import pytest
from django.db import IntegrityError

from content.models import Linktree, LinktreeButton

pytestmark = pytest.mark.django_db


class TestLinktreeModel:
    def test_generates_uuid_primary_key(self):
        tree = Linktree.objects.create(handle='gustavo', name='Gustavo')
        assert tree.id is not None

    def test_handle_is_unique(self):
        Linktree.objects.create(handle='gustavo', name='Gustavo')
        with pytest.raises(IntegrityError):
            Linktree.objects.create(handle='gustavo', name='Otro')

    def test_public_path_prefixes_lk_and_at(self):
        tree = Linktree.objects.create(handle='gustavo', name='Gustavo')
        assert tree.public_path == '/lk/@gustavo'

    def test_defaults_to_active_personal_kind(self):
        tree = Linktree.objects.create(handle='x', name='X')
        assert tree.is_active is True
        assert tree.kind == Linktree.Kind.PERSONAL

    def test_footer_tagline_defaults_to_brand_line(self):
        tree = Linktree.objects.create(handle='x', name='X')
        assert tree.footer_tagline == 'DISEÑO · CÓDIGO · RESULTADOS'


class TestLinktreeButtonModel:
    @pytest.fixture
    def tree(self):
        return Linktree.objects.create(handle='gustavo', name='Gustavo')

    def test_orders_buttons_by_order_field(self, tree):
        second = LinktreeButton.objects.create(linktree=tree, label='B', order=2)
        first = LinktreeButton.objects.create(linktree=tree, label='A', order=1)
        assert list(tree.buttons.all()) == [first, second]

    def test_resolved_icon_comes_from_action_catalog(self, tree):
        button = LinktreeButton.objects.create(
            linktree=tree, label='LinkedIn', action=LinktreeButton.Action.LINKEDIN
        )
        assert button.resolved_icon == 'linkedin'

    def test_resolved_icon_uses_custom_icon_for_custom_action(self, tree):
        button = LinktreeButton.objects.create(
            linktree=tree, label='X', action=LinktreeButton.Action.CUSTOM, icon='rocket'
        )
        assert button.resolved_icon == 'rocket'

    def test_url_button_without_href_is_pending(self, tree):
        button = LinktreeButton.objects.create(
            linktree=tree, label='LinkedIn', action=LinktreeButton.Action.LINKEDIN, href=''
        )
        assert button.is_pending is True

    def test_vcard_button_without_href_is_not_pending(self, tree):
        button = LinktreeButton.objects.create(
            linktree=tree, label='Guardar', action=LinktreeButton.Action.VCARD, href=''
        )
        assert button.is_pending is False

    def test_deleting_linktree_cascades_buttons(self, tree):
        LinktreeButton.objects.create(linktree=tree, label='A')
        tree.delete()
        assert LinktreeButton.objects.count() == 0

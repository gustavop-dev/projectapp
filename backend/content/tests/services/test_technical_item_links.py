"""The JSON/MCP update refuses a technical document that traces nothing.

``requirement.linked_item_ids`` is what powers the client-facing "view
requirements" modal, the PDF, and the scope item each platform requirement
inherits. The admin editor already blocks a save that breaks it; this covers
the import path, which used to accept an untraced document in silence.
"""
import pytest
from django.utils import timezone

from content.api_errors import ProposalActionError
from content.models import BusinessProposal, ProposalSection
from content.serializers.proposal import ProposalFromJSONSerializer
from content.services.proposal_module_links import (
    build_item_link_options,
    build_technical_item_coverage,
)
from content.services.proposal_service import (
    apply_proposal_json_update,
    enforce_technical_item_coverage,
)

pytestmark = pytest.mark.django_db

LOGIN = 'item-views-login'
PANEL = 'item-views-panel'


def _fr_section(groups=None, additional=None):
    return {
        'section_type': 'functional_requirements',
        'content_json': {
            'groups': groups if groups is not None else [{
                'id': 'views',
                'title': 'Vistas',
                'items': [
                    {'id': LOGIN, 'name': 'Inicio de sesión'},
                    {'id': PANEL, 'name': 'Panel'},
                ],
            }],
            'additionalModules': additional or [],
        },
    }


def _tech(linked):
    return {
        'epics': [{
            'title': 'Acceso',
            'epicKey': 'acceso',
            'requirements': [{
                'title': 'Entrar',
                'flowKey': 'entrar',
                'linked_item_ids': list(linked),
            }],
        }],
    }


class TestBuildItemLinkOptions:
    def test_group_items_are_always_required(self):
        options = build_item_link_options([_fr_section()])

        assert len(options) == 1
        assert options[0]['isRequiredForCoverage'] is True
        assert [i['id'] for i in options[0]['items']] == [LOGIN, PANEL]

    def test_unselected_catalog_module_is_not_required(self):
        """An optional module nobody sold must never block a save."""
        options = build_item_link_options([_fr_section(additional=[{
            'id': 'extra',
            'title': 'Extra',
            'selected': False,
            'items': [{'id': 'item-extra-uno', 'name': 'Uno'}],
        }])])

        extra = next(o for o in options if o['groupId'] == 'extra')
        assert extra['isRequiredForCoverage'] is False

    @pytest.mark.parametrize('flags', [
        {'selected': True},
        {'selected': None, 'default_selected': True},
    ])
    def test_selected_catalog_module_becomes_required(self, flags):
        options = build_item_link_options([_fr_section(additional=[dict(
            {'id': 'extra', 'title': 'Extra',
             'items': [{'id': 'item-extra-uno', 'name': 'Uno'}]}, **flags,
        )])])

        extra = next(o for o in options if o['groupId'] == 'extra')
        assert extra['isRequiredForCoverage'] is True

    def test_hidden_group_is_skipped(self):
        options = build_item_link_options([_fr_section(groups=[{
            'id': 'views', 'title': 'Vistas', 'is_visible': False,
            'items': [{'id': LOGIN, 'name': 'Login'}],
        }])])

        assert options == []


class TestUntracedItemReport:
    def test_reports_the_items_no_requirement_links(self):
        options = build_item_link_options([_fr_section()])

        report = build_technical_item_coverage(options, _tech([LOGIN]))

        assert report['requiredCount'] == 2
        assert report['coveredRequiredCount'] == 1
        assert [m['id'] for m in report['missingRequired']] == [PANEL]

    def test_reports_nothing_when_every_item_is_traced(self):
        options = build_item_link_options([_fr_section()])

        report = build_technical_item_coverage(options, _tech([LOGIN, PANEL]))

        assert report['missingRequired'] == []
        assert report['coveredRequiredCount'] == 2


class TestEnforceItemTracing:
    def test_raises_naming_the_untraced_items(self):
        with pytest.raises(ProposalActionError) as exc:
            enforce_technical_item_coverage([_fr_section()], _tech([]))

        assert exc.value.code == 'technical_item_coverage_incomplete'
        assert 'Inicio de sesión' in str(exc.value)
        assert 'Panel' in str(exc.value)
        assert 'linked_item_ids' in exc.value.hint

    def test_passes_when_every_item_is_traced(self):
        sections = [_fr_section()]
        tech = _tech([LOGIN, PANEL])

        enforce_technical_item_coverage(sections, tech)

        report = build_technical_item_coverage(
            build_item_link_options(sections), tech,
        )
        assert report['missingRequired'] == []

    def test_document_without_epics_is_not_gated(self):
        """A proposal with no technical detail has nothing to trace yet."""
        sections = [_fr_section()]
        empty = {'epics': []}
        report = build_technical_item_coverage(
            build_item_link_options(sections), empty,
        )
        # The items ARE untraced here — the gate skips anyway, by design.
        assert [m['id'] for m in report['missingRequired']] == [LOGIN, PANEL]

        enforce_technical_item_coverage(sections, empty)


class TestImportPathIsGated:
    """End to end over apply_proposal_json_update, the shared import path."""

    @pytest.fixture
    def proposal(self, db):
        p = BusinessProposal.objects.create(
            title='Tracing Proposal',
            client_name='Tracing Client',
            client_email='tracing@example.com',
            language='es',
            currency='COP',
            status='draft',
            expires_at=timezone.now() + timezone.timedelta(days=14),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='functional_requirements',
            title='Requerimientos', order=10,
            content_json=_fr_section()['content_json'],
        )
        ProposalSection.objects.create(
            proposal=p, section_type='technical_document',
            title='Detalle técnico', order=16,
            content_json=_tech([LOGIN, PANEL]),
        )
        return p

    def _validated(self, proposal, sections):
        serializer = ProposalFromJSONSerializer(
            data={
                'title': proposal.title,
                'client_name': proposal.client_name,
                'sections': dict(
                    # The serializer requires this key on every from-JSON payload.
                    {'general': {'clientName': proposal.client_name}}, **sections,
                ),
            },
            context={'proposal': proposal},
        )
        assert serializer.is_valid(), serializer.errors
        return serializer.validated_data

    def test_update_with_untraced_items_is_rejected(self, proposal):
        with pytest.raises(ProposalActionError) as exc:
            apply_proposal_json_update(
                proposal, self._validated(proposal, {'technicalDocument': _tech([])}),
            )

        assert exc.value.code == 'technical_item_coverage_incomplete'

    def test_rejected_update_persists_nothing(self, proposal):
        """The gate runs inside the atomic block, so the proposal is untouched."""
        before = proposal.sections.get(
            section_type='technical_document',
        ).content_json

        with pytest.raises(ProposalActionError):
            apply_proposal_json_update(
                proposal, self._validated(proposal, {'technicalDocument': _tech([])}),
            )

        after = BusinessProposal.objects.get(pk=proposal.pk).sections.get(
            section_type='technical_document',
        ).content_json
        assert after == before

    def test_update_that_omits_the_technical_document_is_not_gated(self, proposal):
        """Only a payload asserting the detail gets gated.

        That the stored document traces nothing is irrelevant here: an update
        touching other sections is not claiming the detail is complete, so
        rejecting it would block unrelated edits.
        """
        proposal.sections.filter(section_type='technical_document').update(
            content_json=_tech([]),
        )

        apply_proposal_json_update(proposal, self._validated(proposal, {
            'functionalRequirements': _fr_section()['content_json'],
        }))

        stored = BusinessProposal.objects.get(pk=proposal.pk).sections.get(
            section_type='functional_requirements',
        ).content_json
        assert [i['id'] for i in stored['groups'][0]['items']] == [LOGIN, PANEL]

    def test_update_sending_an_empty_technical_document_is_not_gated(self, proposal):
        """The seeder fills an empty document; that content is not the caller's.

        A payload of `technicalDocument: {}` asserts nothing about the detail —
        the epics that exist afterwards were generated by
        seed_module_technical_requirements. Rejecting the caller for what the
        system wrote on its behalf would block the reseeding path.
        """
        proposal.sections.filter(section_type='technical_document').update(
            content_json=_tech([]),
        )

        apply_proposal_json_update(
            proposal, self._validated(proposal, {'technicalDocument': {}}),
        )

        stored = BusinessProposal.objects.get(pk=proposal.pk).sections.get(
            section_type='technical_document',
        ).content_json
        assert stored is not None
        assert 'epics' in stored

    def test_update_that_traces_every_item_is_accepted(self, proposal):
        tech = _tech([LOGIN, PANEL])
        tech['epics'][0]['title'] = 'Acceso revisado'

        apply_proposal_json_update(
            proposal, self._validated(proposal, {'technicalDocument': tech}),
        )

        stored = BusinessProposal.objects.get(pk=proposal.pk).sections.get(
            section_type='technical_document',
        ).content_json
        assert stored['epics'][0]['title'] == 'Acceso revisado'

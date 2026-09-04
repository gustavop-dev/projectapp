import pytest

from content.models import AdditionalModule


pytestmark = pytest.mark.django_db


SLUG = 'audiovisual-experiences'


@pytest.fixture
def module():
    return AdditionalModule.objects.select_related('category').get(slug=SLUG)


def test_migration_seeds_bilingual_audiovisual_module(module):
    assert module.category.slug == 'marketing-acquisition'
    assert module.name_es == 'Experiencias audiovisuales'
    assert module.name_en == 'Audiovisual experiences'
    assert module.icon == '🎬'
    assert module.is_active is True


def test_audiovisual_module_carries_both_languages_of_every_list(module):
    assert len(module.problems_solved_es) == len(module.problems_solved_en) == 3
    assert len(module.integrations_es) == len(module.integrations_en) == 3
    assert len(module.implementation_requirements_es) == 6
    assert len(module.implementation_requirements_en) == 6


def test_audiovisual_module_states_the_initial_packages(module):
    assert '4, 8 y 16 recursos audiovisuales' in ' '.join(
        module.implementation_requirements_es,
    )
    assert '4, 8, and 16 audiovisual assets' in ' '.join(
        module.implementation_requirements_en,
    )


def test_audiovisual_module_invites_to_consult_available_packages(module):
    assert module.implementation_requirements_es[-1] == (
        'Paquetes disponibles consultados con el representante comercial antes de empezar.'
    )
    assert module.implementation_requirements_en[-1] == (
        'Available packages reviewed with the sales representative before starting.'
    )


def test_audiovisual_module_declares_the_collaborative_brand_input(module):
    requirements = ' '.join(module.implementation_requirements_es).lower()

    assert 'trabajo colaborativo' in module.what_is_es.lower()
    assert 'identidad de marca' in requirements
    assert 'material propio' in requirements
    assert 'mensajes clave' in requirements


def test_audiovisual_module_occupies_a_free_position_in_its_category(module):
    siblings = AdditionalModule.objects.filter(
        category_id=module.category_id,
    ).exclude(pk=module.pk).values_list('order', flat=True)

    assert module.order not in set(siblings)


def test_seeded_catalog_never_names_the_production_tooling():
    """The catalog sells the outcome, never the tool used to produce it."""
    text = ' '.join(
        ' '.join(
            [
                module.name_es, module.name_en,
                module.summary_es, module.summary_en,
                module.what_is_es, module.what_is_en,
                module.purpose_es, module.purpose_en,
                *module.problems_solved_es, *module.problems_solved_en,
                *module.integrations_es, *module.integrations_en,
                *module.implementation_requirements_es,
                *module.implementation_requirements_en,
            ],
        )
        for module in AdditionalModule.objects.all()
    ).lower()

    # Guard against a vacuous pass: the corpus must really carry catalog copy.
    assert 'experiencias audiovisuales' in text
    assert 'hyperframe' not in text

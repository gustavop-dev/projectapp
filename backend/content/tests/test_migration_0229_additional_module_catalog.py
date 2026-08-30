import pytest

from content.models import AdditionalModule


pytestmark = pytest.mark.django_db


EXPECTED_MODULES = {
    'sales-crm-pipeline': ('marketing-acquisition', 'CRM y embudo comercial', 'CRM and sales pipeline'),
    'scheduling-bookings': ('commerce-transactions', 'Agenda, reservas y disponibilidad', 'Scheduling, bookings, and availability'),
    'memberships-subscriptions': ('commerce-transactions', 'Membresías y suscripciones', 'Memberships and subscriptions'),
    'customer-self-service': ('identity-access', 'Portal de autoservicio para clientes', 'Customer self-service portal'),
    'loyalty-referrals': ('marketing-acquisition', 'Fidelización y referidos', 'Loyalty and referral program'),
}


@pytest.mark.parametrize(
    ('slug', 'category_slug', 'name_es', 'name_en'),
    [
        (slug, *expected)
        for slug, expected in EXPECTED_MODULES.items()
    ],
)
def test_catalog_expansion_seeds_bilingual_module(
    slug,
    category_slug,
    name_es,
    name_en,
):
    module = AdditionalModule.objects.select_related('category').get(slug=slug)

    assert module.category.slug == category_slug
    assert module.name_es == name_es
    assert module.name_en == name_en
    assert len(module.problems_solved_es) == 3
    assert len(module.integrations_en) == 3
    assert len(module.implementation_requirements_es) == 3


def test_catalog_expansion_uses_unique_category_positions():
    modules = AdditionalModule.objects.filter(
        slug__in=EXPECTED_MODULES,
    ).values_list('category_id', 'order')

    positions = list(modules)
    assert len(positions) == len(set(positions))

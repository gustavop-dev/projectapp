"""Where the panel's income form gets the start of the next hosting window.

Duplicating an income counts from the original, but creating one has no
original: the antecedent is the last window already on the book for that
client. An income does not record which hosting it belongs to — ``origin`` is
a label, not a link — so the lookup goes through the client, narrowed by
project, and refuses to guess when the client has several hostings that could
each own that last window.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model

from content.models import HostingRecord, IncomeRecord
from content.utils import today_bogota

User = get_user_model()
pytestmark = pytest.mark.django_db

URL = '/api/accounting/incomes/period-suggestion/'


def make_client(email='daniel@example.com', *, first='Daniel'):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345', first_name=first,
    )
    return UserProfile.objects.create(user=user, cedula='1049654583')


def make_window(client, start, end, **overrides):
    fields = {
        'concept': 'Hosting',
        'kind': IncomeRecord.Kind.EXPECTED,
        'origin': IncomeRecord.Origin.HOSTING,
        'client': client,
        'period_date': start,
        'period_start': start,
        'period_end': end,
        'period_cadence': 'annual',
        'total_amount': Decimal('550000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def make_hosting(client, **overrides):
    fields = {
        'client_name': 'Daniel - Kore',
        'domain_url': 'https://korehealths.com/',
        'monthly_value': Decimal('91667.00'),
        'payment_modality': 'annual',
        'payment_per_cycle': Decimal('1100004.00'),
        'is_active': True,
        'client': client,
    }
    fields.update(overrides)
    return HostingRecord.objects.create(**fields)


class TestSuggestion:
    def test_the_next_window_opens_the_day_after_the_last_one_closed(
        self, super_client,
    ):
        client = make_client()
        make_window(client, date(2025, 9, 1), date(2026, 8, 31))

        response = super_client.get(URL, {'client': client.pk})

        assert response.status_code == 200, response.data
        assert response.data['previous_period_end'] == '2026-08-31'
        assert response.data['suggested_start'] == '2026-09-01'

    def test_the_latest_window_wins_over_an_older_one(self, super_client):
        client = make_client()
        make_window(client, date(2023, 1, 1), date(2023, 12, 31))
        make_window(client, date(2025, 9, 1), date(2026, 8, 31))

        response = super_client.get(URL, {'client': client.pk})

        assert response.data['suggested_start'] == '2026-09-01'

    def test_a_project_narrows_the_lookup_to_its_own_windows(self, super_client):
        client = make_client()
        project = Project.objects.create(name='Kore', client=client.user)
        make_window(client, date(2025, 9, 1), date(2026, 8, 31))
        make_window(
            client, date(2026, 1, 1), date(2026, 6, 30), project=project,
        )

        response = super_client.get(
            URL, {'client': client.pk, 'project': project.pk},
        )

        assert response.data['previous_period_end'] == '2026-06-30'
        assert response.data['suggested_start'] == '2026-07-01'

    def test_the_first_charge_of_a_client_is_proposed_for_today(
        self, super_client,
    ):
        client = make_client()

        response = super_client.get(URL, {'client': client.pk})

        assert response.data['previous_period_end'] is None
        assert response.data['suggested_start'] == today_bogota().isoformat()

    def test_a_client_with_no_window_yet_falls_back_to_today(self, super_client):
        """Only a recorded window counts: origin alone attests no dates."""
        client = make_client()
        make_window(
            client, date(2025, 9, 1), None,
            period_start=None, period_date=date(2025, 9, 1),
        )
        make_window(
            client, date(2026, 1, 1), date(2026, 6, 30),
            origin=IncomeRecord.Origin.DEVELOPMENT,
        )

        response = super_client.get(URL, {'client': client.pk})

        assert response.data['previous_period_end'] is None
        assert response.data['suggested_start'] == today_bogota().isoformat()

    def test_several_hostings_without_a_project_propose_nothing(
        self, super_client,
    ):
        """The last window may belong to the other hosting — refuse to guess."""
        client = make_client()
        make_hosting(client)
        make_hosting(client, domain_url='https://otro.com/')
        make_window(client, date(2025, 9, 1), date(2026, 8, 31))

        response = super_client.get(URL, {'client': client.pk})

        assert response.data['previous_period_end'] is None
        assert response.data['suggested_start'] == today_bogota().isoformat()

    def test_a_project_disambiguates_several_hostings(self, super_client):
        client = make_client()
        project = Project.objects.create(name='Kore', client=client.user)
        make_hosting(client)
        make_hosting(client, domain_url='https://otro.com/')
        make_window(
            client, date(2025, 9, 1), date(2026, 8, 31), project=project,
        )

        response = super_client.get(
            URL, {'client': client.pk, 'project': project.pk},
        )

        assert response.data['suggested_start'] == '2026-09-01'

    def test_no_client_proposes_today(self, super_client):
        """The form asks before a client is picked; that is not an error."""
        response = super_client.get(URL)

        assert response.status_code == 200, response.data
        assert response.data['suggested_start'] == today_bogota().isoformat()

    def test_the_window_of_another_client_is_ignored(self, super_client):
        mine = make_client()
        theirs = make_client('nestor@example.com', first='Néstor')
        make_window(theirs, date(2025, 9, 1), date(2026, 8, 31))

        response = super_client.get(URL, {'client': mine.pk})

        assert response.data['previous_period_end'] is None

    def test_a_window_closing_today_still_opens_the_next_one_tomorrow(
        self, super_client,
    ):
        client = make_client()
        today = today_bogota()
        make_window(client, today - timedelta(days=30), today)

        response = super_client.get(URL, {'client': client.pk})

        assert response.data['suggested_start'] == (
            today + timedelta(days=1)
        ).isoformat()

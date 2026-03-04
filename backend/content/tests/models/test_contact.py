"""
Tests for the Contact model.

Covers: field validation, budget choices, __str__.
"""
import pytest
from content.models import Contact


pytestmark = pytest.mark.django_db


class TestContactCreation:
    def test_str_returns_subject(self, contact):
        assert str(contact) == 'Project inquiry'

    def test_create_contact_with_all_fields(self, contact):
        assert contact.email == 'client@example.com'
        assert contact.phone_number == '+573001234567'
        assert contact.subject == 'Project inquiry'
        assert contact.message == 'I need a web application.'
        assert contact.budget == '5-10K'

    def test_create_contact_without_optional_fields(self, db):
        c = Contact.objects.create(
            email='min@example.com',
            phone_number='123',
            subject='Quick question',
        )
        assert c.message is None
        assert c.budget is None

    @pytest.mark.parametrize('budget', [
        '500-5K', '5-10K', '10-20K', '20-30K', '>30K',
    ])
    def test_valid_budget_choices(self, db, budget):
        c = Contact.objects.create(
            email='test@test.com',
            phone_number='123',
            subject='Test',
            budget=budget,
        )
        assert c.budget == budget

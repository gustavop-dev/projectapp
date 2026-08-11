"""The NDA names EL CONSULTOR by NIT or by cédula — at least one is required.

Every other field stays optional so the document can still be printed blank
and completed by hand.
"""

from content.serializers.diagnostic import ConfidentialityParamsSerializer


class TestConfidentialityParamsSerializerContractorIdentity:
    def test_accepts_a_consultant_identified_only_by_nit(self):
        serializer = ConfidentialityParamsSerializer(data={
            'contractor_nit': '900.123.456-7',
        })
        assert serializer.is_valid(), serializer.errors

    def test_accepts_a_consultant_identified_only_by_cedula(self):
        serializer = ConfidentialityParamsSerializer(data={
            'contractor_cedula': '1037635428',
        })
        assert serializer.is_valid(), serializer.errors

    def test_rejects_a_consultant_with_neither_document(self):
        serializer = ConfidentialityParamsSerializer(data={'client_full_name': 'Ana'})
        assert not serializer.is_valid()
        assert 'contractor_nit' in serializer.errors

    def test_client_fields_stay_optional(self):
        """Only the consultant's identity became mandatory."""
        serializer = ConfidentialityParamsSerializer(data={
            'contractor_nit': '900.123.456-7',
            'client_full_name': '',
            'client_cedula': '',
        })
        assert serializer.is_valid(), serializer.errors

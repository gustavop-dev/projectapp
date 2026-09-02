from io import StringIO

import pytest
from django.core.management import CommandError, call_command


def test_command_refuses_implicit_non_production_settings():
    with pytest.raises(CommandError, match='non-production settings'):
        call_command('diagnose_proposal_notifications', stdout=StringIO())

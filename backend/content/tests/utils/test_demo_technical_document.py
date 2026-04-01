"""Shape parity between demo and empty technical document JSON."""

from content.demo_technical_document import DEMO_TECHNICAL_DOCUMENT_JSON
from content.technical_document_defaults import EMPTY_TECHNICAL_DOCUMENT_JSON


def test_demo_technical_document_nested_keys_match_empty_template():
    demo = DEMO_TECHNICAL_DOCUMENT_JSON
    empty = EMPTY_TECHNICAL_DOCUMENT_JSON
    assert set(demo.keys()) == set(empty.keys())
    assert set(demo['architecture'].keys()) == set(empty['architecture'].keys())
    assert set(demo['dataModel'].keys()) == set(empty['dataModel'].keys())
    assert set(demo['integrations'].keys()) == set(empty['integrations'].keys())
    assert set(demo['performanceQuality'].keys()) == set(empty['performanceQuality'].keys())
    assert set(demo['quality'].keys()) == set(empty['quality'].keys())
    assert set(demo['growthReadiness'].keys()) == set(empty['growthReadiness'].keys())

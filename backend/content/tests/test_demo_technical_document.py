"""Shape parity between demo and empty technical document JSON."""

from content.demo_technical_document import DEMO_TECHNICAL_DOCUMENT_JSON
from content.technical_document_defaults import EMPTY_TECHNICAL_DOCUMENT_JSON


def _assert_dict_keys_match(a, b, path):
    assert set(a.keys()) == set(b.keys()), f'Key mismatch at {path}: {set(a.keys())!r} vs {set(b.keys())!r}'


def test_demo_technical_document_nested_keys_match_empty_template():
    demo = DEMO_TECHNICAL_DOCUMENT_JSON
    empty = EMPTY_TECHNICAL_DOCUMENT_JSON
    _assert_dict_keys_match(demo, empty, 'root')
    _assert_dict_keys_match(demo['architecture'], empty['architecture'], 'architecture')
    _assert_dict_keys_match(demo['dataModel'], empty['dataModel'], 'dataModel')
    _assert_dict_keys_match(demo['integrations'], empty['integrations'], 'integrations')
    _assert_dict_keys_match(demo['performanceQuality'], empty['performanceQuality'], 'performanceQuality')
    _assert_dict_keys_match(demo['quality'], empty['quality'], 'quality')
    _assert_dict_keys_match(demo['growthReadiness'], empty['growthReadiness'], 'growthReadiness')

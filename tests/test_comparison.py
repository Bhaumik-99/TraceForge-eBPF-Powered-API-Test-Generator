from traceforge.comparison import json_matches

def test_redacted_values_are_wildcards_but_structure_is_checked():
    expected = {"user":"demo","token":"[REDACTED]","items":[1,2]}
    assert json_matches(expected, {"user":"demo","token":"real-value","items":[1,2]})
    assert not json_matches(expected, {"user":"demo","token":"real-value","items":[1]})
    assert not json_matches(expected, {"user":"demo","token":"real-value","items":[1,2],"extra":True})

def test_booleans_do_not_compare_equal_to_numbers():
    assert not json_matches(True, 1)

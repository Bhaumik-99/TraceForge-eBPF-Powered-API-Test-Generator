"""Response comparison helpers shared by replay and generated tests."""
from typing import Any
REDACTED_MARKER = "[REDACTED]"
BODY_OMITTED_PREFIX = "[BODY OMITTED:"

def json_matches(expected: Any, actual: Any) -> bool:
    """Compare structure strictly while treating redacted/omitted values as wildcards."""
    if expected == REDACTED_MARKER:
        return True
    if isinstance(expected, str) and expected.startswith(BODY_OMITTED_PREFIX):
        return True
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and set(expected) == set(actual)
                and all(json_matches(expected[k], actual[k]) for k in expected))
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(expected) == len(actual)
                and all(json_matches(a, b) for a, b in zip(expected, actual)))
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(expected) is type(actual) and expected == actual
    return type(expected) is type(actual) and expected == actual

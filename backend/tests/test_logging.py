import json
import logging

from apps.common.logging import JsonFormatter


def test_json_formatter_includes_extra_fields() -> None:
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.request_id = "abc"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "abc"

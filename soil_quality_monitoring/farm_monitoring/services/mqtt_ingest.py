import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from farm_monitoring.models import Measurement, Sensor

logger = logging.getLogger(__name__)

TOPIC_PATTERN = re.compile(r'^(?P<prefix>.+)/(?P<serial>[^/]+)/measurement$')


class IngestError(Exception):
    pass


@dataclass
class IngestResult:
    sensor_serial: str
    value: float
    timestamp: datetime
    measurement_id: int


def parse_topic(topic: str) -> str:
    match = TOPIC_PATTERN.match(topic)
    if not match:
        raise IngestError(f"Topic does not match expected pattern: {topic!r}")
    return match.group('serial')


def parse_payload(raw: bytes | str) -> tuple[float, Optional[datetime]]:
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise IngestError(f"Malformed JSON payload: {e}") from e

    if not isinstance(data, dict):
        raise IngestError(f"Payload must be a JSON object, got {type(data).__name__}")

    if 'value' not in data:
        raise IngestError("Payload missing required field 'value'")

    try:
        value = float(data['value'])
    except (TypeError, ValueError) as e:
        raise IngestError(f"Field 'value' is not a number: {data['value']!r}") from e

    ts = None
    if 'timestamp' in data and data['timestamp']:
        ts = parse_datetime(str(data['timestamp']))
        if ts is None:
            raise IngestError(f"Field 'timestamp' is not ISO 8601: {data['timestamp']!r}")
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, timezone.utc)

    return value, ts


def ingest_measurement(topic: str, payload: bytes | str) -> IngestResult:
    serial = parse_topic(topic)
    value, ts = parse_payload(payload)

    try:
        sensor = Sensor.objects.get(
            serial_number=serial,
            archived=False,
            is_active=True,
        )
    except Sensor.DoesNotExist as e:
        raise IngestError(
            f"Unknown or inactive sensor: serial={serial!r}"
        ) from e

    measurement = Measurement.objects.create(
        sensor=sensor,
        value=value,
        **({'timestamp': ts} if ts else {}),
    )

    return IngestResult(
        sensor_serial=serial,
        value=value,
        timestamp=measurement.timestamp,
        measurement_id=measurement.pk,
    )

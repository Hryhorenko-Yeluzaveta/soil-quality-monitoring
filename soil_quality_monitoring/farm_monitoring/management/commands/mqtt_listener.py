# To run: python manage.py mqtt_listener

import logging
import signal
import socket
import sys
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand

import paho.mqtt.client as mqtt

from farm_monitoring.services.mqtt_ingest import IngestError, ingest_measurement

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Subscribe to MQTT measurement topic and persist sensor readings to the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default=settings.MQTT_HOST,
            help=f"MQTT broker host (default from settings: {settings.MQTT_HOST})",
        )
        parser.add_argument(
            '--port',
            type=int,
            default=settings.MQTT_PORT,
            help=f"MQTT broker port (default from settings: {settings.MQTT_PORT})",
        )

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        prefix = settings.MQTT_TOPIC_PREFIX
        qos = settings.MQTT_QOS
        topic = f"{prefix}/+/measurement"
        client_id = f"{settings.MQTT_CLIENT_ID_PREFIX}-listener-{uuid.uuid4().hex[:8]}"

        client = mqtt.Client(
            client_id=client_id,
            clean_session=False,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        client.reconnect_delay_set(min_delay=1, max_delay=60)

        def on_connect(c, userdata, flags, reason_code, properties):
            if reason_code == 0:
                self.stdout.write(self.style.SUCCESS(
                    f"Connected to MQTT broker at {host}:{port}, subscribing to {topic!r} (QoS {qos})"
                ))
                c.subscribe(topic, qos=qos)
            else:
                self.stderr.write(self.style.ERROR(
                    f"Connection failed: reason_code={reason_code}"
                ))

        def on_disconnect(c, userdata, flags, reason_code, properties):
            self.stderr.write(self.style.WARNING(
                f"Disconnected from broker (reason_code={reason_code}). Auto-reconnecting…"
            ))

        def on_message(c, userdata, msg):
            try:
                result = ingest_measurement(msg.topic, msg.payload)
            except IngestError as e:
                self.stderr.write(self.style.WARNING(
                    f"[skip] {msg.topic}: {e}"
                ))
                return
            except Exception as e:
                logger.exception("Unexpected error while processing %s", msg.topic)
                self.stderr.write(self.style.ERROR(
                    f"[error] {msg.topic}: {e!r}"
                ))
                return

            self.stdout.write(
                f"[ok] {result.sensor_serial} = {result.value} @ {result.timestamp.isoformat()} "
                f"(measurement_id={result.measurement_id})"
            )

        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        def stop(_signum, _frame):
            self.stdout.write("\nStopping MQTT listener…")
            client.disconnect()
            sys.exit(0)

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        try:
            client.connect(host, port, keepalive=60)
        except (socket.gaierror, ConnectionRefusedError, OSError) as e:
            self.stderr.write(self.style.ERROR(
                f"Cannot connect to MQTT broker at {host}:{port}: {e}\n"
                f"Чи запущено Mosquitto? Спробуй: docker compose up -d"
            ))
            sys.exit(1)

        client.loop_forever()

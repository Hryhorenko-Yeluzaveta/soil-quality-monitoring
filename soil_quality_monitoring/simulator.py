import json
import os
import random
import sys
import time
import uuid

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv

load_dotenv()

URL_SENSORS = 'http://127.0.0.1:8000/api/sensors'
HEADERS = {
    'X-API-Key': os.getenv('IOT_API_KEY'),
    'Content-Type': 'application/json',
}

MQTT_HOST = os.getenv('MQTT_HOST', '127.0.0.1')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC_PREFIX = os.getenv('MQTT_TOPIC_PREFIX', 'farm/sensors')
MQTT_QOS = int(os.getenv('MQTT_QOS', '1'))
MQTT_CLIENT_ID = f"{os.getenv('MQTT_CLIENT_ID_PREFIX', 'smartfarm')}-simulator-{uuid.uuid4().hex[:8]}"

PUBLISH_INTERVAL_SECONDS = 60
RAIN_PROBABILITY = 0.05

ENVIRONMENT = {
    'TEMP': 20.0,
    'HUM': 50.0,
}

temp_sensors: list[str] = []
hum_sensors: list[str] = []
ph_sensors: list[str] = []
nit_sensors: list[str] = []
ph_states: dict[str, float] = {}
nit_states: dict[str, float] = {}


def initialize_sensors():
    global temp_sensors, hum_sensors, ph_sensors, nit_sensors
    temp_sensors.clear()
    hum_sensors.clear()
    ph_sensors.clear()
    nit_sensors.clear()

    response = requests.get(URL_SENSORS, headers=HEADERS, timeout=5)
    if response.status_code == 404:
        return
    response.raise_for_status()
    active_sensors = response.json()['sensors']

    last_values_temp = []
    last_values_hum = []
    for sensor in active_sensors:
        sn = sensor['serial_number']
        lv = sensor['last_value']
        match sensor['type']:
            case 'TEMP':
                temp_sensors.append(sn)
                if lv is not None:
                    last_values_temp.append(lv)
            case 'HUM':
                hum_sensors.append(sn)
                if lv is not None:
                    last_values_hum.append(lv)
            case 'PH':
                ph_sensors.append(sn)
                if lv is not None:
                    ph_states[sn] = lv
            case 'NIT':
                nit_sensors.append(sn)
                if lv is not None:
                    nit_states[sn] = lv

    active_ph = set(ph_sensors)
    active_nit = set(nit_sensors)
    for sn in list(ph_states.keys()):
        if sn not in active_ph:
            ph_states.pop(sn, None)
    for sn in list(nit_states.keys()):
        if sn not in active_nit:
            nit_states.pop(sn, None)

    if last_values_temp:
        ENVIRONMENT['TEMP'] = sum(last_values_temp) / len(last_values_temp)
    if last_values_hum:
        ENVIRONMENT['HUM'] = sum(last_values_hum) / len(last_values_hum)


def get_start_value(current_values, default_value):
    if current_values:
        return sum(current_values) / len(current_values)
    return default_value


def generate_measurement_temperature(client):
    for sn in temp_sensors:
        value = ENVIRONMENT['TEMP'] + random.uniform(-1, 1)
        value = max(-20.0, min(40.0, value))
        publish_measurement(client, sn, value)


def generate_measurement_humidity(client):
    for sn in hum_sensors:
        value = ENVIRONMENT['HUM'] + random.uniform(-1.5, 1.5)
        value = max(0.0, min(100.0, value))
        publish_measurement(client, sn, value)


def generate_measurement_ph(client):
    for sn in ph_sensors:
        if sn not in ph_states:
            ph_states[sn] = get_start_value(ph_states.values(), 7.0)
        ph_states[sn] += random.uniform(-0.2, 0.2)
        ph_states[sn] = max(0.0, min(14.0, ph_states[sn]))
        publish_measurement(client, sn, ph_states[sn])


def generate_measurement_nitrogen(client):
    for sn in nit_sensors:
        if sn not in nit_states:
            nit_states[sn] = get_start_value(nit_states.values(), 45.0)
        nit_states[sn] -= random.uniform(0.5, 1)
        if nit_states[sn] < 0.0:
            nit_states[sn] = 0.0
        publish_measurement(client, sn, nit_states[sn])


def publish_measurement(client: mqtt.Client, serial_number: str, value: float):
    topic = f"{MQTT_TOPIC_PREFIX}/{serial_number}/measurement"
    payload = json.dumps({'value': round(value, 2)})
    info = client.publish(topic, payload, qos=MQTT_QOS)
    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        print(f"[publish error] {topic}: rc={info.rc}", file=sys.stderr)


def build_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.reconnect_delay_set(min_delay=1, max_delay=60)

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[mqtt] Connected to {MQTT_HOST}:{MQTT_PORT}")
        else:
            print(f"[mqtt] Connection failed: reason_code={reason_code}", file=sys.stderr)

    def on_disconnect(c, userdata, flags, reason_code, properties):
        print(f"[mqtt] Disconnected (reason_code={reason_code}); will auto-reconnect", file=sys.stderr)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


def main():
    client = build_mqtt_client()
    try:
        while True:
            try:
                initialize_sensors()

                generate_measurement_temperature(client)
                ENVIRONMENT['TEMP'] += random.uniform(-2.0, 2.5)
                ENVIRONMENT['TEMP'] = max(-20.0, min(40.0, ENVIRONMENT['TEMP']))

                generate_measurement_humidity(client)
                if random.random() < RAIN_PROBABILITY:
                    ENVIRONMENT['HUM'] += random.uniform(25.0, 35.0)
                else:
                    ENVIRONMENT['HUM'] -= random.uniform(0.1, 2)
                ENVIRONMENT['HUM'] = max(0.0, min(100.0, ENVIRONMENT['HUM']))

                generate_measurement_nitrogen(client)
                generate_measurement_ph(client)

                time.sleep(PUBLISH_INTERVAL_SECONDS)
            except requests.RequestException as e:
                print(f"[fetch error] /api/sensors: {e}", file=sys.stderr)
                time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n[shutdown] stopping simulator…")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == '__main__':
    main()

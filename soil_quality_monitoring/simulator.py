import random
import time
import requests

URL_SEND_MEASUREMENT = 'http://127.0.0.1:8000/api/measurement'
URL_SENSORS = 'http://127.0.0.1:8000/api/sensors'
RAIN_PROBABILITY = 0.05
ENVIRONMENT = {
    'TEMP': 20.0,
    'HUM': 50.0,
}

temp_sensors = []
hum_sensors = []
ph_sensors = []
nit_sensors = []
ph_states = {}
nit_states = {}

def initialize_sensors():
    global temp_sensors, hum_sensors, ph_sensors, nit_sensors, nit_states, ph_states
    temp_sensors.clear()
    hum_sensors.clear()
    ph_sensors.clear()
    nit_sensors.clear()
    ph_states.clear()
    nit_states.clear()

    active_sensors = requests.get(URL_SENSORS).json()['sensors']
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

    if len(last_values_temp) != 0:
        ENVIRONMENT['TEMP'] = sum(last_values_temp) / len(last_values_temp)
    if len(last_values_hum) != 0:
        ENVIRONMENT['HUM'] = sum(last_values_hum) / len(last_values_hum)

def get_start_value(current_values, default_value):
    if current_values:
        return sum(current_values) / len(current_values)
    else:
        return default_value

def generate_measurement_temperature():
    for temp_sensor in temp_sensors:
        temp_variation = random.uniform(-1, 1)
        temp_value = ENVIRONMENT['TEMP'] + temp_variation
        if temp_value > 40.0: temp_value = 40.0
        if temp_value < -20.0: temp_value = -20.0
        save_measurement(temp_sensor, temp_value)

def generate_measurement_humidity():
    for hum_sensor in hum_sensors:
        hum_sensor_variation = random.uniform(-1.5, 1.5)
        hum_value = ENVIRONMENT['HUM'] + hum_sensor_variation
        if hum_value > 100.0: hum_value = 100.0
        if hum_value < 0: hum_value = 0.0
        save_measurement(hum_sensor, hum_value)

def generate_measurement_ph():
    for ph_sensor in ph_sensors:
        if ph_sensor not in ph_states:
            ph_states[ph_sensor] = get_start_value(ph_states.values(), 7.0)
        ph_states[ph_sensor] += random.uniform(-0.2, 0.2)
        if ph_states[ph_sensor] > 14.0: ph_states[ph_sensor] = 14.0
        save_measurement(ph_sensor, ph_states[ph_sensor])

def generate_measurement_nitrogen():
    for nit_sensor in nit_sensors:
        if nit_sensor not in nit_states:
            nit_states[nit_sensor] = get_start_value(nit_states.values(), 45.0)
        nit_states[nit_sensor] -= random.uniform(0.5, 1)
        if nit_states[nit_sensor] < 0.0: nit_states[nit_sensor] = 0.0
        save_measurement(nit_sensor, nit_states[nit_sensor])


def save_measurement(serial_number, value):
    measurement = {'serial_number': serial_number, 'value': round(value, 2)}
    res = requests.post(URL_SEND_MEASUREMENT, json=measurement)
    if res.status_code != 201:
        print(f"Помилка: {res.text}")
    print(f'Статус: {res.status_code}')

if __name__ == '__main__':
    while True:
        try:
            initialize_sensors()
            generate_measurement_temperature()
            ENVIRONMENT['TEMP'] += random.uniform(-2.0, 2.5)
            if ENVIRONMENT['TEMP'] > 40.0: ENVIRONMENT['TEMP'] = 40.0
            if ENVIRONMENT['TEMP'] < -20.0: ENVIRONMENT['TEMP'] = -20.0

            generate_measurement_humidity()
            is_raining = random.random() < RAIN_PROBABILITY
            if is_raining:
                ENVIRONMENT['HUM'] += random.uniform(25.0, 35.0)
            else:
                ENVIRONMENT['HUM'] -= random.uniform(0.1, 2)
            if ENVIRONMENT['HUM'] > 100.0: ENVIRONMENT['HUM'] = 100.0
            if ENVIRONMENT['HUM'] < 0: ENVIRONMENT['HUM'] = 0.0

            generate_measurement_nitrogen()
            generate_measurement_ph()

            time.sleep(60)
        except KeyboardInterrupt:
            break
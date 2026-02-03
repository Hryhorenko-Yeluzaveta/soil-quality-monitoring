from django.http import JsonResponse
from django.shortcuts import render
import json

from django.views.decorators.csrf import csrf_exempt

from farm_monitoring.models import Measurement, Sensor

@csrf_exempt
def add_measurement(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sensor = Sensor.objects.get(serial_number=data['serial_number'])
            measurement = Measurement.objects.create(sensor=sensor, value=data['value'])
            measurement.save()
            return JsonResponse({'message': 'Measurement added'}, status=201)
        except Sensor.DoesNotExist:
            return JsonResponse({"error": "Sensor not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Only POST allowed"}, status=405)

def get_active_sensors(request):
    sensors = Sensor.objects.filter(is_active=True)
    if not sensors:
        return JsonResponse({"message": "There are no sensors yet"}, status=404)
    data = []
    for s in sensors:
        last_measurement = Measurement.objects.filter(sensor=s).order_by('-timestamp').first()
        if last_measurement:
            data.append({
                'serial_number': s.serial_number,
                'type': s.type,
                'last_value': last_measurement.value,
            })
        else:
            data.append({
                'serial_number': s.serial_number,
                'type': s.type,
                'last_value': None,
            })
    return JsonResponse({'sensors': data}, status=200)

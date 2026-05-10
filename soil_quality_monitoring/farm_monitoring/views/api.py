import os
from django.http import JsonResponse

from farm_monitoring.models import Measurement, Sensor


def get_active_sensors(request):
    if request.headers.get('X-API-Key') != os.getenv('IOT_API_KEY'):
        return JsonResponse({"error": "Unauthorized device"}, status=403)

    sensors = Sensor.objects.filter(is_active=True, archived=False)
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

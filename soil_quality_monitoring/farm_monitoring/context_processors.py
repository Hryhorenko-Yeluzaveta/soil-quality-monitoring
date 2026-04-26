from farm_monitoring.services.farm_map_image import get_farm_map_image_url


def farm_map_background(request):
    return {'farm_map_bg_url': get_farm_map_image_url()}

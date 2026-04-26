import hashlib
import logging
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GOOGLE_STATIC_MAPS_URL = 'https://maps.googleapis.com/maps/api/staticmap'
CACHE_SUBDIR = 'farm_maps'


def _fingerprint() -> str:
    lat, lng = settings.FARM_MAP_CENTER
    width, height = settings.FARM_MAP_SIZE
    raw = (
        f'{lat}_{lng}_{settings.FARM_MAP_ZOOM}'
        f'_{settings.FARM_MAP_TYPE}_{width}x{height}@{settings.FARM_MAP_SCALE}'
    )
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _cache_path() -> Path:
    cache_dir = Path(settings.MEDIA_ROOT) / CACHE_SUBDIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f'{_fingerprint()}.png'


def _cache_url() -> str:
    return f'{settings.MEDIA_URL}{CACHE_SUBDIR}/{_fingerprint()}.png'


def _download(target: Path) -> bool:
    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning('GOOGLE_MAPS_API_KEY is not set; farm map background unavailable.')
        return False

    lat, lng = settings.FARM_MAP_CENTER
    width, height = settings.FARM_MAP_SIZE

    params = {
        'center': f'{lat},{lng}',
        'zoom': settings.FARM_MAP_ZOOM,
        'size': f'{width}x{height}',
        'scale': settings.FARM_MAP_SCALE,
        'maptype': settings.FARM_MAP_TYPE,
        'key': settings.GOOGLE_MAPS_API_KEY,
    }

    try:
        response = requests.get(GOOGLE_STATIC_MAPS_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error('Failed to download farm map: %s', exc)
        return False

    target.write_bytes(response.content)
    return True


def get_farm_map_image_url() -> str | None:
    target = _cache_path()
    if target.exists():
        return _cache_url()
    if _download(target):
        return _cache_url()
    return None

import uuid

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render

from ..services import build_family_chart_data, resolve_main_person_id
from ..utils import register_genealogy_cache

# Versioned cache key: bump the suffix whenever the serialized data shape changes
# so stale entries (older schema) are orphaned and allowed to expire.
CACHE_KEY_FAMILY_CHART_DATA = "genealogy_family_chart_data_v2"
register_genealogy_cache(CACHE_KEY_FAMILY_CHART_DATA)


def family_chart_view(request, main_person_id=None):
  return render(request, "genealogy/family_chart.html", {"main_person_id": main_person_id})


def family_chart_data(request):
  main_person_id = resolve_main_person_id(request.GET.get("main_person_id"))

  if not main_person_id:
    return JsonResponse([], safe=False)

  # Cache versioning: CACHE_KEY_FAMILY_CHART_DATA stores the current generation UUID.
  # When clear_genealogy_caches is called, it deletes this key, causing a new UUID to be generated,
  # effectively invalidating all specific person caches.
  cache_version = cache.get(CACHE_KEY_FAMILY_CHART_DATA)
  if not cache_version:
    cache_version = str(uuid.uuid4())
    cache.set(CACHE_KEY_FAMILY_CHART_DATA, cache_version, 3600 * 24)

  specific_cache_key = f"{CACHE_KEY_FAMILY_CHART_DATA}_{main_person_id}_{cache_version}"
  data = cache.get(specific_cache_key)
  if data is None:
    data = build_family_chart_data(main_person_id)
    cache.set(specific_cache_key, data, 3600)
  return JsonResponse(data, safe=False)

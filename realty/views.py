#  Copyright 2017 Google Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import json

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.serializers import serialize
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render

from .models import Property


def properties_geojson(request):
    """
    Retrieves properties given the querystring params, and 
    returns them as GeoJSON.
    """
    ne = request.GET["ne"].split(",")
    sw = request.GET["sw"].split(",")
    lookup = {
        "point__contained": Polygon.from_bbox((sw[1], sw[0], ne[1], ne[0])),
        "bedrooms__gte": request.GET["min-bedrooms"],
        "bedrooms__lte": request.GET["max-bedrooms"],
        "bathrooms__gte": request.GET["min-bathrooms"],
        "car_spaces__gte": request.GET["min-car-spaces"],
        "property_type__in": request.GET["property-types"].split(",")
    }
    if request.GET["nearest-school"] != "1":
        lookup["nearest_school_distance__lt"] = int(request.GET["nearest-school"]) - 1
    if request.GET["nearest-train-station"] != "1":
        lookup["nearest_train_station_distance__lt"] = int(request.GET["nearest-train-station"]) - 1

    properties = Property.objects.filter(**lookup)
    json = serialize("geojson", properties, geometry_field="point")

    return HttpResponse(json, content_type="application/json")


def properties_map(request):
    """
    Index page for the app, with map + form for filtering 
    properties.
    """
    # Get the center of all properties, for centering the map.
    
    if Property.objects.exists():
        cursor = connection.cursor()
        cursor.execute("SELECT ST_AsText(st_centroid(st_union(point))) FROM realty_property")
        center = dict(zip(("lng", "lat"), GEOSGeometry(cursor.fetchone()[0]).get_coords()))
    else:
        # Default, when no properties exist.
        center = {"lat": -33.864869, "lng": 151.1959212}

    context = {
        "center": json.dumps(center),
        "title": "Property Finder",
        "api_key": settings.GOOGLE_MAPS_API_WEB_KEY,
        "property_types": Property._meta.get_field("property_type").choices,
        "distance_range": (1, 21),
    }

    # Ranges for each of the slider fields.
    for field in ["bedrooms", "bathrooms", "car_spaces"]:
        choices = Property._meta.get_field("bedrooms").choices
        context[field + "_range"] = (choices[0][0], choices[-1][0])

    return render(request, "map.html", context)
    
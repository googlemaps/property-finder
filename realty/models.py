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

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from geopy.distance import distance
from googlemaps import Client


class Property(models.Model):

    PROPERTY_CAR_SPACES_CHOICES = [(i, i) for i in range(0, 4)]
    PROPERTY_BEDROOMS_CHOICES = [(i, i) for i in range(1, 5)]
    PROPERTY_BATHROOMS_CHOICES = [(i, i) for i in range(1, 5)]
    PROPERTY_TYPE_CHOICES = (
        (1, 'House'),
        (2, 'Townhouse'),
        (3, "Apartment"),
        (4, 'Studio'),
    )

    class Meta:
        verbose_name_plural = "Properties"

    address = models.CharField(max_length=200)
    description = models.TextField()
    car_spaces = models.IntegerField(choices=PROPERTY_CAR_SPACES_CHOICES, default=1)
    bedrooms = models.IntegerField(choices=PROPERTY_BEDROOMS_CHOICES, default=3)
    bathrooms = models.IntegerField(choices=PROPERTY_BATHROOMS_CHOICES, default=2)
    property_type = models.IntegerField(choices=PROPERTY_TYPE_CHOICES, default=1)
    nearest_school = models.CharField(max_length=1000, null=True)
    nearest_school_distance = models.FloatField(null=True)
    nearest_train_station = models.CharField(max_length=1000, null=True)
    nearest_train_station_distance = models.FloatField(null=True)
    point = models.PointField(srid=4326, null=True, unique=True)
    
    def __str__(self):
        return self.address
        
    def set_google_maps_fields(self, latlng=None):
        """
        Uses the Google Maps API to set:
          - geocoded latlng
          - nearest school name + distance
          - nearest train station name + distance
        """
        client = Client(key=settings.GOOGLE_MAPS_API_SERVER_KEY)
        if not latlng:
            data = client.geocode(self.address)
            if not data:
                raise Exception("Unable to resolve the address: '%s'" % address)
            latlng = data[0]["geometry"]["location"]
        self.point = GEOSGeometry("POINT(%(lng)s %(lat)s)" % latlng)

        error = ""
        for field in ("school", "train_station"):
            try:
                place = client.places_nearby(location=latlng, rank_by="distance", type=field)["results"][0]
            except IndexError:
                continue
            except Exception as e:
                error = e
                continue
            setattr(self, "nearest_%s" % field, place["name"])
            place_latlng = place["geometry"]["location"]
            d = distance((latlng["lat"], latlng["lng"]), (place_latlng["lat"], place_latlng["lng"])).km
            setattr(self, "nearest_%s_distance" % field, round(d, 2))
        if error:
            raise Exception(error)

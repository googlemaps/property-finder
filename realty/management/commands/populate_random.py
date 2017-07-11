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

import random

from django.conf import settings
from django.core.management.base import BaseCommand
import googlemaps

from realty.models import Property


class Command(BaseCommand):
    """
    Utility for populating the database with random (real) locations.
    """

    def add_arguments(self, parser):
        parser.add_argument("--num", action="store", dest="num", default=500, type=int,
            help="Number of records to add - note that each record will use Google's reverse "
                 "geocoding API and Places API, counting towards up to 3 requests per record "
                 "against your daily quota.")
        parser.add_argument("--center", action="store", dest="center", default="-33.864869,151.1959212",
            help="Center of area where locations will be randomly drawn from, eg: --center %(default)s")
        parser.add_argument("--delete", action="store_true", dest="delete",
            help="Delete existing records before populating.")

    def handle(self, **options):
    
        client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_SERVER_KEY)
        properties = []
        start_lat, start_lng = map(float, options["center"].split(","))
        step = {"lat": 3.0, "lng": 5.0}
        seen = set()
        
        for i in range(options["num"] + 1, 1, -1):
            # Random latlng within a boundary that grows out from the center 
            # as iteration occurs.
            latlng = {
                "lat": random.uniform(start_lat + (step["lat"]/i), start_lat - (step["lat"]/i)),
                "lng": random.uniform(start_lng - (step["lng"]/i), start_lng + (step["lng"]/i)),
            }
            try:
                result = client.reverse_geocode(latlng)[0]
                address = result["formatted_address"]
                latlng = result["geometry"]["location"]
            except Exception as e:
                print "Error: %s" % e
                continue
            # Resolved addresses aren't always postal addresses - they could represent a landmark
            # or area of some sort. Sticking with addresses that being with a digit works 
            # reasonably well.
            if not address[0].isdigit():
                print "Skipping non-postal address: %s" % address
                continue
            # Discard duplicates
            if address in seen:
                print "Skipping duplicate address: %s" % address
                continue
            seen.add(address)
            property = Property(address=address)
            property.set_google_maps_fields(latlng=latlng)
            # Set a random value for each of the range fields.
            for field in ("bedrooms", "bathrooms", "car_spaces", "property_type"):
                setattr(property, field, random.choice(Property._meta.get_field(field).choices)[0])
            property.description = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut 
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco 
laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in 
voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat 
non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""
            properties.append(property)
            print "Resolved %s" % address
        
        if options["delete"]:
            print "Deleting %s old properties" % Property.objects.count()
            Property.objects.all().delete()
        Property.objects.bulk_create(properties)
        print "Inserted %s properties" % len(properties)

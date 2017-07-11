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

from django.contrib.gis import admin
from django.contrib.messages import error
from django.db import models
from django.forms.widgets import RadioSelect

from .models import Property


class PropertyAdmin(admin.ModelAdmin):

    search_fields = ["address", "description"]
    list_display = ["address", "bedrooms", "bathrooms", "car_spaces", "property_type"]
    list_filter = ["bedrooms", "bathrooms", "car_spaces", "property_type"]
    readonly_fields = ["point", "nearest_school", "nearest_school_distance", 
                       "nearest_train_station", "nearest_train_station_distance"]
    icon = '<i class="material-icons">location_city</i>'
    radio_fields = {
        "bedrooms": admin.HORIZONTAL,
        "bathrooms": admin.HORIZONTAL,
        "car_spaces": admin.HORIZONTAL,
        "property_type": admin.HORIZONTAL,
    }

    def save_model(self, request, obj, form, change):
        # If the address was changed, geocode it and store the 
        # resolved latlng.
        super(PropertyAdmin, self).save_model(request, obj, form, change)
        if form.data.get("address", "") != form.initial.get("address", ""):
            try:
                obj.set_google_maps_fields()
                obj.save()
            except Exception as e:
                error(request, e)


admin.site.register(Property, PropertyAdmin)

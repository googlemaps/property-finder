/*
  Copyright 2017 Google Inc.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

const mapStyle = [
  {"featureType": "administrative", "elementType": "labels.text.fill", "stylers": [{"color": "#444444"}]},
  {"featureType": "landscape", "elementType": "all", "stylers": [{"color": "#f2f2f2"}]},
  {"featureType": "poi", "elementType": "all", "stylers": [{"visibility": "off"}]},
  {"featureType": "poi", "elementType": "labels.icon", "stylers": [{"visibility": "off"}]},
  {"featureType": "poi.school", "elementType": "all", "stylers": [{"visibility": "on"}, {"hue": "#ff0000"}, {"gamma": "0.70"}, {"weight": "2.41"}, {"saturation": "34"}, {"lightness": "1"}]},
  {"featureType": "poi.school", "elementType": "geometry", "stylers": [{"visibility": "on"}]},
  {"featureType": "poi.school", "elementType": "labels.icon", "stylers": [{"visibility": "on"}]},
  {"featureType": "road", "elementType": "all", "stylers": [{"saturation": -100}, {"lightness": 45}]},
  {"featureType": "road", "elementType": "labels.text", "stylers": [{"weight": "1.74"}, {"visibility": "on"}]},
  {"featureType": "road", "elementType": "labels.text.fill", "stylers": [{"visibility": "on"}, {"color": "#635c5c"}]},
  {"featureType": "road.highway", "elementType": "all", "stylers": [{"visibility": "simplified"}]},
  {"featureType": "road.arterial", "elementType": "labels.icon", "stylers": [{"visibility": "off"}]},
  {"featureType": "transit", "elementType": "all", "stylers": [{"visibility": "off"}]},
  {"featureType": "water", "elementType": "all", "stylers": [{"color": "#78bdd9"}, {"visibility": "on"}]}
];

function initMap() {

  const sliders = document.querySelectorAll('.mdl-slider');
  const spinner = document.querySelector('.mdl-spinner');
  const map = new google.maps.Map(document.querySelector('#map'), {
    zoom: 14,
    center: window.mapCenter,
    styles: mapStyle
  });
  
  // Hide the markers rendered via map.data.loadGeoJson, since we'll add markers 
  // seperately with MarkerClusterer.
  map.data.setStyle(() => ({visible: false}));

  // Info window will show a property's information when its marker is clicked.
  const infoWindow = new google.maps.InfoWindow();
  infoWindow.setOptions({pixelOffset: new google.maps.Size(0, -30)});

  // We call map.data.loadGeoJson every time the bounds_changed event is triggered, 
  // which sometimes can occur multiple times very quickly in succession, so we 
  // only do this inside a function run via setTimeout, which is cancelled each 
  // time the event is triggered. timeoutHandler stores the handler for this.
  let timeoutHandler = 0;
  
  // MarkerClusterer instance which we store to allow us to call clearMarkers 
  // on it, each time the property data is received after map.data.loadGeoJson
  // being called.
  let markerCluster = null;
  
  // Stores the bounds used for retrieving data, so that when the bounds_changed 
  // event is triggered, we don't request new data if the new bounds fall within 
  // dataBounds, for example when zooming in.
  let dataBounds = null;
  
  // Loads properties via map.data.loadGeoJson inside a setTimeout handler, which is 
  // cancelled each time loadProperties is called.
  function loadProperties() {

    // Show the loading spinner.
    spinner.classList.add('is-active');

    clearTimeout(timeoutHandler);
    timeoutHandler = setTimeout(() => {
      
      // For retrieving data, use a larger (2x) bounds than the actual map bounds,
      // which will allow for some movement of the map, or one level of zooming 
      // out, without needed to load new data.
      const ne = map.getBounds().getNorthEast();
      const sw = map.getBounds().getSouthWest();
      const extendedLat = ne.lat() - sw.lat();
      const extendedLng = ne.lng() - sw.lng();
      dataBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(sw.lat() - extendedLat, sw.lng() - extendedLng),
        new google.maps.LatLng(ne.lat() + extendedLat, ne.lng() + extendedLng)
      );

      // Build the querystring of parameters to use in the URL given to 
      // map.data.loadGeoJson, which consists of the various form field 
      // values and the current bounding box.
      const params = {
        ne: dataBounds.getNorthEast().toUrlValue(),
        sw: dataBounds.getSouthWest().toUrlValue()
      };
      Array.prototype.forEach.call(sliders, (item) => params[item.id] = item.value);
      const types = document.querySelectorAll('input[name="property-types"]:checked');
      params['property-types'] = Array.prototype.map.call(types, (item) => item.value).join(',');
      const url = window.propertiesGeoJsonUrl + '?' + Object.keys(params).map((k) => k + '=' + params[k]).join('&');

      map.data.loadGeoJson(url, null, (features) => {

        // Set the value in the "Total properties: x" text.
        document.querySelector('#total-text').innerHTML = features.length;
        // Hide the loading spinner.
        spinner.classList.remove('is-active');
        // Clear the previous marker cluster.
        if (markerCluster !== null) {
          markerCluster.clearMarkers();
        }

        // Build an array of markers, one per property.
        const markers = features.map((feature) => {

          const marker = new google.maps.Marker({
            position: feature.getGeometry().get(0),
            icon: window.imagePath + 'marker.png'
          });

          // Show the property's details in the infowindow when 
          // the marker is clicked.
          marker.addListener('click', () => {
            const position = feature.getGeometry().get();
            let content = `
            <div>
              <img src="https://maps.googleapis.com/maps/api/streetview?size=200x200&location=${position.lat()},${position.lng()}&key=${window.apiKey}">
              <h2>${feature.getProperty('address')}</h2>
              <p>${feature.getProperty('description')}</p>
              <ul>
                <li>Bedrooms: ${feature.getProperty('bedrooms')}</li>
                <li>Bathrooms: ${feature.getProperty('bathrooms')}</li>
                <li>Car spaces: ${feature.getProperty('car_spaces')}</li>
            `;
            const nearestSchool = feature.getProperty('nearest_school');
            if (nearestSchool) {
              content += `<li>Nearest school: ${nearestSchool} (${feature.getProperty('nearest_school_distance')} kms)</li>`;
            }
            const nearestTrainStation = feature.getProperty('nearest_train_station');
            if (nearestTrainStation) {
              content += `<li>Nearest train station: ${nearestTrainStation} (${feature.getProperty('nearest_train_station_distance')} kms)</li>`;
            }
            content += '</ul></div>';
            infoWindow.setContent(content);
            infoWindow.setPosition(position);
            infoWindow.open(map);             
          });

          return marker;
        });
        
        // Build the marker clusterer.
        markerCluster = new MarkerClusterer(map, markers, {
          styles: [1, 2, 3].map(i => ({
            url: window.imagePath + `cluster${i}.png`, 
            width: 24+(24*i), 
            height: 24+(24*i), 
            textColor: '#fff', 
            textSize: 12+(4*i)
          }))
        });
      });      

    }, 100);
  }
  
  // Refresh data each time the map bounds change, and fall outside the 
  // bounds of currently loaded data.
  google.maps.event.addListener(map, 'bounds_changed', () => {
    if (dataBounds === null || 
          !dataBounds.contains(map.getBounds().getNorthEast()) ||
          !dataBounds.contains(map.getBounds().getSouthWest())) {
      loadProperties();
    }
  });
  
  // Refresh data each time one of the sliders change.
  Array.prototype.forEach.call(sliders, item => 
    item.addEventListener('input', () => {
      loadProperties();
      // Also update the slider's text.
      let value = Number(item.value);
      if (item.id.indexOf('nearest') === 0) {
        value = value === 1 ? 'Any' : (value-1) + 'km';
      }
      document.querySelector(`#${item.id}-text`).innerHTML = value;
    })
  );
  
  // Refresh data when the "property types" checkboxes change.
  const types = document.querySelectorAll('input[name="property-types"]');
  Array.prototype.forEach.call(types, item => item.addEventListener('change', loadProperties));

}
// Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ';

// Initialize the map
var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/dark-v11', 
    center: [121.54, 25.044],
    zoom: 12,
    pitch: 0,
    bearing: 0
});

var showAllStations = false;

// Marker color categories
var markerColors = {
    low: '#808080', 
    medium: '#ffa500',
    high: '#00ff00'
};

// Function to create a marker with color and add it to the map
function createMarker(station, color, opacity) {
    var el = document.createElement('div');
    el.className = 'marker';
    el.style.backgroundColor = color;
    el.style.opacity = opacity;
    el.style.width = '6px';
    el.style.height = '6px';
    el.style.borderRadius = '50%';

    new mapboxgl.Marker(el)
        .setLngLat([station.longitude, station.latitude])
        .setPopup(new mapboxgl.Popup({ offset: 25 })
        .setHTML(`<b>${station.sna}</b><br>可用車輛：${station.available_rent_bikes} / ${station.total}`))
        .addTo(map);
}

// Function to update map markers
function updateMarkers() {
    
    fetch("/bike-stations")
        .then(response => response.json())
        .then(data => {
            data.forEach(station => {
                var ratio = station.available_rent_bikes / station.total;
                var color = '';
                var opacity = 1; // Declare and initialize opacity

                if (ratio < 0.4) {
                    color = markerColors.low;
                    opacity = 0;
                } else if (ratio >= 0.4 && ratio < 0.75) {
                    color = markerColors.medium;
                    opacity = 0.5;
                } else {
                    color = markerColors.high;
                    opacity = 1;
                }
                
                // Uncomment the following line if you want to filter markers based on ratio
                // if (ratio > 0.4){
                //     createMarker(station, color, opacity);
                // }

                createMarker(station, color, opacity); // Create marker with color and opacity
            });
        });
}

updateMarkers();

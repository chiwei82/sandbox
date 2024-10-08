var map = L.map('map').setView([25.065, 121.5454], 12);
var showAllStations = false

var redIcon = new L.Icon({
    iconUrl: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
    iconSize: [25, 25],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var orangeIcon = new L.Icon({
    iconUrl: 'https://maps.google.com/mapfiles/ms/icons/orange-dot.png',
    iconSize: [25, 25],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var greenIcon = new L.Icon({
    iconUrl: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
    iconSize: [25, 25],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var markers = [];

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

var markersCluster = L.markerClusterGroup();

function updateMarkers() {
    
    clearMarkers();
    markersCluster.clearLayers();

    if (showAllStations) {
        var districtSelect = document.getElementById('district-select');
        for (var i = 0; i < districtSelect.options.length; i++) {
            districtSelect.options[i].selected = true;
        }
        var statusFilter = document.getElementById('statusFilter');
        for (var i = 0; i < statusFilter.options.length; i++) {
            statusFilter.options[i].selected = true;
        }
    }
    
    var districtSelect = document.getElementById('district-select');
    var selectedDistricts = Array.from(districtSelect.selectedOptions).map(option => option.value);
    var selectedStatus = Array.from(document.getElementById('statusFilter').selectedOptions).map(option => option.value);
    var total_bike = 0;
    var available = 0;
    var rate = 0;
    var stationsWithRatio = [];

    fetch("/bike-stations")
        .then(response => response.json())
        .then(data => {
            data.forEach(station => {
                var lat = station.latitude;
                var lon = station.longitude;
                var stationName = station.sna;
                var availableBikes = station.available_rent_bikes;
                var totalSlots = station.total;
                var infoTime = station.infoTime;

                var ratio = availableBikes / totalSlots;
                var icon = null;

                if (ratio < 0.4 && selectedStatus.includes('low')) {
                    icon = redIcon;
                } else if (ratio >= 0.4 && ratio < 0.75 && selectedStatus.includes('medium')) {
                    icon = orangeIcon;
                } else if (ratio >= 0.75 && selectedStatus.includes('high')) {
                    icon = greenIcon;
                }

                if (icon && (showAllStations || (selectedDistricts.length === 0 || selectedDistricts.includes(station.sareaen)))) {
                    var marker = L.marker([lat, lon], { icon: icon })
                        .bindPopup(`
                        <b>${stationName}</b>
                        <br>可用車輛：${availableBikes} / ${totalSlots}
                        <br>更新時間: ${infoTime}`);
                    markersCluster.addLayer(marker);
                    markers.push(marker);
                    map.addLayer(markersCluster);

                    total_bike += totalSlots;
                    document.querySelector('#total_bike').innerText = total_bike;

                    available += availableBikes;
                    document.querySelector('#available').innerText = available;

                    rate = (available / total_bike) * 100;
                    rate = rate.toFixed(2);
                    document.querySelector('#rate').innerText = rate + '%';

                    stationsWithRatio.push({
                        name: stationName,
                        ratio: ratio,
                        rate: (ratio * 100).toFixed(2) + '%',
                        lat: lat,
                        lon: lon,
                        availableBikes: availableBikes,
                        infoTime: infoTime,
                        totalSlots: totalSlots,
                        icon: icon
                    });
                }
            });

            stationsWithRatio.sort((a, b) => b.ratio - a.ratio);

            var demographicsList = document.querySelector('.demographics ul');
            demographicsList.innerHTML = '';

            stationsWithRatio.forEach(station => {
                var listItem = document.createElement('li');
                listItem.innerHTML = `
                    <span class="station-name" style="cursor: pointer;">${station.name}</span>
                    <span>${station.rate}</span>
                `;
                

                listItem.querySelector('.station-name').addEventListener('click', function() {
                    var marker = L.marker([station.lat, station.lon])
                        .addTo(map)
                        .bindPopup(`
                        <b>${station.name}</b>
                        <br>可用車輛：${station.availableBikes} / ${station.totalSlots}
                        <br>更新時間: ${station.infoTime}`);

                    map.setView([station.lat, station.lon], 15);
                    marker.openPopup(); 
                });

                demographicsList.appendChild(listItem);
            });
        });
}


function show_all() {
    showAllStations = true;
    updateMarkers();
}
    

function updateTime() {
    fetch("/time")
        .then(response => response.text())
        .then(time => {
            document.querySelector('#time').innerText = time;
        })
        .catch(error => console.log('Error fetching time:', error));
}

// DOM 加載
document.addEventListener('DOMContentLoaded', function() {updateTime();});

document.getElementById('district-select').addEventListener('change', function() {
    showAllStations = false; 
    updateMarkers();
});

document.getElementById('statusFilter').addEventListener('change', function() {
    showAllStations = false; 
    updateMarkers();
});

// document.getElementById('show_all').addEventListener('click', show_all);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
}).addTo(map);

updateMarkers();

var stationData = [];
fetch("/bike-stations")
    .then(response => response.json())
    .then(data => {
        stationData = data;
    });


// search div
function searchStations(query) {
    var selectedDistricts = Array.from(document.getElementById('district-select').selectedOptions).map(option => option.value);
    var selectedStatus = Array.from(document.getElementById('statusFilter').selectedOptions).map(option => option.value);

    return stationData.filter(station => {
        var isInSelectedDistrict = selectedDistricts.length === 0 || selectedDistricts.includes(station.sareaen);
        var isInSelectedStatus = false;
        var ratio = station.available_rent_bikes / station.total;
        
        if (ratio < 0.4 && selectedStatus.includes('low')) {
            isInSelectedStatus = true;
        } else if (ratio >= 0.4 && ratio < 0.75 && selectedStatus.includes('medium')) {
            isInSelectedStatus = true;
        } else if (ratio >= 0.75 && selectedStatus.includes('high')) {
            isInSelectedStatus = true;
        }
        
        return station.sna.toLowerCase().includes(query.toLowerCase()) && isInSelectedDistrict && isInSelectedStatus;
    });
}

function updateSearchResults(results) {
    var searchResults = document.getElementById('search-results');
    searchResults.innerHTML = '';
    
    results.forEach(station => {
        var listItem = document.createElement('li');
        listItem.textContent = station.sna; 
        listItem.addEventListener('click', function() {
        
            map.setView([station.latitude, station.longitude], 24); 
            var marker = markers.find(m => m.getLatLng().lat === station.latitude && m.getLatLng().lng === station.longitude);
            if (marker) marker.openPopup(); 
            
            searchResults.innerHTML = '';
            document.getElementById('station-search').value = '';
        });

        searchResults.appendChild(listItem);
    });
}

document.getElementById('station-search').addEventListener('input', function() {
    var query = this.value;
    if (query.length > 0) {
        var matchingStations = searchStations(query); 
        updateSearchResults(matchingStations);
    } else {
        document.getElementById('search-results').innerHTML = '';
    }
});

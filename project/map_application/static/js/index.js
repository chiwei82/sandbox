var map = L.map('map').setView([25.065, 121.5454], 12);
var showAllStations = false;
var stationData = [];  // 用來緩存站點數據

// 定義不同狀態的標記顏色
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
var markersCluster = L.markerClusterGroup();

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    markersCluster.clearLayers();
}

// 抽取 API 請求邏輯，緩存站點數據
function fetchBikeStations() {
    if (stationData.length === 0) {
        return fetch("/bike-stations")
            .then(response => response.json())
            .then(data => {
                stationData = data;
                return data;
            });
    } else {
        return Promise.resolve(stationData);
    }
}

// 根據可用自行車比例返回相應的標記圖標
function getIconByRatio(ratio, selectedStatus) {
    if (ratio < 0.4 && selectedStatus.includes('low')) {
        return redIcon;
    } else if (ratio >= 0.4 && ratio < 0.75 && selectedStatus.includes('medium')) {
        return orangeIcon;
    } else if (ratio >= 0.75 && selectedStatus.includes('high')) {
        return greenIcon;
    }
    return null;
}

// 抽取獲取選中的區域和狀態的邏輯
function getSelectedDistricts() {
    return Array.from(document.getElementById('district-select').selectedOptions).map(option => option.value);
}

function getSelectedStatus() {
    return Array.from(document.getElementById('statusFilter').selectedOptions).map(option => option.value);
}

// 處理站點數據並更新標記和統計數據
function processStationData(station, selectedDistricts, selectedStatus) {
    var lat = station.latitude;
    var lon = station.longitude;
    var stationName = station.sna;
    var availableBikes = station.available_rent_bikes;
    var totalSlots = station.total;
    var infoTime = station.infoTime;

    var ratio = availableBikes / totalSlots;
    var icon = getIconByRatio(ratio, selectedStatus);

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
}

// 更新標記和統計數據
function updateMarkers() {
    clearMarkers();

    var selectedDistricts = getSelectedDistricts();
    var selectedStatus = getSelectedStatus();

    total_bike = 0;
    available = 0;
    stationsWithRatio = [];

    fetchBikeStations().then(data => {
        data.forEach(station => {
            processStationData(station, selectedDistricts, selectedStatus);
        });

        stationsWithRatio.sort((a, b) => b.ratio - a.ratio);
        updateDemographicsList();
    });
}

// 更新站點列表的顯示
function updateDemographicsList() {
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
}
function updateTime() { 
    fetch("/time")
    .then(response => response.text())
    .then(time => { document.querySelector('#time').innerText = time; }); }

// DOM 加載後自動調用
document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    updateMarkers();
});

document.getElementById('district-select').addEventListener('change', function() {
    showAllStations = false;
    updateMarkers();
});

document.getElementById('statusFilter').addEventListener('change', function() {
    showAllStations = false;
    updateMarkers();
});

// 地圖顯示層
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
}).addTo(map);

// 搜索站點
function searchStations(query) {
    var selectedDistricts = getSelectedDistricts();
    var selectedStatus = getSelectedStatus();

    return stationData.filter(station => {
        var isInSelectedDistrict = selectedDistricts.length === 0 || selectedDistricts.includes(station.sareaen);
        var ratio = station.available_rent_bikes / station.total;
        var isInSelectedStatus = (ratio < 0.4 && selectedStatus.includes('low')) ||
                                 (ratio >= 0.4 && ratio < 0.75 && selectedStatus.includes('medium')) ||
                                 (ratio >= 0.75 && selectedStatus.includes('high'));

        return station.sna.toLowerCase().includes(query.toLowerCase()) && isInSelectedDistrict && isInSelectedStatus;
    });
}

// 更新搜索結果
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

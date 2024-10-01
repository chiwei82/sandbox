var map = L.map('map').setView([25.0330, 121.5654], 14);
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

// 清除地圖上的標記
function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

// 更新地圖標記
function updateMarkers() {
    
    clearMarkers();

    if (showAllStations) {
        // 選擇所有區域
        var districtSelect = document.getElementById('district-select');
        for (var i = 0; i < districtSelect.options.length; i++) {
            districtSelect.options[i].selected = true;
        }
        // 選擇所有狀態
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

                // 如果 `showAllStations` 為 true，忽略篩選器並顯示所有站點
                if (icon && (showAllStations || (selectedDistricts.length === 0 || selectedDistricts.includes(station.sareaen)))) {
                    var marker = L.marker([lat, lon], { icon: icon })
                        .addTo(map)
                        .bindPopup(`
                        <b>${stationName}</b>
                        <br>可用車輛：${availableBikes} / ${totalSlots}
                        <br>更新時間: ${infoTime}`);
                    markers.push(marker);

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
                
                // 添加點擊事件監聽器，使地圖移動到該站點
                listItem.querySelector('.station-name').addEventListener('click', function() {
                    var marker = L.marker([station.lat, station.lon])
                        .addTo(map)
                        .bindPopup(`
                        <b>${station.name}</b>
                        <br>可用車輛：${station.availableBikes} / ${station.totalSlots}
                        <br>更新時間: ${station.infoTime}`);

                    map.setView([station.lat, station.lon], 15); // 根據需求調整縮放級別
                    marker.openPopup(); // 打開標記的 popup，顯示站點資訊
                });

                demographicsList.appendChild(listItem);
            });
        });
}

// 顯示使用者的目前位置並顯示所有站點
function showCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                var lat = position.coords.latitude;
                var lon = position.coords.longitude;

                // 在使用者的位置新增標記
                var currentLocationMarker = L.marker([lat, lon]).addTo(map)
                    .bindPopup('You are here!')
                    .openPopup();

                // 將地圖視野移到使用者位置
                map.setView([lat, lon], 15);

                // 設置為顯示所有站點
                showAllStations = true;
                updateMarkers(); // 顯示所有站點
                
            },
            function(error) {
                console.log('Error retrieving your location: ', error);
            }
        );
    } else {
        alert('Geolocation is not supported by your browser');
    }
}

// 顯示使用者的目前位置並顯示所有站點
function show_all() {
    // 設置為顯示所有站點
    showAllStations = true;
    updateMarkers(); // 顯示所有站點
}
    
// 當下拉選單變更時，更新標記
function updateTime() {
    fetch("/time")
        .then(response => response.text())
        .then(time => {
            document.querySelector('#time').innerText = time;
        })
        .catch(error => console.log('Error fetching time:', error));
}

document.addEventListener('DOMContentLoaded', function() {updateTime();});
// 當下拉選單變更時，按照篩選器顯示
document.getElementById('district-select').addEventListener('change', function() {
    showAllStations = false; // 如果篩選器變更，按照篩選條件顯示
    updateMarkers();
});

document.getElementById('statusFilter').addEventListener('change', function() {
    showAllStations = false; // 如果篩選器變更，按照篩選條件顯示
    updateMarkers();
});

// 設置點擊事件，當按下顯示我的位置按鈕時顯示所有站點
// document.getElementById('current_loc_button').addEventListener('click', showCurrentLocation);
document.getElementById('show_all').addEventListener('click', show_all);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

updateMarkers();

// 站點數據儲存
var stationData = [];

// 從伺服器獲取所有站點數據
fetch("/bike-stations")
    .then(response => response.json())
    .then(data => {
        stationData = data; // 儲存站點數據
    });

// 搜尋站點的函數
function searchStations(query) {
    var selectedDistricts = Array.from(document.getElementById('district-select').selectedOptions).map(option => option.value);
    var selectedStatus = Array.from(document.getElementById('statusFilter').selectedOptions).map(option => option.value);

    return stationData.filter(station => {
        var isInSelectedDistrict = selectedDistricts.length === 0 || selectedDistricts.includes(station.sareaen);
        var isInSelectedStatus = false;
        var ratio = station.available_rent_bikes / station.total;
        
        // 根據 ratio 判斷狀態
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

// 更新搜尋結果的顯示
function updateSearchResults(results) {
    var searchResults = document.getElementById('search-results');
    searchResults.innerHTML = ''; // 清空上次結果
    
    results.forEach(station => {
        var listItem = document.createElement('li');
        listItem.textContent = station.sna; // 顯示站點名稱
        listItem.addEventListener('click', function() {
        
            map.setView([station.latitude, station.longitude], 15); // 移動到站點
            var marker = markers.find(m => m.getLatLng().lat === station.latitude && m.getLatLng().lng === station.longitude);
            if (marker) marker.openPopup(); // 打開該站點的 popup
            
            searchResults.innerHTML = ''; // 清空結果列表
            document.getElementById('station-search').value = ''; // 清空搜尋框
        });

        searchResults.appendChild(listItem);
    });
}

// 監聽輸入框的鍵入事件
document.getElementById('station-search').addEventListener('input', function() {
    var query = this.value;
    if (query.length > 0) {
        var matchingStations = searchStations(query); // 搜尋匹配站名
        updateSearchResults(matchingStations); // 更新顯示匹配結果
    } else {
        document.getElementById('search-results').innerHTML = ''; // 清空結果
    }
});

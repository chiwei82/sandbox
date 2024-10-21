// Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ';

// 顯示加載動畫
function showLoadingSpinner() {
    document.getElementById('loading-spinner').style.display = 'block';
}

// 隱藏加載動畫
function hideLoadingSpinner() {
    document.getElementById('loading-spinner').style.display = 'none';
}

// Initialize the map with a function
function createMap(containerId, style, fetchPath) {
    var map = new mapboxgl.Map({
        container: containerId,
        style: style, 
        center: [121.54, 25.044],
        zoom: 12,
        pitch: 0,
        bearing: 0
    });

    // 顯示加載動畫
    showLoadingSpinner();

    map.on('load', function () {
        fetch(fetchPath)
          .then(response => response.json())
          .then(data => {
            const sumOfTxnTimesArray = data.features.map(feature => feature.properties.sum_of_txn_times);
            const maxSumOfTxnTimes = Math.max(...sumOfTxnTimesArray);

            console.log(containerId + " -> maxSumOfTxnTimes = " + maxSumOfTxnTimes);

            map.addSource('route_data', {
              'type': 'geojson',
              'data': data
            });

            // 添加一個簡單的點圖層來快速展示初始地圖
            map.addLayer({
              'id': 'initial-points',
              'type': 'circle',
              'source': 'route_data',
              'paint': {
                'circle-radius': 5,
                'circle-color': '#007cbf',
                'circle-opacity': 0.6
              }
            });

            // 延遲加載熱力圖層，確保地圖快速顯示後才渲染大量數據
            setTimeout(function() {
                map.addLayer({
                  'id': 'bike-heatmap',
                  'type': 'heatmap',
                  'source': 'route_data', 
                  'maxzoom': 18, 
                  'paint': {
                    'heatmap-weight': [
                      'interpolate',
                      ['linear'],
                      ['get', 'sum_of_txn_times'],
                      1, 0,    
                      maxSumOfTxnTimes, 1  
                    ],
                    'heatmap-intensity': [
                      'interpolate',
                      ['linear'],
                      ['zoom'],
                      0, 1,
                      18, 3
                    ],
                    'heatmap-color': [
                      'interpolate',
                      ['linear'],
                      ['heatmap-density'],
                      0, 'rgba(33,102,172,0)',
                      0.1, 'rgb(103,169,207)',
                      0.2, 'rgb(209,229,240)',
                      0.4, 'rgb(253,219,199)',
                      0.6, 'rgb(239,138,98)',
                      0.8, 'rgb(178,24,43)',
                      1, 'rgb(128,0,38)'
                    ],
                    'heatmap-radius': [
                      'interpolate',
                      ['linear'],
                      ['zoom'],
                      0, 2,
                      18, 20
                    ],
                    'heatmap-opacity': [
                      'interpolate',
                      ['linear'],
                      ['zoom'],
                      0, 1,
                      18, 0.6
                    ]
                  }
                });

                // 移除快速加載的點圖層
                map.removeLayer('initial-points');

                // 隱藏加載動畫
                hideLoadingSpinner();
            }, 2000); // 2 秒後加載熱力圖層
          })
          .catch(error => {
            console.error('Error fetching GeoJSON data:', error);
            hideLoadingSpinner(); // 發生錯誤也隱藏加載動畫
          });
    });

    return map;
}

// 創建兩個不同的地圖實例，並分別加載不同的 GeoJSON 數據
var beforeMap = createMap('before', 'mapbox://styles/mapbox/streets-v11', '/mapbox/routes/week');
var afterMap = createMap('after', 'mapbox://styles/mapbox/outdoors-v12', '/mapbox/routes/weekend');

// A selector or reference to HTML element
const container = '#comparison-container';

// Create map compare slider
const compareMap = new mapboxgl.Compare(beforeMap, afterMap, container, {
    // Set this to enable comparing two maps by mouse movement:
    // mousemove: true
});

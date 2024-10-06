// Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ';

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

    map.on('load', function () {
        fetch(fetchPath)
          .then(response => response.json())
          .then(data => {
            // 從 GeoJSON 中提取所有的 sum_of_txn_times
            const sumOfTxnTimesArray = data.features.map(feature => feature.properties.sum_of_txn_times);

            // 獲取最大值
            const maxSumOfTxnTimes = Math.max(...sumOfTxnTimesArray);

            console.log(containerId + " -> maxSumOfTxnTimes = " + maxSumOfTxnTimes);

            // 加載 GeoJSON 資料
            map.addSource('route_data', {
              'type': 'geojson',
              'data': data
            });
      
            // 添加熱力圖圖層
            map.addLayer({
              'id': 'bike-heatmap',
              'type': 'heatmap',
              'source': 'route_data', 
              'maxzoom': 18, 
              'paint': {
                // 設置熱力圖的權重，根據 sum_of_txn_times 的值動態調整
                'heatmap-weight': [
                  'interpolate',
                  ['linear'],
                  ['get', 'sum_of_txn_times'],
                  1, 0,    
                  maxSumOfTxnTimes, 1  
                ],
                // 設置熱力圖的強度，根據地圖縮放級別動態調整
                'heatmap-intensity': [
                  'interpolate',
                  ['linear'],
                  ['zoom'],
                  0, 1,  // 在縮放級別 0 時，強度為 1
                  18, 3  // 在縮放級別 18 時，強度為 3
                ],
                // 使用光譜式漸變來設置熱力圖的顏色梯度
                'heatmap-color': [
                  'interpolate',
                  ['linear'],
                  ['heatmap-density'],  // 根據熱力密度設定顏色
                  0, 'rgba(33,102,172,0)',   // 最低密度，透明
                  0.1, 'rgb(103,169,207)',   // 漸變的藍色
                  0.2, 'rgb(209,229,240)',   // 更淺的藍色
                  0.4, 'rgb(253,219,199)',   // 漸變到橙色
                  0.6, 'rgb(239,138,98)',    // 漸變到紅色
                  0.8, 'rgb(178,24,43)',     // 更深的紅色
                  1, 'rgb(128,0,38)'         // 最深的紅色
                ],
                // 設置每個點的半徑，根據地圖縮放級別動態調整
                'heatmap-radius': [
                  'interpolate',
                  ['linear'],
                  ['zoom'],
                  0, 2,   // 在縮放級別 0 時，半徑為 2
                  18, 20  // 在縮放級別 18 時，半徑為 20
                ],
                // 設置熱力圖的透明度
                'heatmap-opacity': [
                  'interpolate',
                  ['linear'],
                  ['zoom'],
                  0, 1,  // 在縮放級別 0 時，透明度為 1
                  18, 0.6  // 在縮放級別 18 時，透明度為 0.6
                ]
              }
            });
          })
          .catch(error => console.error('Error fetching GeoJSON data:', error));
    });
    return map;
}

// 創建兩個不同的地圖實例，並分別加載不同的 GeoJSON 數據
var beforeMap = createMap('before', 'mapbox://styles/mapbox/streets-v11', '/mapbox/week_route');
var afterMap = createMap('after', 'mapbox://styles/mapbox/outdoors-v12', '/mapbox/weekend_route');

// A selector or reference to HTML element
const container = '#comparison-container';

// Create map compare slider
const compareMap = new mapboxgl.Compare(beforeMap, afterMap, container, {
    // Set this to enable comparing two maps by mouse movement:
    // mousemove: true
});
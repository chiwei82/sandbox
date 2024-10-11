# YouBike 資料視覺化專案

此專案使用 FastAPI 構建，提供多個 API 端點來進行台北市 YouBike 自行車站點的即時數據視覺化和路徑分析。
整合了自行車站點數據、地理數據，使用於 Mapbox 或 Leaflet 等地圖視覺化套件中，並使用 d3.js 呈現圖表。

## 專案目的

- 找出使用者的使用習慣、站點的潛在分群、提供實時站點數據查詢
- 透過週間、週末的熱力圖、前 20 大站點路徑分析、付費路線分析，勾勒出使用者習慣
- 幫助潛在 TA 了解台北市市民使用 YouBike 的狀況

## 如何運行
#### 使用 Docker
- docker build -t image_fastapi .
- docker run -d -p host_port:container_port image_fastapi

#### 使用 local host
1. `創立虛擬環境` python -m venv env 
2. `啟動虛擬環境` env\Scripts\activate
3. `安裝套件` pip install -r requirements.txt
4. `移至目錄` cd project/map_application
5.  `啟動` uvicorn main:app --reload
6. `測試 & debug` 此專案預設執行路徑在 ${workspaceFolder}

## API 種類

- **即時站點數據**：提供台北市 YouBike 站點的即時自行車數據，包括可用車輛數量、目前是否有充足的腳踏車。
- **天氣資訊查詢**：根據指定城市名稱獲取當前天氣資訊。
- **讀取GeoJSON 數據**：回傳具有商業資訊的 GeoJson data
- **Data IO**：使用 API 進行ETL (e.g. 隨機抽樣、讀取duckdb 後將資料提供js繪製) 
- **靜態文件服務**：掛載前端視覺化 HTML 文件，用於渲染地圖（Mapbox, Leaflet, D3.js 等）。

## 前端網頁

### home.html
- 主頁: 用於包裝不同頁面的資訊

### mapbox.html
- 呈現週間、週末的熱力圖：考慮到載入速度，對原始資料進行 30% 抽樣。
- 計算車輛使用量：借出和還入次數均算作一次使用量。

### Leaflet.html
- 呈現週間、週末的路線次數在各行政區的排名。
- 透過與左側地圖互動，右側 D3 渲染的圖表會有相對應的視覺反應。
- 計算車輛使用量：某條路線的平均使用量，即 (借出 + 還入) / 2。

### index.html
- 呈現實時站點資訊。
- mapbox_3d 是相同的，以 3D 地圖呈現。

## API 端點

### 1. GET /bike-stations
- 抓取台北市政府公開資訊即時 YouBike 站點資料。
- **回應格式**：JSON，包含站點名稱、座標、可租借自行車數量、抓取時間等資訊。
- **範例請求**：`/bike-stations`

### 2. GET /weather/{city_name}
- 根據城市名稱，抓取該地區的當前天氣資訊。
- **參數**：`city_name` (字串) - 城市名稱，如台北市。
- **回應格式**：JSON，包含溫度和天氣描述。
- **範例請求**：`/weather/Taipei`

### 3. GET /country_moi
- 回傳台灣的 GeoJSON 資料，包含各縣市的地理邊界資訊。
- **回應格式**：GeoJSON，用於地理資訊可視化。
- **範例請求**：`/country_moi`

### 4. GET /geojson/{weekend_status}
- 根據 weekend_status 回傳 台北市的 GeoJSON 資料，
- **回應格式**：GeoJSON，包含各行政區的站點使用數據
- **參數**：`weekend_status` (str) - "week"、"weekend"
- **範例請求**：`/geojson/week`

### 5. GET /top_ten_routes/{weekend_status}
- 回傳站點使用量前 20 的路徑數據（週間）。
- **回應格式**：GeoJSON，包含前 20 名站點路徑及其相關資訊。
- **參數**：`weekend_status` (str) - "week"、"weekend"
- **範例請求**：`/top_ten_routes/week`

### 6. GET /mapbox/routes/{weekend_status}
- 回傳台北市週間路徑資料的 GeoJSON，用於可視化。
- **回應格式**：GeoJSON。
- **參數**：`weekend_status` (str) - "week"、"weekend"
- **範例請求**：`/mapbox/routes/week`

### 7. GET /mapbox/refresh_route_sample/{frac}
- 根據指定比例隨機抽樣站點路徑數據，並生成新的 GeoJSON 檔案。
- **參數**：`frac` (float) - 抽樣比例（預設為 0.3）。
- **回應格式**：文字訊息，表示抽樣狀態是否成功。
- **範例請求**：`/mapbox/refresh_route_sample/0.5`

### 8. GET /refresh/constant_html/{token}
- 刷新以 Python 撰寫的 ETL 形式產生的 HTML 檔案。
- **回應格式**：文字訊息，表示 ETL 是否成功。
- **參數**：`token` (字串) - 管理員密碼。只有當 token === 'admin' 時才進行刷新。
- **範例請求**：`/refresh/constant_html/admin`

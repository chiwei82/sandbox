import requests
from fastapi import FastAPI
import pandas as pd
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime, timedelta
from shapely.geometry import LineString
import geopandas as gpd
import json
import logging
import aiofiles
import os
import sys
from pathlib import Path

# Logging 設置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設置路徑和全域緩存
abspath = os.path.abspath(__file__)
dname = os.path.dirname(os.path.dirname(os.path.dirname(abspath)))
sys.path.append(os.path.dirname(abspath))
sys.path.append(dname)
from bike_data import get_weather as bike_weather
from constant_plot import generate_distribution_plot, generate_exist_rate, generate_fee_plot

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# 全域緩存字典
cache = {}

# 通用緩存檔案讀取函數
async def load_file_with_cache(file_path: str, cache_key: str, expiry_minutes: int = 10):
    """
    通用的緩存檔案讀取功能。檢查緩存是否存在且未過期，否則重新讀取檔案。
    """
    now = datetime.now()
    if cache_key in cache:
        cached_data, expiry_time = cache[cache_key]
        if expiry_time > now:
            logger.info(f"Returning cached data for {cache_key}")
            return cached_data  # 使用緩存

    # 使用 aiofiles 進行異步檔案讀取
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        data = await file.read()
        data = json.loads(data)

    cache[cache_key] = (data, now + timedelta(minutes=expiry_minutes))
    logger.info(f"Loaded data from file for {cache_key}")
    return data

# 抓取台北市公共自行車即時資訊
@app.get("/bike-stations")
def get_bike_stations():
    """
    抓取台北市公共自行車即時資訊
    """
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    response = requests.get(url)
    data = response.json()

    for station in data:
        station['sna'] = station['sna'].replace("YouBike2.0_", "")

    df = pd.DataFrame(data)
    df = df.sort_values("infoTime").query(f"infoTime >= '{datetime.now()-timedelta(days=1)}'")
    return data

# 獲取現在時間
@app.get("/time")
def get_time():
    """
    獲取現在時間
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 抓取地點天氣
@app.get("/weather/{city_name}")
def get_weather(city_name: str):
    """
    抓取地點天氣: 參數 -> 城市名稱
    """
    return bike_weather(city_name, json=True)

# 回傳 "台灣" 的 GeoJSON
@app.get("/country_moi")
async def get_country_moi():
    """
    回傳 "台灣" 的 GeoJSON
    """
    file_path = r"static/geojson/COUNTY_MOI_1130718.json"
    return await load_file_with_cache(file_path, "country_moi")

# 回傳 "台北" 的 GeoJSON (週間 或 週末)
@app.get("/geojson/{weekend_status}")
async def get_geojson(weekend_status: str):
    """
    回傳 "台北" 的 GeoJSON。裡面包含各行政區的 站點使用量 (週間 或 週末)
    """
    if weekend_status == "week":
        file_path = "static/geojson/OSM_DATA.geojson"
        cache_key = "geojson_week"
    elif weekend_status == "weekend":
        file_path = "static/geojson/OSM_DATA_weekend.geojson"
        cache_key = "geojson_weekend"
    else:
        return {"error": "Invalid weekend status"}

    return await load_file_with_cache(file_path, cache_key)

# 回傳 站點使用量 (週間 或 週末) 前 20 名站點
@app.get("/top_ten_routes/{weekend_status}")
async def get_top_ten_routes(weekend_status: str):
    """
    回傳站點使用量 (週間 或 週末) 前 20 名站點
    """
    if weekend_status == "week":
        file_path = r"static/data/週間起訖站點統計_cleaned.csv"
        cache_key = "top_ten_week"
    elif weekend_status == "weekend":
        file_path = r"static/data/週末起訖站點統計_cleaned.csv"
        cache_key = "top_ten_weekend"
    else:
        return {"error": "Invalid weekend status"}

    async def json_etl(file_path):
        top = pd.read_csv(file_path)\
            .sort_values(by="mean_of_txn_times_byRoutes", ascending=False)\
            .head(20)[["mean_of_txn_times_byRoutes", "on_stop", "off_stop", 
                       'lat_start', 'lng_start', 'lat_end', 'lng_end', "district_name"]]

        def create_linestring(row):
            return LineString([(row['lng_start'], row['lat_start']), (row['lng_end'], row['lat_end'])])

        top['geometry'] = top.apply(create_linestring, axis=1)
        top['mean_of_txn_times_byRoutes'] = top['mean_of_txn_times_byRoutes'].round(0)
        gdf = gpd.GeoDataFrame(top, geometry='geometry')

        output_path = fr"static/geojson/top_ten_{weekend_status}.geojson"
        gdf.to_file(output_path, driver="GeoJSON")

        return await load_file_with_cache(output_path, f"top_ten_{weekend_status}")

    return await json_etl(file_path)

# 讀取 SAMPLED WEEK ROUTE 並回傳 GeoJSON
@app.get("/mapbox/routes/{weekend_status}")
async def get_routes(weekend_status: str):
    """
    讀取 SAMPLED WEEK ROUTE 並回傳 GeoJSON
    """
    if weekend_status == "week":
        file_path = r"static/geojson/week_route.geojson"
        cache_key = "week_route"
    elif weekend_status == "weekend":
        file_path = r"static/geojson/weekend_route.geojson"
        cache_key = "weekend_route"
    else:
        return {"error": "Invalid weekend status"}

    return await load_file_with_cache(file_path, cache_key)

# 將週間、週末起訖站點統計進行隨機抽樣並將結果存成新的 GeoJSON 檔案
@app.get("/mapbox/refresh_weekend_route_sample/{frac}")
def get_refresh_weekend_route(frac: float = 0.3):
    """
    將週間、週末起訖站點統計進行隨機抽樣並將結果存成新的 GeoJSON 檔案
    """
    try:
        WEEK_LOC = r'static/data/週間起訖站點統計_202307.geojson'
        WEEK_OUTPUT = r"static/geojson/week_route.geojson"

        WEEKEND_LOC = r'static/data/週末起訖站點統計_202307.geojson'
        WEEKEND_OUTPUT = r"static/geojson/weekend_route.geojson"

        def movement(FILE_LOC, WEEKEND_OUTPUT, frac=0.3):
            gdf = gpd.read_file(FILE_LOC)

            slice = pd.DataFrame()
            for district in gdf.district_origin.unique():
                df_filtered = gdf.query(f"district_origin == '{district}'")
                slice = pd.concat([slice, df_filtered.sample(frac=frac, random_state=1)])
            slice = slice.sort_values("sum_of_txn_times", ascending=False)

            gpd.GeoDataFrame(slice[["sum_of_txn_times", "width", "geometry"]], geometry='geometry')\
                .to_file(WEEKEND_OUTPUT, driver="GeoJSON")

        movement(WEEK_LOC, WEEK_OUTPUT, frac)
        movement(WEEKEND_LOC, WEEKEND_OUTPUT, frac)

        # 清除舊的緩存，讓下次請求時重新讀取新資料
        cache.pop("week_route", None)
        cache.pop("weekend_route", None)

        return f"{frac} random sampled has been refreshed. status: 200 ok"
    except Exception as e:
        return str(e)

# 刷新 HTML
@app.get("/refresh/constant_html/{token}")
def get_constant_html(token: str):
    if token == "admin":
        try:
            logger.info("Admin access granted, refreshing constant HTML data.")
            # 生成統計圖表
            generate_fee_plot()
            logger.info("Constant HTML has been refreshed successfully.")
            return {"message": "HTML has been refreshed. status: 200 OK"}
        except Exception as e:
            logger.error(f"Error while refreshing HTML: {str(e)}")
            return {"error": str(e)}
    else:
        logger.warning("Unauthorized access attempt to refresh constant HTML.")
        return {"error": "Unauthorized"}

# 付費資料
@app.get("/h10_rent")
async def get_top10_rent():
    file_path = r"static/data/h10付費_租出.json"
    return await load_file_with_cache(file_path, "h10_rent")

# 還入資料
@app.get("/h10_returned")
async def get_top10_returned():
    file_path = r"static/data/h10付費_還入.json"
    return await load_file_with_cache(file_path, "h10_returned")

# 路由設定
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/{file_name}", response_class=HTMLResponse)
async def serve_html(file_name: str):
    """Serve static HTML files dynamically based on the requested file name."""
    file_path = BASE_DIR / f"static/{file_name}.html"
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as file:
            return file.read()
    return HTMLResponse(status_code=404, content="File not found.")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve home.html when accessing the root path."""
    home_path = BASE_DIR / "static/home.html"
    if home_path.exists():
        with home_path.open("r", encoding="utf-8") as file:
            return file.read()
    return HTMLResponse(status_code=404, content="Home page not found.")
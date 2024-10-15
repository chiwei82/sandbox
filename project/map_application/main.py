import requests
from fastapi import FastAPI
import pandas as pd
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from shapely.geometry import LineString
import geopandas as gpd
import json

import os
import sys
abspath = os.path.abspath(__file__)
dname = os.path.dirname(os.path.dirname(os.path.dirname(abspath)))
sys.path.append(os.path.dirname(abspath))
sys.path.append(dname)
from bike_data import get_weather as bike_weather
from constant_plot import generate_distribution_plot,generate_exist_rate,generate_fee_plot

app = FastAPI()

# index.html
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

@app.get("/time")
def get_time():
    """
    獲取現在時間
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# leaflet.html
@app.get("/weather/{city_name}")
def get_weather(city_name: str):
    """
    抓取地點天氣: 參數 -> 城市名稱
    """
    return bike_weather(city_name, json=True)

@app.get("/country_moi")
def get_country_moi():
    """
    回傳 "台灣" 的 GeoJSON
    """
    with open(r"static/geojson/COUNTY_MOI_1130718.json", "r", encoding="utf-8") as geojson_file:
        geojson_data = json.load(geojson_file)

    return geojson_data

@app.get("/geojson/{weekend_status}")
def load_geojson(weekend_status: str):
    """
    回傳 "台北" 的 GeoJSON。裡面包含各行政區的 站點使用量 (週間) 以便繪圖使用
    """
    def load_json(file_path):
        with open(f"{file_path}", "r", encoding="utf-8") as geojson_file:
            geojson_data = json.load(geojson_file)
        return geojson_data

    if weekend_status == "week":
        geojson_data = load_json("static/geojson/OSM_DATA.geojson")    
    
    elif weekend_status == "weekend":
        geojson_data = load_json("static/geojson/OSM_DATA_weekend.geojson")    

    return geojson_data

@app.get("/top_ten_routes/{weekend_status}") 
def return_top_tY(weekend_status: str):
    """
    回傳 站點使用量 (週間) 前 20 站點
    """
    if weekend_status == "week":
        file_path = r"static/data/週間起訖站點統計_cleaned.csv"
    elif weekend_status == "weekend":
        file_path = r"static/data/週末起訖站點統計_cleaned.csv"

    def json_etl(file_path):
        top = pd.read_csv(file_path)\
            .sort_values(by="mean_of_txn_times_byRoutes", ascending=False)\
            .head(20)[["mean_of_txn_times_byRoutes", "on_stop", "off_stop", 
                    'lat_start', 'lng_start', 'lat_end', 'lng_end', "district_name"]]
        
        def create_linestring(row):
            return LineString([(row['lng_start'], row['lat_start']), (row['lng_end'], row['lat_end'])])

        top['geometry'] = top.apply(create_linestring, axis=1)
        top['mean_of_txn_times_byRoutes'] = top['mean_of_txn_times_byRoutes'].round(0)
        gdf = gpd.GeoDataFrame(top, geometry='geometry')
        
        gpd.GeoDataFrame(gdf, geometry='geometry')\
            .to_file(fr"static/geojson/top_ten_{weekend_status}.geojson", driver="GeoJSON")
        
        with open(fr"static/geojson/top_ten_{weekend_status}.geojson", "r", encoding="utf-8") as geojson_file:
            to_return = json.load(geojson_file)
        
        return to_return
    
    to_return = json_etl(file_path)

    return to_return

@app.get("/mapbox/routes/{weekend_status}")
def return_week_route(weekend_status):
    """
    讀取 SAMPLED WEEK ROUTE 並回傳 GeoJSON
    """ 
    if weekend_status == "week":
        with open(r"static/geojson/week_route.geojson", "r", encoding="utf-8") as geojson_file:
            to_return = json.load(geojson_file)

    elif weekend_status == "weekend":
        with open(r"static/geojson/weekend_route.geojson", "r", encoding="utf-8") as geojson_file:
            to_return = json.load(geojson_file)

    return to_return

@app.get("/mapbox/refresh_weekend_route_sample/{frac}")
def refresh_weekend_route_sample(frac: float = 0.3):
    """
    將週間、週末起訖站點統計進行隨機抽樣並將 GeoJSON 存成新檔案
    """
    try:
        # 周末
        WEEK_LOC = r'static/data/週間起訖站點統計_202307.geojson'
        WEEK_OUTPUT = r"static/geojson/week_route.geojson"

        WEEKEND_LOC = r'static/data/週末起訖站點統計_202307.geojson'
        WEEKEND_OUTPUT = r"static/geojson/weekend_route.geojson"

        def movement(FILE_LOC,WEEKEND_OUTPUT, frac = 0.3):

            gdf = gpd.read_file(FILE_LOC)

            slice = pd.DataFrame()
            for district in gdf.district_origin.unique():
                df_filtered = gdf.query(f"district_origin == '{district}'")
                slice = pd.concat([slice,df_filtered.sample(frac=frac, random_state=1)])
            slice = slice.sort_values("sum_of_txn_times",ascending=False)
        
            gpd.GeoDataFrame(slice[["sum_of_txn_times","width","geometry"]], geometry='geometry')\
                .to_file(WEEKEND_OUTPUT, driver="GeoJSON")

        movement(WEEK_LOC, WEEK_OUTPUT, frac)    
        movement(WEEKEND_LOC, WEEKEND_OUTPUT, frac)

        return f"{frac} random sampled has been refreshed. status: 200 ok"
    except Exception as e:
        return str(e)

@app.get("/refresh/constant_html/{token}")
def refresh_html(token: str):
    if token == "admin":
        try:
            # generate_distribution_plot()
            # generate_exist_rate()
            generate_fee_plot()
            return f"html has been refreshed. status: 200 ok"
        except Exception as e:
            return str(e)
    else:
        pass

@app.get("/h10_租")
def get_top10():
    with open(r"static/data/h10付費_租出.json", "r", encoding="utf-8") as json_file:
        to_return = json.load(json_file)

    return to_return

@app.get("/h10_還")
def get_top10():
    with open(r"static/data/h10付費_還入.json", "r", encoding="utf-8") as json_file:
        to_return = json.load(json_file)

    return to_return

# 路由設定
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_html():
    with open("static/home.html", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/fullpage", response_class=HTMLResponse)
async def read_html():
    with open("static/fullpage.html", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/index", response_class=HTMLResponse)
async def read_html():
    with open("static/index.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/mapbox", response_class=HTMLResponse)
async def read_html():
    with open("static/mapbox.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/leaflet", response_class=HTMLResponse)
async def read_html():
    with open("static/leaflet.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/mapbox_3d", response_class=HTMLResponse)
async def read_html():
    with open("static/mapbox_3d.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/d3", response_class=HTMLResponse)
async def read_html():
    with open("static/d3_.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/bike_routes_map", response_class=HTMLResponse)
async def read_html():
    with open("static/bike_routes_map.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/見車率", response_class=HTMLResponse)
async def read_html():
    with open("static/見車率.html", "r", encoding="utf-8") as file:
        return file.read()
    
    
@app.get("/見車率_0930", response_class=HTMLResponse)
async def read_html():
    with open("static/見車率_0930.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/distribute", response_class=HTMLResponse)
async def read_html():
    with open("static/distribute.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/test", response_class=HTMLResponse)
async def read_html():
    with open("static/test.html", "r", encoding="utf-8") as file:
        return file.read()
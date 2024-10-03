import requests
from fastapi import FastAPI
import pandas as pd
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from shapely.geometry import LineString
import random
import geopandas as gpd
from bike_data import get_weather as bike_weather
import json

app = FastAPI()

# index.html
@app.get("/bike-stations")
def get_bike_stations():
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
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# leaflet.html
@app.get("/weather/{city_name}")
def get_weather(city_name: str):
    return bike_weather(city_name, json=True)

@app.get("/geojson")
def load_geojson():
    
    with open("static\geojson\OSM_DATA.geojson", "r", encoding="utf-8") as geojson_file:
        geojson_data = json.load(geojson_file)

    return geojson_data

@app.get("/geojson_weekend")
def load_geojson_weekend():
    
    with open("static\geojson\OSM_DATA_weekend.geojson", "r", encoding="utf-8") as geojson_file:
        geojson_data = json.load(geojson_file)

    return geojson_data

@app.get("/top_ten_routes")
def return_top_ten():
    
    top = pd.read_csv(r"D:\sandbox_git\warehouse\insight\週間起訖站點統計_cleaned.csv")\
        .sort_values(by="mean_of_txn_times_byRoutes", ascending=False)\
        .head(20)[["mean_of_txn_times_byRoutes", "on_stop", "off_stop", 
                   'lat_start', 'lng_start', 'lat_end', 'lng_end', "district_name"]]
    
    def create_linestring(row):
        return LineString([(row['lng_start'], row['lat_start']), (row['lng_end'], row['lat_end'])])

    top['geometry'] = top.apply(create_linestring, axis=1)
    top['mean_of_txn_times_byRoutes'] = top['mean_of_txn_times_byRoutes'].round(0)
    gdf = gpd.GeoDataFrame(top, geometry='geometry')
    
    gpd.GeoDataFrame(gdf, geometry='geometry')\
        .to_file(r"static\geojson\top_ten.geojson", driver="GeoJSON")
    
    with open(r"static\geojson\top_ten.geojson", "r", encoding="utf-8") as geojson_file:
        to_return = json.load(geojson_file)

    return to_return

@app.get("/top_ten_routes_weekend")
def return_top_ten():
    
    top = pd.read_csv(r"D:\sandbox_git\warehouse\insight\週末起訖站點統計_cleaned.csv")\
        .sort_values(by="mean_of_txn_times_byRoutes", ascending=False)\
        .head(20)[["mean_of_txn_times_byRoutes", "on_stop", "off_stop", 
                   'lat_start', 'lng_start', 'lat_end', 'lng_end', "district_name"]]
    
    def create_linestring(row):
        return LineString([(row['lng_start'], row['lat_start']), (row['lng_end'], row['lat_end'])])

    top['geometry'] = top.apply(create_linestring, axis=1)
    top['mean_of_txn_times_byRoutes'] = top['mean_of_txn_times_byRoutes'].round(0)
    gdf = gpd.GeoDataFrame(top, geometry='geometry')
    
    gpd.GeoDataFrame(gdf, geometry='geometry')\
        .to_file(r"static\geojson\top_ten_weekend.geojson", driver="GeoJSON")
    
    with open(r"static\geojson\top_ten_weekend.geojson", "r", encoding="utf-8") as geojson_file:
        to_return = json.load(geojson_file)

    return to_return

@app.get("/mapbox/week_route")
def return_week_route():
    
    with open(r"static\geojson\week_route.geojson", "r", encoding="utf-8") as geojson_file:
        to_return = json.load(geojson_file)

    return to_return

@app.get("/mapbox/weekend_route")
def return_week_route():
    
    with open(r"static\geojson\weekend_route.geojson", "r", encoding="utf-8") as geojson_file:
        to_return = json.load(geojson_file)

    return to_return

@app.get("/mapbox/refresh_weekend_route_sample/{frac}")
def refresh_weekend_route_sample(frac: float = 0.3):
    try:
        # 周末
        WEEK_LOC = r'D:\sandbox_git\warehouse\週間起訖站點統計_202307.geojson'
        WEEK_OUTPUT = r"D:\sandbox_git\project\map_application\static\geojson\week_route.geojson"

        WEEKEND_LOC = r'D:\sandbox_git\warehouse\週末起訖站點統計_202307.geojson'
        WEEKEND_OUTPUT = r"D:\sandbox_git\project\map_application\static\geojson\weekend_route.geojson"

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
    
# 路由設定
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/home.html", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/index", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/mapbox", response_class=HTMLResponse)
async def read_mapbox():
    with open("static/mapbox.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/leaflet", response_class=HTMLResponse)
async def read_mapbox():
    with open("static/leaflet.html", "r", encoding="utf-8") as file:
        return file.read()
import requests
from fastapi import FastAPI
import pandas as pd
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta

app = FastAPI()

# 從新的 API URL 獲取自行車站即時資料
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

app.mount("/", StaticFiles(directory="static", html=True), name="static")


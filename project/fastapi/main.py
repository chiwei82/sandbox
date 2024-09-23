import requests
from fastapi import FastAPI
import pandas as pd
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
import os
# 使用 os.path.join 構建 static 目錄的路徑
current_dir = os.path.dirname(os.path.abspath(__file__))  # 當前文件的目錄
static_dir = os.path.join(current_dir, "static")  # 靜態文件的路徑

# 掛載靜態文件目錄
app = FastAPI()
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except:
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    except:
        @app.get("/")
        async def read_index():
            return FileResponse(os.path.join(static_dir, "index.html"))

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
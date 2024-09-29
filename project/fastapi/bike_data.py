from dagster import job, schedule
import pandas as pd
import requests
import duckdb
from datetime import datetime,timedelta
import dask
import sys
sys.path.append("D:\sandbox_git")
from function.log import Logger
logger = Logger().get_logger()

def get_weather(city_name):
    
    base_url = "https://api.openweathermap.org/data/2.5/weather?q={city_name},tw&APPID=cddf115f5a5d9213ab3674132a2581a6"
    response = requests.get(base_url.format(city_name=city_name.replace(" Dist","")))

    if response.status_code == 404:
        response = requests.get(base_url.format(city_name='taipei'))
        print(f'{city_name} whether not found. Use default city: taipei.')
    
    if response.status_code == 200:
        data = response.json()
        main = data['main']
        weather = data['weather'][0]

        # openweather api 預設 return temperature in kelvin
        temperature_k = main['temp']
        temperature_k_feels_like = main['feels_like']
        temperature_c_str = f"{temperature_k - 273.15:.2f}"
        temperature_k_feels_like_str = f"{temperature_k_feels_like - 273.15:.2f}"

        return pd.DataFrame({
            'city': [city_name],
            'temperature': [temperature_c_str],  
            'feels_like': [temperature_k_feels_like_str],  
            'humidity': [main['humidity']],  
            'description': [weather['description']]  
        })

    else:
        return pd.DataFrame({
            'city': [city_name],
            'temperature': ["unknown"],
             'feels_like': ["unknown"],  
            'humidity': ["unknown"],
            'description': ["unknown"]
        })
            
def get_bike_data():

    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    response = requests.get(url)
    data = response.json()

    for station in data:
        station['sna'] = station['sna'].replace("YouBike2.0_", "")

    df = pd.DataFrame(data)
    df = df.sort_values("infoTime").query(f"infoTime >= '{datetime.now()-timedelta(days=1)}'") # 只保留一天內有更新的資料
    df["fetch_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return df

def main():

    # get_bike_data()
    df_bike = get_bike_data()

    # get_weather()
    unique_sareaen = list(df_bike['sareaen'].unique())
    delayed = [dask.delayed(get_weather)(city_name) for city_name in unique_sareaen]  
    df_weather = pd.concat(dask.compute(*delayed)) 

    # merge
    df_bike = df_bike.merge(df_weather, left_on="sareaen", right_on="city",how="left")

    try:
        conn = duckdb.connect(database='warehouse\data_sandbox.duckdb')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS youbike (
                sno TEXT, 
                sna TEXT, 
                sarea TEXT, 
                mday TEXT, 
                ar TEXT, 
                sareaen TEXT, 
                snaen TEXT, 
                aren TEXT, 
                act TEXT, 
                srcUpdateTime TEXT, 
                updateTime TEXT, 
                infoTime TEXT, 
                infoDate TEXT, 
                total INTEGER, 
                available_rent_bikes INTEGER, 
                latitude REAL, 
                longitude REAL, 
                available_return_bikes INTEGER, 
                fetch_time TEXT,
                city TEXT,
                temperature FLOAT,
                feels_like FLOAT,
                humidity INTEGER,
                description TEXT                  
        );
        """)
        conn.execute("INSERT INTO youbike SELECT * FROM df_bike")
        logger.info("Save Success")
        conn.close()

    except Exception as e:
        logger.error(e)

if __name__ == "__main__":
    main()
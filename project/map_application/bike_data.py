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

def get_weather(city_name,json=False):
    
    base_url = "https://api.openweathermap.org/data/2.5/weather?q={city_name}&APPID=cddf115f5a5d9213ab3674132a2581a6"
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

        to_return = pd.DataFrame({
            'city': [city_name],
            'temperature': [temperature_c_str],  
            'feels_like': [temperature_k_feels_like_str],  
            'humidity': [main['humidity']],  
            'description': [weather['description']]  
        })

    else:
        to_return = pd.DataFrame({
            'city': [city_name],
            'temperature': ["unknown"],
             'feels_like': ["unknown"],  
            'humidity': ["unknown"],
            'description': ["unknown"]
        })

    if json:
        return to_return.to_json(orient='records')
    else:
        return to_return
            
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

def save_raw_data(df_bike):
    
    df_bike = df_bike.copy()
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

def data_market():

    try:
        conn = duckdb.connect(database='D:/sandbox_git/warehouse/data_sandbox.duckdb')
        df = conn.execute(
            "SELECT * FROM youbike"
        ).fetch_df()[['sno', 'sna', 'sarea', 'fetch_time','infoTime', 'latitude', 'longitude', 'available_rent_bikes', 'total', 'temperature', 'description']].sort_values(['sno', 'fetch_time'], ascending=True)
        
        conn.close()
        
        df["fetch_time"] = pd.to_datetime(df["fetch_time"])
        df["infoTime"] = pd.to_datetime(df["infoTime"])
        df["src_validate"] = (df["fetch_time"] - df["infoTime"]).dt.total_seconds() / 60

        # 超過20分鐘沒有更新的站點全部刪掉
        df = df.query("src_validate < 21").drop(columns=["src_validate","infoTime"])

        def calculate_change_rate(group):
            group['change_rate'] = group['available_rent_bikes'].pct_change().fillna(0)
            group['time_diff'] = group['fetch_time'].diff().dt.total_seconds() / 60
            group.loc[group['time_diff'] > 12, 'change_rate'] = 0
            return group

        df_pct = df.groupby('sno', as_index=False).apply(calculate_change_rate)
        df_available = df_pct.query("~time_diff.isna()").query("time_diff < 12").query("change_rate != inf")
        conn = duckdb.connect(database='warehouse\data_sandbox.duckdb')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS youbike_available (
                sno VARCHAR,
                sna VARCHAR,
                sarea VARCHAR,
                fetch_time TIMESTAMP,
                latitude FLOAT,
                longitude FLOAT,
                available_rent_bikes INTEGER,
                total INTEGER,
                temperature FLOAT,
                description VARCHAR,
                change_rate DOUBLE,
                time_diff DOUBLE
            );
        """)
        conn.execute("""
            DELETE FROM youbike_available WHERE sno IN (SELECT sno FROM df_available);
        """)
        conn.execute("INSERT INTO youbike_available SELECT * FROM df_available")
        logger.info("Market data Success")
        conn.close()
    except Exception as e:
        logger.error(e)

def main():

    # get_bike_data()
    df_bike = get_bike_data()

    # get_weather()
    unique_sareaen = list(df_bike['sareaen'].unique())
    delayed = [dask.delayed(get_weather)(city_name) for city_name in unique_sareaen]  
    df_weather = pd.concat(dask.compute(*delayed)) 

    # merge
    df_bike = df_bike.merge(df_weather, left_on="sareaen", right_on="city",how="left")

    save_raw_data(df_bike)
    data_market()

if __name__ == "__main__":
    main()
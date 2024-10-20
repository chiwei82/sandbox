import os
import sys
import folium
import duckdb
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors

abspath = os.path.abspath(__file__)
dname = os.path.dirname(os.path.dirname(os.path.dirname(abspath)))
sys.path.append(dname)

plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta'] 
plt.rcParams['axes.unicode_minus'] = False 

try:
    db_loc = dname+'/warehouse/data_sandbox.duckdb'
    conn = duckdb.connect(database = db_loc)
    sna_loc = conn.execute("SELECT distinct sna, latitude as lat,longitude as lng FROM youbike").fetch_df()
    conn.close()
except: # for docker
    conn = duckdb.connect('/workspace/warehouse/data_sandbox.duckdb')
    sna_loc = conn.execute("SELECT distinct sna, latitude as lat,longitude as lng FROM youbike").fetch_df()
    conn.close()

def get_lat_lon(df,from_stop,to_stop):
    return df.merge(sna_loc, left_on=f"{from_stop}", right_on="sna")\
    .rename(columns={"lat":"lat_start","lng":"lng_start"})\
    .drop(columns="sna")\
    .merge(sna_loc, left_on=f"{to_stop}", right_on="sna")\
    .rename(columns={"lat":"lat_end","lng":"lng_end"})\
    .drop(columns="sna")

def generate_distribution_plot():
    
    conn = duckdb.connect(database=db_loc)
    df = conn.execute("SELECT distinct sna,latitude,longitude,total FROM youbike ORDER BY total").fetch_df()
    conn.close()

    m = folium.Map(location=[25.08,121.53], zoom_start=12,
                tiles='https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ',
                    attr='Mapbox')

    def get_color(number):
        number = int(number)
        if number  < 15:
            return "black"
        elif number >80:
            return "red"
        elif number > 31:
            return "orange"
        else:
            return "gray"
        
    def get_opa(color):
        if color in ["black","gray"]:
            return 0.4
        else:
            return 0.8

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=max(row["total"]/10,3),  
            tooltip=folium.Tooltip(f"<div style='font-size: 18px;'>站點: {row['sna']}, 有{row['total']}個車位</div>"),  
            color= get_color(row["total"]),  
            fill=True,
            fill_color= get_color(row["total"]), 
            fill_opacity= get_opa(get_color(row["total"])) 
        ).add_to(m)

    legend_html = """
        <div style="
        position: fixed;
        top: 20px; left: 50%; transform: translateX(-50%);
        width: auto; height: auto;
        background-color: rgba(255, 255, 255, 0.8);
        border: 2px solid grey; z-index: 9999; font-size: 16px; line-height: 1.6;
        border-radius: 15px; padding: 10px;
        text-align: center;
        ">
        <strong style="font-size: 18px;">Legend</strong> <br>
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: flex-start; margin-top: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:black; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                <span style="font-size: 14px; margin-left: 10px;"> 低於15輛(<25%) </span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:gray; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                <span style="font-size: 14px; margin-left: 10px;"> 中 </span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:orange; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                <span style="font-size: 14px; margin-left: 10px;"> 高(>75%) </span>
            </div>
            <div style="display: flex; align-items: center;">
                <i style="background:red; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                <span style="font-size: 14px; margin-left: 10px;"> 前10名(>80輛) </span>
            </div>
        </div>
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

    output =  dname+"/project/map_application/static/distribute.html"
    m.save(fr'{output}')

def generate_exist_rate():

    conn = duckdb.connect(database=db_loc)
    df = conn.execute("SELECT * FROM youbike where infoDate = '2024-09-30' ").fetch_df()[["sna","available_return_bikes","infoTime","latitude","longitude","infoDate","total"]]
    conn.close()

    zt = df.query("available_return_bikes ==0").groupby(["sna"],as_index=False).agg(zt = ("sna","count"))
    
    df = df.query("available_return_bikes !=0")\
            .groupby(["sna","latitude","longitude"],as_index=False)\
            .agg(nzt = ("sna","count"))\
            .merge(zt,how="left",on="sna").fillna(0)
    df["zsr"] = 1- df["zt"] / (df["nzt"]+ df["zt"])

    def rate(row):
        if row <0.6:
            return "低"
        elif row >= 0.9:
            return "高"
        else:
            return "中"
    df["見車率"] = df["zsr"].apply(rate)

    def plot(df,save_name):
        
        ordered_df = pd.DataFrame()
        for rate in ["高","中","低"]:
            filtered = df.query(f"見車率 == '{rate}'")
            ordered_df = pd.concat([ordered_df,filtered])

        df = ordered_df.copy()

        m = folium.Map(location=[25.04,121.56], zoom_start=12,
                    tiles='https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ',
                        attr='Mapbox')

        color_map = {
            "低":"red",
            "中":"orange",
            "高":"green"
        }

        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=4,  
                tooltip=folium.Tooltip(f"<div style='font-size: 18px;'>站點: {row['sna']}</div>"),  
                color=color_map[row['見車率']],  
                fill=True,
                fill_color=color_map[row['見車率']], 
                fill_opacity=0.8  
            ).add_to(m)

        if save_name == "available_bikes_0930":
            p_content = "2024/09/30"
        else:
            p_content = ""
        
        legend_html = f"""
            <div style="
            position: fixed;
            top: 20px; left: 50%; transform: translateX(-50%);
            width: 200px; height: auto;
            background-color: rgba(255, 255, 255, 0.8);
            border:2px solid grey; z-index:9999; font-size:20px; line-height: 1.6;
            border-radius: 15px; padding: 10px;
            text-align: center;
            ">
            <strong>見車率分類</strong> <br>
            <p>{p_content}</p>
            <div style="display: flex; justify-content: space-around; align-items: center; margin-top: 10px;">
                <div>
                    <i style="background:red; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                    <span style="font-size: 20px;">低</span>
                </div>
                <div>
                    <i style="background:orange; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                    <span style="font-size: 20px;">中</span>
                </div>
                <div>
                    <i style="background:green; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                    <span style="font-size: 20px;">高</span>
                </div>
            </div>
            </div>
        """

        m.get_root().html.add_child(folium.Element(legend_html))
        m.save(dname +f"/project/map_application/static/{save_name}.html")

    plot(gpd.read_file(dname+"/warehouse/見車率_202307.geojson").rename(columns={"stop_name":"sna","category":"見車率"}),"見車率")
    plot(df,"見車率_0930")

def generate_fee_plot():

    df = pd.read_csv(dname+r"/project/map_application/static/data/202312_轉乘YouBike2.0票證刷卡資料.csv")

    routes_pattern = df.groupby(["借車站", "還車站",'lat_start', 'lng_start', 'lat_end', 'lng_end','distance_km'], as_index=False)\
    .agg(路線次數 = ("index", "nunique"),
         平均分數 = ("租借分數","mean"),
         付費紀錄 = ("付費","sum"))\
        .sort_values("路線次數",ascending=False)
    routes_pattern["付費比率"] = routes_pattern["付費紀錄"] / routes_pattern["路線次數"]

    filtered = pd.DataFrame()
    for sna in routes_pattern["借車站"].unique():
        station = routes_pattern.query(f"借車站 == '{sna}'")
        station = station.sort_values(by = ["路線次數","付費比率"],ascending=False).head(10)
        filtered = pd.concat([filtered,station])

    mymap = folium.Map(location=[25.065,121.56], zoom_start=12,
                tiles='https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ',
                attr='Mapbox')

    def get_color_from_ratio(ratio):

        # 從灰色到橘色
        colors = ['#808080', '#FFA500']
        cmap = LinearSegmentedColormap.from_list("custom_cmap", colors)
        rgba_color = cmap(ratio)
        hex_color = mcolors.to_hex(rgba_color)
        
        return hex_color

    def get_op(route):
        if route > 15:
            return 1
        elif route > 5:
            return 0.6
        else:
            return 0.1

    # 繪製無付費紀錄的路線
    for row in filtered.query("付費比率 ==0").to_dict(orient = "records"):
        folium.PolyLine(
            locations=[(row['lat_start'], row['lng_start']), (row['lat_end'], row['lng_end'])],
            color=get_color_from_ratio(row["付費比率"]),  
            weight = min(0.8 * (row["路線次數"] ** 0.5 / filtered["路線次數"].mean() ** 0.5), 2),
            opacity = get_op(row["路線次數"])       
        ).add_to(mymap)

    # 繪製至少有一筆付費紀錄的路線
    for row in filtered.query("付費比率 !=0 ")\
                    .sort_values("付費比率")\
                    .reset_index()\
                    .drop(columns="index")\
                    .to_dict(orient = "records"):
        folium.PolyLine(
            locations=[(row['lat_start'], row['lng_start']), (row['lat_end'], row['lng_end'])],
            color=get_color_from_ratio(row["付費比率"]),  
            weight = min(0.8 * (row["路線次數"] ** 0.5 / filtered["路線次數"].mean() ** 0.5), 2) ,
            opacity = get_op(row["路線次數"])
        ).add_to(mymap)

    for _, row in filtered[["借車站","lat_start","lng_start"]].drop_duplicates().iterrows():
        folium.CircleMarker(
            location=[row['lat_start'], row['lng_start']],
            radius=1,  
            tooltip=folium.Tooltip(f"<div style='font-size: 18px;'>站點: {row['借車站']}</div>"),
            popup=folium.Popup(f"<div style='font-size: 18px;'>站點: {row['借車站']}</div>", max_width=300),  
            color="red",  
            fill=True,
            fill_color="red", 
            fill_opacity=0.4  
        ).add_to(mymap)

    for _, row in filtered[["還車站","lat_end","lng_end"]].drop_duplicates().iterrows():
        folium.CircleMarker(
            location=[row['lat_end'], row['lng_end']],
            radius=1,  
            tooltip=folium.Tooltip(f"<div style='font-size: 18px;'>站點: {row['還車站']}</div>"),
            popup=folium.Popup(f"<div style='font-size: 18px;'>站點: {row['還車站']}</div>", max_width=300),
            color="red",  
            fill=True,
            fill_color="red", 
            fill_opacity=0.4  
        ).add_to(mymap)

    legend_html = """
        <div style="
        position: fixed;
        top: 20px; 
        left: 50%; 
        transform: translateX(-50%);
        width: auto; 
        height: auto;
        background-color: rgba(255, 255, 255, 0.8);
        border: 2px solid grey; 
        z-index: 9999; 
        font-size: 16px; 
        line-height: 1.6;
        border-radius: 15px; 
        padding: 10px;
        text-align: center;
        ">
        <strong style="font-size: 18px;">Legend</strong> <br>
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: flex-start; margin-top: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:gray; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                <span style="font-size: 14px; margin-left: 10px;"> "免費" 路線: 顏色越深、越粗代表越多人騎乘 </span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:orange; width: 20px; height: 20px; display:inline-block; border-radius: 50%;"></i>
                <span style="font-size: 14px; margin-left: 10px;"> "付費" 路線: 顏色越深、越粗代表此路線付費比率越高 </span>
            </div>
        </div>
    </div>
    """
    
    mymap.get_root().html.add_child(folium.Element(legend_html))
    mymap.save(dname+r"/project/map_application/static/bike_routes_map.html")
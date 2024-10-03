from function.log import Logger
import pandas as pd
import osmnx as ox
import geopandas as gpd
pd.set_option('display.max_columns', None)
# 將其保存為 GeoJSON 文件
GEO_LOC = r"D:\sandbox_git\project\map_application\static\geojson\COUNTY_MOI_1130718.json"
TAI_LOC = r"D:\sandbox_git\project\map_application\static\geojson\OSM_DATA.geojson"
TAI_LOC_weekend = r"D:\sandbox_git\project\map_application\static\geojson\OSM_DATA_weekend.geojson"

# 創建 Logger 物件
logger = Logger().get_logger()

# 讀取 SHP 文件
shp_file = gpd.read_file(r"C:\Users\tonyf\Downloads\直轄市、縣(市)界線檔(TWD97經緯度)1130719\COUNTY_MOI_1130718.shp", encoding="utf-8")


shp_file.to_file(GEO_LOC, driver="GeoJSON")

geojson = gpd.read_file(GEO_LOC)

# 使用 bounding box 查詢 admin_level=7 的資料
north, south, east, west = 26.0854, 24.9601, 120.6147, 122.4855  # 台北市大致經緯度範圍
gdf = ox.geometries_from_bbox(north, south, east, west, tags={'admin_level': '7'})

districts = ["北投區", "士林區", "大同區", "中山區", "松山區", "內湖區", "萬華區", "中正區", "大安區", "信義區", "南港區", "文山區"]
df = gdf[["name", "geometry"]].query(f"name.isin({districts})").sort_values(by = ["name","geometry"]).reset_index().drop_duplicates(subset="name")

gpd.GeoDataFrame(df, geometry='geometry')\
    .to_file(TAI_LOC_weekend, driver="GeoJSON")

df = gpd.read_file(TAI_LOC)
route_weekday = pd.read_csv(r"D:\sandbox_git\warehouse\insight\週末起訖站點統計_cleaned.csv")
route_sum = route_weekday.groupby("district_name",as_index=False).agg(paths = ("route","nunique"))
route_sum["paths_pct"] = route_sum["paths"] /  route_sum["paths"].sum()
df = df.merge(route_sum,left_on="name",right_on="district_name").drop(columns="district_name")
df
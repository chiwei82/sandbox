# dagster/my_dagster_job.py
from dagster import job, op
import sys
import os

# 讓 dagster 能夠找到 project/map_application 資料夾中的 bike_data.py
sys.path.append(os.path.join(os.path.dirname(__file__), '../project/map_application'))

from bike_data import main

@op
def run_bike_data_main():
    main()

@job
def bike_data_job():
    run_bike_data_main()
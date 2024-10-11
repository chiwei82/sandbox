from dagster import job, op
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../project/map_application'))
from bike_data import main

@op
def run_bike_data_main():
    main()

@job
def bike_data_job():
    run_bike_data_main()
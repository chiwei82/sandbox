# dagster/repository.py
from dagster import repository
from dagster_job import bike_data_job
from schedule import bike_data_schedule

@repository
def my_repository():
    return [bike_data_job, bike_data_schedule]

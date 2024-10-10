# dagster/schedule.py
from dagster import schedule
from dagster_job import bike_data_job

@schedule(cron_schedule="*/10 * * * *", job=bike_data_job)
def bike_data_schedule():
    return {}

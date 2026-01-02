from dagster import Definitions, load_assets_from_modules, define_asset_job, ScheduleDefinition
from . import assets
from .resources import APISourceResource, DBTargetResource
import os

all_assets = load_assets_from_modules([assets])

# Job definition
etl_job = define_asset_job(
    name="etl_job",
    selection=all_assets,
    description="Job to run the daily ETL assets"
)

# Schedule definition
daily_etl_schedule = ScheduleDefinition(
    job=etl_job,
    cron_schedule="0 0 * * *", # Runs at midnight daily
    execution_timezone="UTC",
)

# Resources
defs = Definitions(
    assets=all_assets,
    jobs=[etl_job],
    schedules=[daily_etl_schedule],
    resources={
        "api": APISourceResource(
            api_url=os.getenv("API_URL", "http://localhost:8000/data")
        ),
        "db": DBTargetResource(
            user=os.getenv("DB_TARGET_USER", "postgres"),
            password=os.getenv("DB_TARGET_PASSWORD", "postgres"),
            host="localhost", # Using localhost for external access from Dagster dev
            port=os.getenv("DB_TARGET_EXTERNAL_PORT", "5434"),
            db_name=os.getenv("DB_TARGET_NAME", "db_alvo"),
        ),
    },
)

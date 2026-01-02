from dagster import asset, Output, DailyPartitionsDefinition, MetadataValue
from datetime import datetime
import pandas as pd
from .resources import APISourceResource, DBTargetResource
from etl.main import ETLProcessor

daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01")

@asset(
    partitions_def=daily_partitions,
    group_name="etl",
    description="Daily ETL process to extract wind data and load into target DB"
)
def daily_wind_etl(context, api: APISourceResource, db: DBTargetResource):
    partition_date_str = context.partition_key
    context.log.info(f"Running ETL for partition: {partition_date_str}")
    
    partition_date = datetime.strptime(partition_date_str, "%Y-%m-%d").date()

    with db.get_session() as session:
        processor = ETLProcessor(api_url=api.api_url, db_session=session)
        
        df = processor.extract(partition_date)
        context.log.info(f"Extracted {len(df)} rows")
        
        transformed_df = processor.transform(df)
        context.log.info("Data transformed")
        
        processor.load(transformed_df)
        context.log.info("Data loaded")

    return Output(
        value=len(transformed_df), 
        metadata={
            "rows_processed": len(transformed_df),
            "preview": MetadataValue.md(transformed_df.head().to_markdown()),
            "columns": list(transformed_df.columns)
        }
    )

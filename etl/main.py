import argparse
import httpx
import pandas as pd
from datetime import datetime, time
from .database import engine, Base, SessionLocal
from .models import Signal, Data

# Ensure tables exist

class ETLProcessor:
    def __init__(self, api_url: str, db_session = None):
        self.api_url = api_url
        if db_session:
            self.db = db_session
            self.own_session = False
        else:
            self.db = SessionLocal()
            self.own_session = True
            
        # Ensure tables exist using the current database connection
        Base.metadata.create_all(bind=self.db.get_bind())

    def extract(self, date: datetime.date) -> pd.DataFrame:
        """
        Extract data from the API for a specific date.
        """
        start_date = datetime.combine(date, time.min)
        end_date = datetime.combine(date, time.max)
        
        print(f"Extracting data from {start_date} to {end_date}...")
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "columns": "timestamp,wind_speed,power"
        }
        
        try:
            with httpx.Client() as client:
                response = client.get(self.api_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
            if not data:
                print("No data found for this date.")
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
            
        except httpx.RequestError as e:
            print(f"API request failed: {e}")
            return pd.DataFrame()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample data to 10-minute intervals and calculate statistics.
        """
        if df.empty:
            return df
            
        print("Transforming data...")
        
        # Set timestamp as index for resampling
        df.set_index('timestamp', inplace=True)
        
        agg_funcs = ['mean', 'min', 'max', 'std']
        
        resampled = df.resample('10min').agg({
            'wind_speed': agg_funcs,
            'power': agg_funcs
        })
        
        transformed_data = []
        
        for index, row in resampled.iterrows():
            timestamp = index
            
            for col_level1 in ['wind_speed', 'power']:
                 for col_level2 in agg_funcs:
                     val = row[(col_level1, col_level2)]
                     if pd.isna(val):
                         continue
                         
                     signal_name = f"{col_level1}_{col_level2}"
                     transformed_data.append({
                         'timestamp': timestamp,
                         'signal_name': signal_name,
                         'value': val
                     })
                     
        return pd.DataFrame(transformed_data)

    def load(self, df: pd.DataFrame):
        """
        Load transformed data into db_alvo.
        """
        if df.empty:
            print("Nothing to load.")
            return

        print("Loading data into target database...")
        
        # Ensure Signals exist and get their IDs
        unique_signals = df['signal_name'].unique()
        signal_map = {}
        
        for name in unique_signals:
            signal = self.db.query(Signal).filter_by(name=name).first()
            if not signal:
                signal = Signal(name=name)
                self.db.add(signal)
                self.db.commit()
                self.db.refresh(signal)
            signal_map[name] = signal.id
            
        # Insert Data
        df['signal_id'] = df['signal_name'].map(signal_map)
        
        # Prepare objects for bulk insert
        data_objects = []
        for _, row in df.iterrows():
            data_objects.append(Data(
                timestamp=row['timestamp'],
                signal_id=row['signal_id'],
                value=row['value']
            ))
        
        try:
             for obj in data_objects:
                 self.db.merge(obj)
             
             self.db.commit()
             print(f"Successfully loaded {len(data_objects)} records.")
             
        except Exception as e:
            self.db.rollback()
            print(f"Error loading data: {e}")

    def run(self, date_str: str):
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            df = self.extract(date)
            transformed_df = self.transform(df)
            self.load(transformed_df)
        finally:
            if self.own_session:
                self.db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ETL for a specific date")
    parser.add_argument("--date", type=str, required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000/data", help="API Endpoint")
    
    args = parser.parse_args()
    
    etl = ETLProcessor(args.api_url)
    etl.run(args.date)

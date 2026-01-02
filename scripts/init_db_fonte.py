import os
import random
from datetime import datetime, timedelta
import dotenv
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
dotenv.load_dotenv()

DB_USER = os.getenv("DB_SOURCE_USER", "postgres")
DB_PASS = os.getenv("DB_SOURCE_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_SOURCE_NAME", "db_fonte")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost") 
DB_PORT = os.getenv("POSTGRES_PORT", "5433")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Connecting to: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")

Base = declarative_base()

class Data(Base):
    __tablename__ = 'data'
    
    timestamp = Column(DateTime, primary_key=True)
    wind_speed = Column(Float)
    power = Column(Float)
    ambient_temperature = Column(Float)

def generate_data():
    data_points = []
    start_date = datetime.now() - timedelta(days=10)
    
    # 10 days * 24 hours * 60 minutes = 14400 points
    total_minutes = 10 * 24 * 60
    
    print(f"Generating {total_minutes} data points...")
    
    for i in range(total_minutes):
        current_time = start_date + timedelta(minutes=i)
        
        # Wind speed 0-25 m/s
        wind = random.uniform(0, 25)
        
        # Power curve simulation (rough approximation)
        # Setup: P ~ v^3
        if wind < 3:
            power = 0
        elif wind > 25:
             power = 0
        else:
            power = min(2000, (wind ** 3) * 1.5) + random.uniform(-50, 50)
            power = max(0, power) # No negative power
            
        temp = 20 + random.uniform(-5, 5) # 15-25 degrees C
        
        data_points.append(Data(
            timestamp=current_time,
            wind_speed=round(wind, 2),
            power=round(power, 2),
            ambient_temperature=round(temp, 2)
        ))
        
    return data_points

def main():
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if data already exists to avoid duplication
        count = session.query(Data).count()
        if count > 0:
            print(f"Database already has {count} records. Skipping insertion.")
            session.close()
            return

        data = generate_data()
        
        # Bulk insert for performance
        print("Inserting data...")
        session.bulk_save_objects(data)
        session.commit()
        print("Data insertion complete!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

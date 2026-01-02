from sqlalchemy import Column, Integer, Float, DateTime
from .database import Base

class Data(Base):
    __tablename__ = 'data'
    
    timestamp = Column(DateTime, primary_key=True)
    wind_speed = Column(Float)
    power = Column(Float)
    ambient_temperature = Column(Float)

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Signal(Base):
    __tablename__ = 'signal'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationship
    data_points = relationship("Data", back_populates="signal")

class Data(Base):
    __tablename__ = 'data'
    
    timestamp = Column(DateTime, primary_key=True)
    signal_id = Column(Integer, ForeignKey('signal.id'), primary_key=True)
    value = Column(Float)
    
    # Relationship
    signal = relationship("Signal", back_populates="data_points")

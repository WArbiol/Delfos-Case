from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from .database import get_db
from .models import Data

app = FastAPI()

@app.get("/data")
def get_data(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    columns: Optional[str] = Query(None, description="Comma-separated list of columns to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve data with optional time range and dynamic column selection.
    """
    
    selectable_columns = ["timestamp", "wind_speed", "power", "ambient_temperature"]
    
    if columns:
        requested_columns = [col.strip() for col in columns.split(',')]
        for col in requested_columns:
            if col not in selectable_columns:
                raise HTTPException(status_code=400, detail=f"Invalid column: {col}")
        
        query_columns = [getattr(Data, col) for col in requested_columns]
        stmt = select(*query_columns)
    else:
        stmt = select(Data)

    # Apply filters
    if start_date:
        stmt = stmt.where(Data.timestamp >= start_date)
    if end_date:
        stmt = stmt.where(Data.timestamp <= end_date)

    result = db.execute(stmt).all()
    
    # Format response
    if columns:
        response_data = []
        for row in result:
             response_data.append(dict(zip(requested_columns, row)))
        return response_data
    else:        
        scalars = db.scalars(stmt).all()
        return scalars


import os
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

dotenv.load_dotenv()

DB_USER = os.getenv("DB_TARGET_USER", "postgres")
DB_PASS = os.getenv("DB_TARGET_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_TARGET_NAME", "db_alvo")
DB_HOST = os.getenv("DB_TARGET_HOST", "localhost") 
DB_PORT = os.getenv("DB_TARGET_EXTERNAL_PORT", "5434")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

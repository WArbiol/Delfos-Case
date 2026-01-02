from dagster import ConfigurableResource, resource
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager

class APISourceResource(ConfigurableResource):
    api_url: str = "http://localhost:8000/data"

class DBTargetResource(ConfigurableResource):
    user: str = "postgres"
    password: str = "postgres"
    host: str = "localhost"
    port: str = "5434"
    db_name: str = "db_alvo"

    @contextmanager
    def get_session(self):
        # Construct connection string
        # Note: In a real scenario, consider using secrets or EnvVar
        url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        engine = create_engine(url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
            engine.dispose()

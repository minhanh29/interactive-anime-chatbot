from typing import Any, Optional

# from app.schemas import DatabaseHelperReSchema
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

from sqlalchemy.orm import Session
from config import settings

# This call handle connect to database via connection string

'''
    Receive a connection like ["Server=123;port=3306;Database=consi_brand_BRANDCODE_attendancemanagement;user=dev;password=dev@123"]
    GET
        {
            Server,
            port,
            Database,
            user,
            password
        }
    Result Expect
        mysql_db = {'drivername': 'mysql+pymysql',
                'username': 'dev',
                'password': 'dev@123',
                'host': '123',
                'database': 'consi_tenant_management',
                'port': 3306}
'''

class DBRepository:

    SessionLocal: Any = None
    engine: Engine = None

    def __init__(self):
        host = settings.HOST
        port = settings.PORT
        root_user = settings.ROOT_USER
        root_password = settings.ROOT_PASSWORD
        current_tenant_db = settings.CURRENT_TENANT_DB

        # self._sqlalchemy = f"postgresql://{root_user}:{root_password}@{host}:{port}/{current_tenant_db}?sslmode=require"
        self._sqlalchemy = f"postgresql://{root_user}:{root_password}@{host}:{port}/{current_tenant_db}"
        self.connect(self._sqlalchemy)
        print("Connected to SQL")

    def connect(self, url: str):
        # => mysql+py://user:pass@host:port/databnase_table
        # url = URL.create(**sqlalchemy)

        self.engine = create_engine(url)

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

    # Dependency
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_engine(self) -> Engine:
        return self.engine


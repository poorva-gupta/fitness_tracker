from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from models import Base,Instructor
from fastapi import Request

class Config:
    def __init__(self,env):
        self.env=env
        self.db=create_engine(URL.create(
            "mysql+mysqlconnector",
            host=self.env.get("host"),
            username=self.env.get("username"),
            password=self.env.get("password"),
            database=self.env.get("database")
        ))
        self.SessionLocal=sessionmaker(bind=self.db)
    def set_up(self):
        Base.metadata.create_all(bind=self.db)
def get_db(request:Request):
    db=request.app.state.db_config.SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

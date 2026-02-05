import os
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/jobs_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    description = Column(Text)
    seniority = Column(String)
    employment_type = Column(String)
    link = Column(String, unique=True, index=True, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
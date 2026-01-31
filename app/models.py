from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from models_base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    filters = relationship("SearchFilter", back_populates="user")

class SearchFilter(Base):
    __tablename__ = 'search_filters'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    keyword = Column(String(100))
    location = Column(String(100))
    experience_level = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="filters")
    jobs = relationship("Job", back_populates="filter")

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    filter_id = Column(Integer, ForeignKey('search_filters.id'))
    title = Column(String(255))
    company = Column(String(255))
    description = Column(Text)
    link = Column(String(500), unique=True)
    found_at = Column(DateTime, default=datetime.utcnow)

    filter = relationship("SearchFilter", back_populates="jobs")
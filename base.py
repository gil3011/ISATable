from sqlalchemy import create_engine, Column, Integer, String, Boolean , ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    logo = Column(String)
    div = Column(String)

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))
    home_score = Column(Integer)
    away_score = Column(Integer)
    div = Column(String)
    location = Column(String)
    played = Column(Boolean, default=False)


engine = create_engine("sqlite:///isasoftball.db")
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
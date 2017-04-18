from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sport_db import \
    Base\
    ,User\
    ,Category\
    ,Sport

engine = create_engine('sqlite:///sports_db.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
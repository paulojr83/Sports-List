from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    sports = relationship("Sport", back_populates='category', cascade="all, delete, delete-orphan")

    @property
    def serialize(self):
        return {
            'sports': [sport.serialize for sport in self.sports],
            'id': self.id,
            'name': self.name,
        }

class Sport(Base):
    __tablename__ = 'item'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    history = Column(String(250))
    origin = Column(String(250))
    data_log = Column( DateTime, default=datetime.datetime.now)
    cat_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, back_populates='sports')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'origin': self.origin,
            'title': self.title,
            'history': self.history,
            'description': self.description,
        }

engine = create_engine('sqlite:///sports_db.db')
Base.metadata.create_all(engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table
)

Base = declarative_base()

# Промежуточная таблица, созданная для репрезентации отношения many-to-many между постами и тегами
tag_post = Table(
    'tag_post',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, unique=False, nullable=False)
    image = Column(String, unique=False, nullable=True)
    date = Column(String, unique=False)
    writer_id = Column(Integer, ForeignKey('writer.id'))
    # Виртуальное поле, соединяющее таблицы post и comments
    comments = relationship("Comment")
    writer = relationship("Writer", back_populates='posts')
    tags = relationship('Tag', secondary=tag_post, back_populates='posts')

class Writer(Base):
    __tablename__ = 'writer'
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, unique=False, nullable=False)
    posts = relationship("Post")

class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, unique=False, nullable=False)
    posts = relationship('Post', secondary=tag_post)

# Таблица для комментариев
class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    # Текст комментариев
    text = Column(String, unique=False, nullable=True)
    # Адрес родительской статьи
    url = Column(String, unique=True, nullable=False)
    post_id = Column(Integer, ForeignKey("post.id"))
    # Виртуальное поле, связывающее с таблицей post
    post = relationship("Post")

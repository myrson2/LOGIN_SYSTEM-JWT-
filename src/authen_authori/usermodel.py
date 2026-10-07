import os
import uuid

from sqlalchemy import Date, ForeignKey, String, Time, create_engine, Column, Integer
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, mapped_column, Mapped

engine = create_engine(
    str(os.getenv("DATABASE_KEY")),
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column( primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

def create_tables() -> None:
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()





"""Declarative base for all SQLAlchemy models.

Import and re-export model classes here so Alembic autogenerate can discover
every table in the canonical schema.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so they register with Base.metadata for Alembic autogenerate.
from app import models  # noqa: E402,F401

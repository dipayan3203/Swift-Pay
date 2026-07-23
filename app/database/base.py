from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Import models here so Alembic can discover them
from app.models.merchant import Merchant